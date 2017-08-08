import logging

import features
from openshifter.deployment import Deployment

import provider
import dns
from openshifter.ssh import Ssh


class OpenShifter:

    def __init__(self):
        self.loaded = False
        self.deployment = None
        self.infrastructure = None
        self.cluster = None

    def load(self, name):
        if not self.loaded:
            self.deployment = Deployment(name)
            self.infrastructure = provider.find(self.deployment)
            self.cluster = self.infrastructure.validate()
            self.loaded = True

    def provision(self):
        cluster = self.infrastructure.create()
        driver = dns.find(self.deployment)
        driver.create(cluster)
        self.cluster = self.infrastructure.validate()

    def install(self):
        if self.cluster.valid:
            features.execute("pre_install", self.deployment, self.cluster)
            features.execute("install", self.deployment, self.cluster)
            features.execute("post_install", self.deployment, self.cluster)
        else:
            logging.error("Cluster is not valid. Did you provision it?")

    def setup(self):
        if self.cluster.valid:
            features.execute("pre_setup", self.deployment, self.cluster)
            features.execute("setup", self.deployment, self.cluster)
            features.execute("post_setup", self.deployment, self.cluster)
        else:
            logging.error("Cluster is not valid. Did you provision it?")

    def create(self):
        self.provision()
        self.install()
        self.setup()

    def destroy(self):
        self.infrastructure.destroy()
        driver = dns.find(self.deployment)
        driver.destroy(self.cluster)
