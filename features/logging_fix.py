from features import Base


class LoggingFix(Base):
    def check(self):
        return self.check_component("logging")

    def setup(self):
        self.execute("master", "systemctl restart origin-master", True)