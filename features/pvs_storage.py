from features import Base


class PVsStorage(Base):
    def check(self):
        return self.check_component('pvs')

    def setup(self):
        if self.deployment['pvs']['type'] == 'gluster':
            self.gluster()
        else:
            self.hostPath()

    def hostPath(self):
        for result in self.execute("*", "mount"):
            if result.stdout.find(b'/dev/mapper/DOCKER-PVS') == -1:
                result.connection.execute("*", "lvcreate -l 100%FREE -n PVS DOCKER", True)
                result.connection.execute("*", "mkfs.xfs /dev/mapper/DOCKER-PVS", True)
                result.connection.execute("*", "mkdir -p /var/lib/origin/openshift.local.volumes", True)
                result.connection.execute("*", "mount /dev/mapper/DOCKER-PVS /var/lib/origin/openshift.local.volumes", True)
                result.connection.execute("*", "echo \"/dev/mapper/DOCKER-PVS /var/lib/origin/openshift.local.volumes xfs defaults 0 1\" >> /etc/fstab", True)
                result.connection.execute("*", "ln -s /var/lib/origin/openshift.local.volumes /pvs", True)
            else:
                self.logger.info("Persistent volumes are already setup")

    def gluster(self):
        self.execute("pvs", "yum -y update", True)
        self.execute("pvs", "yum install -y centos-release-gluster310", True)
        self.execute("pvs", "yum install -y glusterfs gluster-cli glusterfs-libs glusterfs-server", True)
        self.execute("pvs", "pvcreate /dev/sdb", True)
        self.execute("pvs", "vgcreate PVS /dev/sdb", True)
        self.execute("pvs", "lvcreate -l 100%FREE -n PVS PVS", True)
        self.execute("pvs", "mkfs.xfs -i size=512 /dev/mapper/PVS-PVS", True)
        self.execute("pvs", "mkdir -p /data/brick1", True)
        self.execute("pvs", "echo \"/dev/mapper/PVS-PVS /data/brick1 xfs defaults 1 2\" >> /etc/fstab", True)
        self.execute("pvs", "mount -a && mount", True)
        self.execute("pvs", "systemctl start glusterd", True)
        self.execute("pvs", "systemctl enable glusterd", True)
        self.execute("pvs", "mkdir -p /data/brick1/pvs", True)
        self.execute("pvs", "gluster volume create pvs {{deployment.name}}-pvs:/data/brick1/pvs", True)
        self.execute("pvs", "gluster volume start pvs", True)
        self.execute("pvs", "gluster volume info", True)

        self.execute("*", "yum install -y centos-release-gluster310", True)
        self.execute("*", "yum install -y glusterfs gluster-cli glusterfs-libs glusterfs-fuse", True)
        self.execute("*", "mount -t glusterfs {{deployment.name}}-pvs:/pvs /pvs", True)