from features import Base


class Docker(Base):
    def check(self):
        return True

    def setup(self):
        for result in self.execute("*", "yum list installed", True):
            if result.stdout.find(b'docker') == -1:
                self.logger.info("Installing Docker")
                result.connection.execute("*", "yum update -y", True)
                result.connection.execute("*", "yum install -y docker", True)
                result.connection.execute("*", "systemctl start docker", True)
            else:
                self.logger.info("Docker is already setup")

        for result in self.execute("*", "docker info", True):
            if result.stdout.find(b'Storage Driver: devicemapper') == -1:
                self.logger.info("Setting Docker devicemapper storage")
                result.connection.execute("*", "echo DEVS=/dev/sdb >> /etc/sysconfig/docker-storage-setup", True)
                result.connection.execute("*", "echo VG=DOCKER >> /etc/sysconfig/docker-storage-setup", True)
                result.connection.execute("*", "echo SETUP_LVM_THIN_POOL=yes >> /etc/sysconfig/docker-storage-setup", True)
                result.connection.execute("*", "echo DATA_SIZE=\"70%FREE\" >> /etc/sysconfig/docker-storage-setup", True)
                result.connection.execute("*", "systemctl stop docker", True)
                result.connection.execute("*", "rm -rf /var/lib/docker", True)
                result.connection.execute("*", "wipefs --all /dev/sdb", True)
                result.connection.execute("*", "docker-storage-setup", True)
                result.connection.execute("*", "systemctl start docker", True)
            else:
                self.logger.info("Docker devicemapper storage is already setup")