from features import Base


class GlusterServer(Base):
    def check(self):
        return self.check_component('pvs') and self.deployment['pvs']['type'] == 'gluster'

    def applicable(self):
        return ['pvs']

    def call(self, connection):
        if connection.execute("gluster volume info", True).stdout.find("Volume Name: pvs") == -1:
            self.logger.info("Installing Gluster")
            connection.execute("yum -y update", True)
            connection.execute("yum install -y centos-release-gluster310", True)
            connection.execute("yum install -y glusterfs gluster-cli glusterfs-libs glusterfs-server", True)

            self.logger.info("Setting up storage")
            connection.execute("pvcreate /dev/sdb", True)
            connection.execute("vgcreate PVS /dev/sdb", True)
            connection.execute("lvcreate -l 100%FREE -n PVS PVS", True)
            connection.execute("mkfs.xfs -i size=512 /dev/mapper/PVS-PVS", True)
            connection.execute("mkdir -p /data/brick1", True)
            connection.execute("echo \"/dev/mapper/PVS-PVS /data/brick1 xfs defaults 1 2\" >> /etc/fstab", True)
            connection.execute("mount -a && mount", True)

            self.logger.info("Setting up Gluster")
            connection.execute("systemctl start glusterd", True)
            connection.execute("systemctl enable glusterd", True)
            connection.execute("mkdir -p /data/brick1/pvs", True)
            connection.execute("gluster volume create pvs {{deployment.name}}-pvs:/data/brick1/pvs", True)
            connection.execute("gluster volume start pvs", True)
            connection.execute("gluster volume info", True)
        else:
            self.logger.info("Gluster server is running")