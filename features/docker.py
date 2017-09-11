from features import Base


class Docker(Base):
    def check(self):
        return True

    def applicable(self):
        return ['*', '-pvs']

    def call(self, connection):
        if connection.execute("yum list installed", True).stdout.find('docker') == -1:
            self.logger.info("Installing Docker")
            connection.execute("yum install -y docker", True)
            connection.execute("systemctl start docker", True)
        else:
            self.logger.info("Docker is already setup")

        if connection.execute("docker info", True).stdout.find('Data loop file') > -1:
            self.logger.info("Setting up LVM storage")
            connection.execute("echo DEVS=/dev/sdb >> /etc/sysconfig/docker-storage-setup", True)
            connection.execute("echo VG=DOCKER >> /etc/sysconfig/docker-storage-setup", True)
            connection.execute("echo SETUP_LVM_THIN_POOL=yes >> /etc/sysconfig/docker-storage-setup", True)
            connection.execute("echo DATA_SIZE=\"100%FREE\" >> /etc/sysconfig/docker-storage-setup", True)

            self.logger.info("Stopping Docker")
            connection.execute("systemctl stop docker", True)

            self.logger.info("Resetting Docker storage")
            connection.execute("rm -rf /var/lib/docker", True)
            connection.execute("wipefs --all /dev/sdb", True)
            connection.execute("docker-storage-setup", True)

            self.logger.info("Starting Docker")
            connection.execute("systemctl start docker", True)
        else:
            self.logger.info("Docker devicemapper storage is already setup")

        if 'docker' in self.deployment.data and 'prime' in self.deployment['docker']:
            for image in self.deployment['docker']['prime']:
                connection.execute("docker pull " + image, True)