from provider.provisioner import Provisioner, Cluster, Node


class Byo(Provisioner):
    def __init__(self, deployment, logger=None):
        Provisioner.__init__(self, deployment, logger)

    def get_node(self, name):
        node = Node(name)
        node.exists = True
        node.public_address = self.deployment['byo'][name]
        return node
