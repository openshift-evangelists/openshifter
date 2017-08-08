import yaml

from features import Base


class PVs(Base):
    def check(self):
        return self.check_component('pvs')

    def applicable(self):
        return ["master"]

    def call(self, connection):
        self.logger.info("Setting up PVs")
        for i in range(0, self.deployment['pvs']['count']):
            name = 'pv-' + str(i)
            pv = {
                'apiVersion': 'v1',
                'kind': 'PersistentVolume',
                'metadata': {
                    'name': name
                },
                'spec': {
                    'capacity': {
                        'storage': str(self.deployment['pvs']['size']) + 'Gi'
                    },
                    'accessModes': [
                        'ReadWriteMany',
                        'ReadWriteOnce',
                        'ReadOnlyMany'
                    ],
                    'hostPath': {
                        'path': '/pvs/' + name
                    },
                    'persistentVolumeReclaimPolicy': 'Recycle'
                }
            }
            self.logger.info("Creating directory structure")
            connection.execute("mkdir -p /pvs/" + name, True)
            connection.execute("chmod 777 /pvs/" + name, True)
            connection.execute("restorecon /pvs/" + name, True)

            self.logger.info("Creating PV")
            connection.upload("pv.yml", yaml.dump(pv))
            result = connection.execute("oc create -f pv.yml")
            if result.code > 0:
                self.logger.info("PV creating failed")