from features import Base


class ServiceAccount(Base):
    def check(self):
        return True

    def setup(self):
        self.execute("master", "oc create serviceaccount robot --namespace=default")
        self.execute("master", "oc adm policy add-cluster-role-to-user cluster-admin system:serviceaccount:default:robot")
        self.execute("master", "oc sa get-token robot --namespace=default")
