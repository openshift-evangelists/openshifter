from features import Base


class RunAsRoot(Base):
    def check(self):
        return self.check_component("runAsRoot")

    def setup(self):
        self.execute("master", "oc adm policy add-scc-to-group anyuid system:authenticated")