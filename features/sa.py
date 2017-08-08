from features import Base


class ServiceAccount(Base):
    def check(self):
        return True

    def applicable(self):
        return ["master"]

    def call(self, connection):
        self.logger.info("Creating service account")
        connection.execute("oc create serviceaccount robot --namespace=default")
        connection.execute("oc adm policy add-cluster-role-to-user cluster-admin system:serviceaccount:default:robot")
        connection.execute("oc sa get-token robot --namespace=default")
