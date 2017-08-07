import importlib
import inspect
import logging

from openshifter.ssh import Ssh

FEATURES = {
    "pre_install": ["features.docker", "features.pvs_storage"],
    "setup": ["features.logging_fix", "features.runasroot", "features.pvs", "features.sa", "features.users"]
}


def execute(type, deployment, cluster):
    for feature in FEATURES[type]:
        mod = importlib.import_module(feature)
        for name in dir(mod):
            if name == 'Base' or name.startswith("__"):
                continue
            item = getattr(mod, name)
            if inspect.isclass(item) and issubclass(item, Base):
                ft = item(deployment, cluster)
                if hasattr(ft, 'check'):
                    if ft.check():
                        ft.setup()


class Base:
    def __init__(self, deployment, cluster):
        self.deployment = deployment
        self.cluster = cluster
        self.ssh_client = Ssh(deployment, cluster)
        self.logger = logging.getLogger("Feature(%s)" % self.__class__.__name__)

    def check(self):
        return False

    def setup(self):
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