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

        self.dir = os.path.abspath("openshifter/" + self.name)
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def __getitem__(self, key):
        return self.data[key]