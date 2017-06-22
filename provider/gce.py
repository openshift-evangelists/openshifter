import json
import logging

from libcloud.common.google import ResourceNotFoundError

from openshifter.cluster import Cluster
from provider.provisioner import Provisioner


class Gce(Provisioner):
    def __init__(self, deployment):
        Provisioner.__init__(self, deployment, "gce")

        self.name = self.deployment.name

        self.gce = self.deployment['gce']
        self.credentials = json.load(open(self.gce['account'], 'r'))
        self.compute = self._get_compute_driver()(self.credentials['client_email'], self.credentials['private_key'],
                                                  project=self.gce['project'], datacenter=self.gce['zone'])
        self.disk_image = self.compute.ex_get_image("centos-7")
        if self.deployment['type'] == 'ocp':
            self.disk_image = self.compute.ex_get_image("rhel-7")

    def validate(self):
        logging.info("Validating cluster")
        cluster = Cluster()
        try:
            master = self.compute.ex_get_node(self.name + '-master', zone=self.gce['zone'])
        except ResourceNotFoundError:
            logging.info("Master node does not exist")
            cluster.master = None
            cluster.valid = False
            return cluster
        else:
            cluster.master = master.public_ips[0]
            logging.info("Master node exists")

        if self.has_infra():
            try:
                infra = self.compute.ex_get_node(self.name + '-infra', zone=self.gce['zone'])
            except ResourceNotFoundError:
                logging.info("Infra node does not exist")
                cluster.infra = None
                cluster.valid = False
                return cluster
            else:
                cluster.infra = infra.public_ips[0]
                logging.info("Infra node exists")
        else:
            logging.info("There is no infra node in the cluster")
            cluster.infra = cluster.master

        if self.has_nodes():
            for x in range(0, self.deployment['nodes']['count']):
                name = self.name + "-node-" + str(x)
                try:
                    node = self.compute.ex_get_node(name, zone=self.gce['zone'])
                except ResourceNotFoundError:
                    logging.info("Node %s does not exist" % name)
                    cluster.valid = False
                    return cluster
                else:
                    logging.info("Node %s exists" % name)
                    cluster.nodes.append(node.public_ips[0])
        else:
            logging.info("There are no nodes in the cluster")
            cluster.nodes.append(cluster.master)

        cluster.valid = True
        return cluster


    def create(self):
        # Networking
        try:
            network = self.compute.ex_get_network(self.name)
        except ResourceNotFoundError:
            logging.info("Creating network")
            network = self.compute.ex_create_network(self.name, None, mode='auto')
        else:
            logging.info("Network already exists")

        try:
            self.compute.ex_get_firewall(self.name + "-all")
            logging.info("Firewall rule exists")
        except ResourceNotFoundError:
            logging.info("Creating firewall rule")
            self.compute.ex_create_firewall(self.name + "-all", [
                {'IPProtocol': 'tcp', 'ports': ['22']}
            ], network=network.name)

        try:
            self.compute.ex_get_firewall(self.name + "-internal")
            logging.info("Firewall rule exists")
        except ResourceNotFoundError:
            logging.info("Creating firewall rule")
            self.compute.ex_create_firewall(self.name + "-internal", [
                {'IPProtocol': 'icmp'},
                {'IPProtocol': 'tcp', 'ports': ['0-65535']},
                {'IPProtocol': 'udp', 'ports': ['0-65535']}
            ], network=network.name, source_ranges=["10.128.0.0/9"])

        try:
            self.compute.ex_get_firewall(self.name + "-master")
            logging.info("Firewall rule exists")
        except ResourceNotFoundError:
            logging.info("Creating firewall rule")
            self.compute.ex_create_firewall(self.name + "-master", [
                {'IPProtocol': 'tcp', 'ports': ['8443']}
            ], network=network.name, target_tags=['master'])

        try:
            self.compute.ex_get_firewall(self.name + "-infra")
            logging.info("Firewall rule exists")
        except ResourceNotFoundError:
            logging.info("Creating firewall rule")
            self.compute.ex_create_firewall(self.name + "-infra", [
                {'IPProtocol': 'tcp', 'ports': ["80", "443", "30000-32767"]}
            ], network=network.name, target_tags=['infra'])

        # IP addresses
        self._create_address("master")

        if self.has_infra():
            self._create_address("infra")

        if self.has_nodes():
            for x in range(0, self.deployment['nodes']['count']):
                self._create_address("node-" + str(x))

        # Storage
        self._create_disk("master-root")
        self._create_disk("master-docker", 100)

        if self.has_infra():
            self._create_disk("infra-root")
            self._create_disk("infra-docker", 100)

        if self.has_nodes():
            for x in range(0, self.deployment['nodes']['count']):
                name = "node-" + str(x)
                self._create_disk(name + "-root")
                self._create_disk(name + "-docker", 100)

        cluster = Cluster()
        master = self._create_node("master", network, ['master'])
        cluster.master = master.public_ips[0]

        if self.has_infra():
            infra = self._create_node("infra", network, ['infra'])
            cluster.infra = infra.public_ips[0]
        else:
            cluster.infra = master.public_ips[0]

        if self.has_nodes():
            for x in range(0, self.deployment['nodes']['count']):
                name = "node-" + str(x)
                node = self._create_node(name, network, ['node'])
                cluster.nodes.append(node.public_ips[0])
        else:
            cluster.nodes.append(master.public_ips[0])

        return cluster

    def has_infra(self):
        return self.deployment['nodes']['infra']

    def has_nodes(self):
        return self.deployment['nodes']['count'] > 0

    def _create_address(self, name):
        name = self.name + "-" + name
        try:
            self.compute.ex_get_address(name)
            logging.info("Address " + name + " exists")
        except ResourceNotFoundError:
            logging.info("Creating address " + name)
            self.compute.ex_create_address(name, region=self.gce['region'])

    def _create_disk(self, name, size=None):
        name = self.name + "-" + name
        try:
            self.compute.ex_get_volume(name, zone=self.gce['zone'])
            logging.info("Disk " + name + " exists")
        except ResourceNotFoundError:
            logging.info("Creating disk " + name)
            args = {
                'location': self.gce['zone'],
                'ex_disk_type': 'pd-ssd'
            }
            if size is None:
                args['image'] = self.disk_image
            self.compute.create_volume(size, name, **args)

    def _create_node(self, name, network, tags):
        name = self.name + "-" + name
        file = open(self.deployment['ssh']['key'] + ".pub", "r")
        ssh_key = file.read()
        file.close()

        try:
            node = self.compute.ex_get_node(name, self.gce['zone'])
            logging.info("Node " + name + " exists")
        except ResourceNotFoundError:
            logging.info("Creating node " + name)
            node = self.compute.create_node(name,
                                            self.deployment['nodes']['type'],
                                            None,
                                            self.gce['zone'],
                                            ex_metadata= {
                                                'items': [
                                                    {'key': 'sshKeys', 'value':'openshift:' + ssh_key}
                                                ]
                                            },
                                            ex_network=network,
                                            ex_tags=tags,
                                            ex_boot_disk=self.compute.ex_get_volume(name + "-root",
                                                                                    zone=self.gce['zone']),
                                            use_existing_disk=True,
                                            external_ip=self.compute.ex_get_address(name),
                                            ex_service_accounts=[]
                                            )
            self.compute.attach_volume(node, self.compute.ex_get_volume(name + "-docker", zone=self.gce['zone']),
                                       ex_auto_delete=True)

        return node

    def destroy(self):
        logging.info("Destroying master instance")
        name = self.name + '-master'
        self.compute.destroy_node(self.compute.ex_get_node(name, zone=self.gce['zone']))
        self.compute.ex_destroy_address(self.compute.ex_get_address(name))
        if self.has_infra():
            logging.info("Destroying infra instance")
            name = self.name + '-infra'
            self.compute.destroy_node(self.compute.ex_get_node(name, zone=self.gce['zone']))
            self.compute.ex_destroy_address(self.compute.ex_get_address(name))
        if self.has_nodes():
            for x in range(0, self.deployment['nodes']['count']):
                name = self.name + "-node-" + str(x)
                logging.info("Destroying node instance %s" % name)
                self.compute.destroy_node(self.compute.ex_get_node(name, zone=self.gce['zone']))
                self.compute.ex_destroy_address(self.compute.ex_get_address(name))
        logging.info("Destroying firewall rules")
        self.compute.ex_destroy_firewall(self.compute.ex_get_firewall(self.name + "-all"))
        self.compute.ex_destroy_firewall(self.compute.ex_get_firewall(self.name + "-internal"))
        self.compute.ex_destroy_firewall(self.compute.ex_get_firewall(self.name + "-master"))
        self.compute.ex_destroy_firewall(self.compute.ex_get_firewall(self.name + "-infra"))

        logging.info("Destroying network")
        self.compute.ex_destroy_network(self.compute.ex_get_network(self.name))
