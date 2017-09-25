import yaml
import os


class Deployment:
    def __init__(self, name):
        self.name = name
        self.stream = open(name + ".yml", "r")
        self.data = yaml.load(self.stream)

        if 'name' not in self.data:
            self.data['name'] = name

        self.name = self.data['name']
        self.version = Version(self.data['release'])

        if 'installer' not in self.data:
            self.data['installer'] = 'ansible'

        if 'users' not in self.data:
            self.data['users'] = []

        if 'components' not in self.data:
            self.data['components'] = {}

        if 'cockpit' not in self.data['components']:
            self.data['components']['cockpit'] = True

        if 'dns' not in self.data:
            self.data['dns'] = {}

        if 'provider' not in self.data['dns']:
            self.data['dns']['provider'] = self.data['provider']

        if 'nodes' not in self.data:
            self.data['nodes'] = {}

        if 'podsPerCore' not in self.data['nodes']:
            self.data['nodes']['podsPerCore'] = 10

        if 'count' not in self.data['nodes']:
            self.data['nodes']['count'] = 0

        if 'infra' not in self.data['nodes']:
            self.data['nodes']['infra'] = False

        if 'type' not in self.data['nodes']:
            self.data['nodes']['type'] = 'n1-standard-1'

        if 'disk' not in self.data['nodes']:
            self.data['nodes']['disk'] = {}

        if 'boot' not in self.data['nodes']['disk']:
            self.data['nodes']['disk']['boot'] = 100

        if 'docker' not in self.data['nodes']['disk']:
            self.data['nodes']['disk']['docker'] = 100

        self.dir = os.path.abspath("openshifter/" + self.name)
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def __getitem__(self, key):
        return self.data[key]


class Version:
    def __init__(self, version):
        self.openshift = None
        self.major = None
        self.minor = None

        version = str(version)

        if version.startswith("v"):
            version = version[1:]

        vs = version.split(".")
        if len(vs) == 3:
            self.openshift, self.major, self.minor = vs
        else:
            self.openshift, self.major = vs

        self.openshift = int(self.openshift)
        self.major = int(self.major)

        if self.minor is not None:
            self.minor = int(self.minor)

    def __str__(self):
        if self.minor is not None:
            return "v%s.%s.%s" % (self.openshift, self.major, self.minor)
        else:
            return "v%s.%s" % (self.openshift, self.major)

    def git(self):
        if self.major < 6:
            base = 1
        else:
            base = 3
        return "release-%s.%s" % (base, self.major)
