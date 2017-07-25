import json
import os.path
import sys

import libcloud
from libcloud.common.google import ResourceNotFoundError, ResourceExistsError

from provider.provisioner import Provisioner, Node


class Gce(Provisioner):
    def __init__(self, deployment, logger=None):
        Provisioner.__init__(self, deployment, logger)

        self.logger.info("Configuring")
        self.name = self.deployment.name
        self.gce = self.deployment['gce']
        self.credentials = json.load(open(self.gce['account'], 'r'))

        args = [
            self.credentials['client_email'],
            self.credentials['private_key']
        ]
        kwargs = {
            'project': self.gce['project'],
            'datacenter': self.gce['zone'],
            'credential_file': os.path.join(os.path.curdir, 'openshifter', self.name, 'credentials.cache')
        }

        self.logger.info("Setting up")
        driver = libcloud.get_driver(libcloud.DriverType.COMPUTE, libcloud.DriverType.COMPUTE.GCE)
        self.compute = driver(*args, **kwargs)

        self.logger.info("Getting disk image")
        if self.deployment['type'] == 'ocp':
            self.disk_image = self.compute.ex_get_image('rhel-7')
        else:
            self.disk_image = self.compute.ex_get_image('centos-7')

        self.logger.info("Validating Zone and Region")
        try:
            self.zone = self.compute.ex_get_zone(self.gce['zone'])
        except ResourceNotFoundError:
            self.zone = None

        try:
            self.region = self.compute.ex_get_region(self.gce['region'])
        except ResourceNotFoundError:
            self.region = None

        if self.zone is None:
            self.logger.error("Zone is invalid")
            sys.exit(1)

        if self.region is None:
            self.logger.error("Region is invalid")
            sys.exit(1)

    def get_node(self, name):
        try:
            self.logger.info("Getting node")
            node = self.compute.ex_get_node(self.name + "-" + name, zone=self.gce['zone'])
        except ResourceNotFoundError:
            return Node(name)
        else:
            wrapper = Node(name)
            wrapper.exists = True
            wrapper.public_address = node.public_ips[0]
            return wrapper

    def create_node(self, name, labels):
        boot = self.create_disk(name + "-root")
        docker = self.create_disk(name + "-docker", 100)
        address = self.create_address(name)

        try:
            self.logger.info("Creating node")
            node = self.compute.create_node(self.name + "-" + name,
                                            self.deployment['nodes']['type'],
                                            None,
                                            self.gce['zone'],
                                            ex_metadata={
                                                'items': [
                                                    {'key': 'sshKeys', 'value': 'openshift:' + self.get_public_key()}
                                                ]
                                            },
                                            ex_network=self.get_network(),
                                            ex_tags=labels,
                                            ex_boot_disk=boot,
                                            use_existing_disk=True,
                                            external_ip=address,
                                            ex_service_accounts=[{
                                                'email': self.credentials['client_email'],
                                                'scopes': ['compute']
                                            }]
                                            )
            self.logger.info("Attaching Docker volume")
            self.compute.attach_volume(node, docker, ex_auto_delete=True)
        except ResourceExistsError:
            self.logger.info('Node already exists')
            node = self.get_node(self.name + "-" + name)

        return node

    def destroy_node(self, name):
        name = self.name + '-' + name
        try:
            self.logger.info("Destroying node")
            self.compute.destroy_node(self.compute.ex_get_node(name, zone=self.gce['zone']))
        except ResourceNotFoundError:
            pass
        try:
            self.logger.info("Destroying IP adress")
            self.compute.ex_destroy_address(self.compute.ex_get_address(name))
        except ResourceNotFoundError:
            pass

    def create_disk(self, name, size=None):
        args = {
            'location': self.gce['zone'],
            'ex_disk_type': 'pd-ssd'
        }
        if size is None:
            args['image'] = self.disk_image

        self.logger.info("Creating disk %s" % name)
        return self.compute.create_volume(size, self.name + "-" + name, **args)

    def create_address(self, name):
        try:
            self.logger.info("Creating IP address")
            return self.compute.ex_create_address(self.name + "-" + name, region=self.gce['region'])
        except ResourceExistsError:
            self.logger.info('Address already exists')
            return self.compute.ex_get_address(self.name + "-" + name, region=self.gce['region'])

    def get_network(self):
        self.logger.info("Getting network")
        return self.compute.ex_get_network(self.name)

    def pre_create(self):
        try:
            self.logger.info("Creating network")
            network = self.compute.ex_create_network(self.name, None, mode='auto')
        except ResourceExistsError:
            self.logger.info('Network already exists')
            network = self.compute.ex_get_network(self.name)

        try:
            self.logger.info("Creating firewall rule")
            self.compute.ex_create_firewall(self.name + "-all", [
                {'IPProtocol': 'tcp', 'ports': ['22']}
            ], network=network.name)
        except ResourceExistsError:
            self.logger.info('Firewall rule already exists')

        try:
            self.logger.info("Creating firewall rule")
            self.compute.ex_create_firewall(self.name + "-internal", [
                {'IPProtocol': 'icmp'},
                {'IPProtocol': 'tcp', 'ports': ['0-65535']},
                {'IPProtocol': 'udp', 'ports': ['0-65535']}
            ], network=network.name, source_ranges=["10.128.0.0/9"])
        except ResourceExistsError:
            self.logger.info('Firewall rule already exists')

        try:
            self.logger.info("Creating firewall rule")
            self.compute.ex_create_firewall(self.name + "-master", [
                {'IPProtocol': 'tcp', 'ports': ['8443']}
            ], network=network.name, target_tags=['master'])
        except ResourceExistsError:
            self.logger.info('Firewall rule already exists')

        try:
            self.logger.info("Creating firewall rule")
            self.compute.ex_create_firewall(self.name + "-infra", [
                {'IPProtocol': 'tcp', 'ports': ["80", "443", "30000-32767"]}
            ], network=network.name, target_tags=['infra'])
        except ResourceExistsError:
            self.logger.info('Firewall rule already exists')

    def post_destroy(self):
        try:
            self.logger.info("Destroying firewall rule")
            self.compute.ex_destroy_firewall(self.compute.ex_get_firewall(self.name + "-all"))
        except ResourceNotFoundError:
            pass
        try:
            self.logger.info("Destroying firewall rule")
            self.compute.ex_destroy_firewall(self.compute.ex_get_firewall(self.name + "-internal"))
        except ResourceNotFoundError:
            pass

        try:
            self.logger.info("Destroying firewall rule")
            self.compute.ex_destroy_firewall(self.compute.ex_get_firewall(self.name + "-master"))
        except ResourceNotFoundError:
            pass

        try:
            self.logger.info("Destroying firewall rule")
            self.compute.ex_destroy_firewall(self.compute.ex_get_firewall(self.name + "-infra"))
        except ResourceNotFoundError:
            pass

        try:
            self.logger.info("Destroying network")
            self.compute.ex_destroy_network(self.compute.ex_get_network(self.name))
        except ResourceNotFoundError:
            pass
