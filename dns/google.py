from libcloud.common.google import ResourceExistsError, ResourceNotFoundError
from libcloud.dns.providers import get_driver
from libcloud.dns.types import RecordType
from libcloud.dns.base import Record

import json
import logging

class Google:
    def __init__(self, deployment):
        self.deployment = deployment
        self.gce = self.deployment['gce']
        self.credentials = json.load(open(self.gce['account'], 'r'))

        self.driver = get_driver('google')
        self.dns = self.driver(self.credentials['client_email'], self.credentials['private_key'], project=self.gce['project'])

    def create(self, cluster):
        logging.info("Looking up zone")
        zone = self.dns.get_zone(self.deployment['dns']['zone'])

        for name in ['console', '*.apps']:
            name = name + '.' + self.deployment.name + '.' + self.deployment['dns']['suffix'] + '.'
            try:
                logging.info("Creating DNS record %s" % name)
                data = {'ttl': 60, 'rrdatas': [cluster.infra]}
                self.dns.create_record(name, zone, RecordType.A, data)
            except ResourceExistsError:
                logging.info("Record already exists")

    def destroy(self, cluster):
        logging.info("Looking up zone")
        zone = self.dns.get_zone(self.deployment['dns']['zone'])

        for name in ['console', '*.apps']:
            try:
                name = name + '.' + self.deployment.name + '.' + self.deployment['dns']['suffix'] + '.'
                logging.info("Destroying DNS record %s" % name)
                data = {'ttl': 60, 'rrdatas': [cluster.infra]}
                record = Record('', name=name, type=RecordType.A, zone=zone, driver=self.dns, data=data)
                self.dns.delete_record(record)
            except ResourceNotFoundError:
                logging.error("DNS record does not exist")