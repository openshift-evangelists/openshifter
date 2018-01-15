from features import Base


class LoggingFix(Base):
    def check(self):
        return True

    def applicable(self):
        return ["master"]

    def call(self, connection):
        self.logger.info("Restarting master to fix logging and metrics")
        connection.execute("systemctl restart origin-master-api", True)