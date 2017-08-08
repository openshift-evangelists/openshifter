from features import Base


class RunAsRoot(Base):
    def check(self):
        return self.check_component("runAsRoot")

    def applicable(self):
        return ["master"]

    def call(self, connection):
        self.logger.info("Enabling run as root containers")
        connection.execute("oc adm policy add-scc-to-group anyuid system:authenticated")