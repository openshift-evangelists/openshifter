from features import Base


class HostPath(Base):
    def check(self):
        return self.check_component('pvs') and self.deployment['pvs']['type'] == 'hostPath'

    def applicable(self):
        return ['master']

    def call(self, connection):
        if connection.execute("mount").stdout.find(b'/dev/mapper/DOCKER-PVS') == -1:
            connection.execute("lvcreate -l 100%FREE -n PVS DOCKER", True)
            connection.execute("mkfs.xfs /dev/mapper/DOCKER-PVS", True)
            connection.execute("mkdir -p /var/lib/origin/openshift.local.volumes", True)
            connection.execute("mount /dev/mapper/DOCKER-PVS /var/lib/origin/openshift.local.volumes", True)
            connection.execute("echo \"/dev/mapper/DOCKER-PVS /var/lib/origin/openshift.local.volumes xfs defaults 0 1\" >> /etc/fstab", True)
            connection.execute("ln -s /var/lib/origin/openshift.local.volumes /pvs", True)
        else:
            self.logger.info("Persistent volumes are already setup")