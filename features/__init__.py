import importlib
import inspect
import logging

from openshifter.ssh import Ssh

FEATURES = {
    "pre_install": [
        "features.basic",
        "features.docker",
        "features.host_path",
        "features.gluster_server",
        "features.gluster_client",
    ],
    "install": [
        "features.ansible",
    ],
    "post_install": [],
    "pre_setup": [],
    "setup": [
        "features.logging_fix",
        "features.runasroot",
        "features.pvs",
        "features.sa",
        "features.users",
    ],
    "post_setup": []
}


def execute(type, deployment, cluster):
    if type not in FEATURES:
        return

    ssh_client = Ssh(deployment, cluster)

    for feature in FEATURES[type]:
        mod = importlib.import_module(feature)
        for name in dir(mod):
            if name == 'Base' or name.startswith("__"):
                continue
            item = getattr(mod, name)
            if inspect.isclass(item) and issubclass(item, Base):
                ft = item(deployment, cluster, ssh_client)
                if hasattr(ft, 'check'):
                    if ft.check():
                        ft.setup()


class Base:
    def __init__(self, deployment, cluster, ssh):
        self.deployment = deployment
        self.cluster = cluster
        self.ssh_client = ssh
        self.logger = logging.getLogger("Feature(%s)" % self.__class__.__name__)

    def applicable(self):
        return []

    def check(self):
        return False

    def setup(self):
        for client in self.ssh().for_tags(self.applicable()):
            self.logger.info("Starting feature for %s (%s)" % (client.address, ",".join(client.tags)))
            self.call(client)
            self.logger.info("Feature completed for %s (%s)" % (client.address, ",".join(client.tags)))

    def call(self, connection):
        pass

    def ssh(self):
        return self.ssh_client

    def execute(self, tag, cmd, sudo=False):
        return self.ssh().execute(tag, cmd, sudo)

    def upload(self, tag, target, content):
        return self.ssh().write(tag, target, content)

    def download(self, tag, target):
        return self.ssh().read(tag, target)

    def check_component(self, name):
        return name in self.deployment['components'] and self.deployment['components'][name]