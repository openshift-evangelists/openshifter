from libcloud.common.google import ResourceExistsError, ResourceNotFoundError
from libcloud.dns.providers import get_driver
from libcloud.dns.types import RecordType

import json
import logging
import os.path


class Google:
    def __init__(self, deployment):
        self.deployment = deployment
        self.gce = self.deployment['gce']
        self.credentials = json.load(open(self.gce['account'], 'r'))

        self.driver = get_driver('google')
        self.dns = self.driver(self.credentials['client_email'], self.credentials['private_key'],
                               project=self.gce['project'],
                               credential_file=os.path.join(os.path.curdir, 'openshifter', deployment.name, 'credentials.cache'))

    def create(self, cluster):
        logging.info("Looking up zone")
        zone = self.dns.get_zone(self.deployment['dns']['zone'])

        for name in ['console', '*.apps']:
            name = name + '.' + self.deployment.name + '.' + self.deployment['dns']['suffix'] + '.'
            try:
                logging.info("Creating DNS record %s" % name)
                data = {'ttl': 60, 'rrdatas': [cluster.infra.public_address]}
                self.dns.create_record(name, zone, RecordType.A, data)
            except ResourceExistsError:
                logging.info("Record already exists")

    def destroy(self, cluster):
        for name in ['console', '*.apps']:
            try:
                name = name + '.' + self.deployment.name + '.' + self.deployment['dns']['suffix'] + '.'
                record = self.get_record("A", name)
                logging.info("Destroying DNS record %s" % name)
                self.dns.delete_record(record)
            except ResourceNotFoundError:
                logging.error("DNS record does not exist")

    def get_record(self, type, name):
        logging.info("Looking up zone")
        zone = self.dns.get_zone(self.deployment['dns']['zone'])
        logging.info("Looking up DNS record %s" % name)
        return self.dns.get_record(zone.id, "%s:%s" % (type, name))