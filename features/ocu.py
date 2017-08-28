import os
from features import Base


class Ocu(Base):
    def check(self):
        return self.deployment['installer'] == 'ocu'

    def setup(self):
        self.execute("master", "setenforce 0", True)
        self.execute("master", "systemctl stop NetworkManager.service", True)

        if self.execute("master", "[ -f /bin/oc ]").code == 1:
            self.execute("master", "curl -L -o oc.tar.gz https://github.com/openshift/origin/releases/download/v3.6.0/openshift-origin-client-tools-v3.6.0-c4dd4cf-linux-64bit.tar.gz", True)
            self.execute("master", "tar -xf oc.tar.gz && mv openshift-origin-client-tools-*/oc /bin/ && rm oc.tar.gz && rm -rf openshift-origin-client-tools-*", True)

        if self.execute("master", "grep insecure /etc/docker/daemon.json").code == 1:
            with open(os.path.join(os.path.dirname(__file__), 'ocu_docker.json'), 'r') as file:
                data = file.read()
            self.upload("master", "docker.json", data)
            self.execute("master", "mv docker.json /etc/docker/daemon.json", True)
            self.execute("master", "systemctl restart docker", True)

        if self.execute("master", "oc cluster status", True).code == 1:
            self.execute("master", "oc cluster up --public-hostname=console.{{ deployment.name }}.{{ deployment.dns.suffix }} --routing-suffix=apps.{{ deployment.name }}.{{ deployment.dns.suffix }}", True)

        self.execute("master", "oc login -u system:admin", True)
        self.execute("master", "oc login localhost:8443 -u developer -p developer --insecure-skip-tls-verify=true", False)