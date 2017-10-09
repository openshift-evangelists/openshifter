from features import Base


class GlusterClient(Base):
    def check(self):
        return self.check_component('pvs') and self.deployment['pvs']['type'] == 'gluster'

    def applicable(self):
        return ["*", "-pvs"]

    def call(self, connection):
        if self.deployment['type'] == 'ocp':
            self.logger.info("Installing Gluster using RHEL RPMS")
            connection.execute("subscription-manager repos --enable rh-gluster-3-client-for-rhel-7-server-rpms", True)
            connection.execute("yum install -y glusterfs glusterfs-cli glusterfs-libs glusterfs-fuse", True)
        else:
            self.logger.info("Installing Gluster client")
            connection.execute("yum install -y centos-release-gluster310", True)
            connection.execute("yum install -y glusterfs gluster-cli glusterfs-libs glusterfs-fuse", True)

        self.logger.info("Mounting Gluster storage")
        connection.execute("mkdir -p /pvs", True)
        connection.execute("mount -t glusterfs {{deployment.name}}-pvs:/pvs /pvs", True)
