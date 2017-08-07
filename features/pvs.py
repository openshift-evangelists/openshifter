import yaml

from features import Base


class PVsStorage(Base):
    def check(self):
        return self.check_component('pvs')

    def setup(self):
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
            self.execute("master", "mkdir -p /pvs/" + name, True)
            self.execute("master", "chmod 777 /pvs/" + name, True)
            self.execute("master", "restorecon /pvs/" + name, True)

            self.upload("master", "pv.yml", yaml.dump(pv))
            self.execute("master", "oc create -f pv.yml")