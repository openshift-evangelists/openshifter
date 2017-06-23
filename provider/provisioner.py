import logging

class Provisioner:
    def __init__(self, deployment, logger=None):
        self.deployment = deployment
        if logger is None:
            self.logger = logging.getLogger('Provisioner (%s)' % deployment['provider'])
        else:
            self.logger = logger

    def validate(self):
        self.logger.info("Validating cluster state")
        cluster = Cluster()
        cluster.valid = True

        self.logger.info("Validating master existence")
        cluster.master = self.get_node("master")
        cluster.master.labels.append("master")
        cluster.valid = cluster.valid and cluster.master.exists
        if cluster.master.exists:
            self.logger.info("Master exists")
        else:
            self.logger.info("Master does not exist")

        if self.has_infra():
            self.logger.info("Validating infra existence")
            cluster.infra = self.get_node("infra")
            cluster.infra.labels.append("infra")
            cluster.valid = cluster.valid and cluster.infra.exists
            if cluster.master.exists:
                self.logger.info("Infra exists")
            else:
                self.logger.info("Infra does not exist")
        else:
            cluster.infra = cluster.master

        if self.has_nodes():
            for x in range(0, self.deployment['nodes']['count']):
                name = "node-" + str(x)
                self.logger.info("Validating node %s existence", name)
                node = self.get_node(name)
                node.labels.append("node")
                cluster.nodes.append(node)
                cluster.valid = cluster.valid and node.exists
                if cluster.master.exists:
                    self.logger.info("Node %s exists", name)
                else:
                    self.logger.info("Node %s does not exist", name)
        else:
            cluster.nodes.append(cluster.master)

        return cluster

    def create(self):
        self.pre_create()

        self.create_node("master", ['master'])
        if self.has_infra():
            self.create_node("infra", ['infra'])
        if self.has_nodes():
            for x in range(0, self.deployment['nodes']['count']):
                name = "node-" + str(x)
                self.create_node(name, ['node'])

        self.post_create()
        return self.validate()

    def destroy(self):
        self.pre_destroy()

        self.destroy_node("master")
        if self.has_infra():
            self.destroy_node("infra")
        if self.has_nodes():
            for x in range(0, self.deployment['nodes']['count']):
                name = "node-" + str(x)
                self.destroy_node(name)

        self.post_destroy()

    def get_public_key(self):
        with open(self.deployment['ssh']['key'] + ".pub", "r") as file:
            return file.read()

    def has_infra(self):
        return self.deployment['nodes']['infra']

    def has_nodes(self):
        return self.deployment['nodes']['count'] > 0

    def create_node(self, name, labels):
        pass

    def get_node(self, name):
        pass

    def destroy_node(self, name):
        pass

    def pre_create(self):
        pass

    def post_create(self):
        pass

    def pre_destroy(self):
        pass

    def post_destroy(self):
        pass


class Cluster:
    def __init__(self):
        self.valid = False
        self.master = None
        self.infra = None
        self.nodes = []


class Node:
    def __init__(self, name):
        self.name = name
        self.labels = []
        self.exists = False
        self.public_address = None
        self.private_address = None
