from features import Base


class LoggingFix(Base):
    def check(self):
        return self.check_component("logging")

    def applicable(self):
        return ["master"]

    def call(self, connection):
        self.logger.info("Restarting master to fix logging")
        connection.execute("systemctl restart origin-master", True)