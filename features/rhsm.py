from features import Base


class RHSM(Base):
    def check(self):
        return self.deployment['type'] == 'ocp' and 'rhsm' in self.deployment.data

    def applicable(self):
        return ["*"]

    def call(self, connection):
        self.logger.info("Register subscriptions")

        u = self.deployment['rhsm']['username']
        p = self.deployment['rhsm']['password']
        pool = self.deployment['rhsm']['pool']

        repos = ''
        repos += ' --enable="rhel-7-server-rpms"'
        repos += ' --enable="rhel-7-server-extras-rpms"'
        repos += ' --enable="rhel-7-fast-datapath-rpms"'
        repos += ' --enable="rhel-7-server-ose-3.%s-rpms"' % (self.deployment.version.major)

        connection.execute("/sbin/subscription-manager register --username=\"%s\" --password=\"%s\"" % (u, p), True)
        connection.execute("/sbin/subscription-manager attach --pool=%s" % pool, True)
        connection.execute('/sbin/subscription-manager repos --disable="*"', True)
        connection.execute('/sbin/subscription-manager repos %s' % repos, True)
