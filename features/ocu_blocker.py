from features import Base


class OcuBlocker(Base):
    def check(self):
        return self.deployment['installer'] == 'ocu'

    def applicable(self):
        return ["master"]

    def call(self, connection):
        self.logger.info("Post-installation steps are not supported for `oc cluster up` deployments")
        exit(0)