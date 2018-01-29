from features import Base


class Basic(Base):
    def check(self):
        return True

    def applicable(self):
        return ['*']

    def call(self, connection):
        self.logger.info("Updating system")
        connection.execute("yum update -y", True)

        self.logger.info("Installing tmux")
        connection.execute("yum install -y tmux sed jq", True)