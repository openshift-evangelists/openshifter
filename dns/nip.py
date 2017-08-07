class Nip:
    def __init__(self, deployment):
        self.deployment = deployment

    def create(self, cluster):
        self.deployment['dns']['suffix'] = cluster.infra.public_address + ".nip.io"

    def destroy(self, cluster):
        pass