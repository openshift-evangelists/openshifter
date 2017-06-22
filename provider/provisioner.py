import libcloud

class Provisioner:
    def __init__(self, deployment, provider):
        self.deployment = deployment
        self.provider = provider

    def _get_compute_driver(self):
        return libcloud.get_driver(libcloud.DriverType.COMPUTE,
                            libcloud.DriverType.COMPUTE.fromstring(self.deployment['provider']))

    def _get_dns_driver(self):
        return libcloud.get_driver(libcloud.DriverType.DNS,
                            libcloud.DriverType.COMPUTE.fromstring(self.deployment['provider']))

    def validate(self):
        pass

    def create(self):
        pass

    def destroy(self):
        pass
