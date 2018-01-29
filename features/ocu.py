import os
from features import Base


class Ocu(Base):
    def check(self):
        return self.deployment['installer'] == 'ocu'

    def setup(self):
        self.execute("master", "setenforce 0", True)
        self.execute("master", "systemctl stop NetworkManager.service", True)

        if self.execute("master", "[ -f /bin/oc ]").code == 1:
            self.execute("master", 'curl -s https://api.github.com/repos/openshift/origin/releases > origin.releases.tmp')

            cmd = 'cat origin.releases.tmp | '
            cmd += 'jq \'.[] | select(.tag_name=="{{ deployment.release }}") | .assets[] | '
            cmd += 'select(.name | test("^.*openshift-origin-client-tools.*linux-64bit.*$")) | .browser_download_url\''

            link = self.execute("master", cmd).stdout.strip()

            self.execute("master", "curl -L -o oc.tar.gz %s" % link, True)
            self.execute("master", "tar -xf oc.tar.gz && mv openshift-origin-client-tools-*/oc /bin/ && rm oc.tar.gz && rm -rf openshift-origin-client-tools-*", True)

        if self.execute("master", "grep insecure /etc/docker/daemon.json").code == 1:
            with open(os.path.join(os.path.dirname(__file__), 'ocu_docker.json'), 'r') as file:
                data = file.read()
            self.upload("master", "docker.json", data)
            self.execute("master", "mv docker.json /etc/docker/daemon.json", True)
            self.execute("master", "systemctl restart docker", True)

        if self.execute("master", "oc cluster status", True).code == 1:
            cmd = "oc cluster up"
            cmd += ' --public-hostname=console.{{ deployment.name }}.{{ deployment.dns.suffix }}'
            cmd += ' --routing-suffix=apps.{{ deployment.name }}.{{ deployment.dns.suffix }}'

            if self.check_component('logging'):
                cmd += ' --logging=true'

            if self.check_component('metrics'):
                cmd += ' --metrics=true'

            self.execute("master", cmd, True)

        self.execute("master", "oc login -u system:admin", True)
        self.execute("master", "oc login localhost:8443 -u developer -p developer --insecure-skip-tls-verify=true", False)