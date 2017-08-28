from features import Base


class PvsEmptyDir(Base):
    def check(self):
        return True

    def applicable(self):
        return ['*', '-pvs']

    def call(self, connection):
        if connection.execute("mount").stdout.find('/dev/mapper/DOCKER-PVS') == -1:
            connection.execute("lvcreate -l 100%FREE -n PVS DOCKER", True)
            connection.execute("mkfs.xfs /dev/mapper/DOCKER-PVS", True)
            connection.execute("mkdir -p /var/lib/origin/openshift.local.volumes", True)
            connection.execute("mount /dev/mapper/DOCKER-PVS /var/lib/origin/openshift.local.volumes", True)
            connection.execute("echo \"/dev/mapper/DOCKER-PVS /var/lib/origin/openshift.local.volumes xfs defaults 0 1\" >> /etc/fstab", True)
            connection.execute("ln -s /var/lib/origin/openshift.local.volumes /pvs", True)
        else:
            self.logger.info("Persistent volumes are already setup")