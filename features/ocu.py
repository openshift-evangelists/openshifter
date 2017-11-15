import os
from features import Base


class Ocu(Base):
    def check(self):
        return self.deployment['installer'] == 'ocu'

    def setup(self):
        self.execute("master", "setenforce 0", True)
        self.execute("master", "systemctl stop NetworkManager.service", True)

        if self.execute("master", "[ -f /bin/oc ]").code == 1:
            cmd = 'curl -s https://github.com/openshift/origin/releases | '
            cmd += 'sed -n "s/^.*openshift-origin-client-tools-{{ deployment.release }}'
            cmd += '\.\([0-9]*\)-\{0,1\}\([^-]*\)-\([a-z0-9]*\)-linux-64bit.tar.gz.*$/'
            cmd += '{{ deployment.release }} \\1 \\2 \\3/p" | head -n 1'

            major, minor, rel, hash = self.execute("master", cmd).stdout.strip().split(" ")

            version = "%s.%s" % (major, minor)

            if rel != '':
                version += "-%s" % rel

            link = 'https://github.com/openshift/origin/releases/download/%s/openshift-origin-client-tools-' % version
            link += '%s-%s-linux-64bit.tar.gz' % (version, hash)

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

            if self.check_component('servicecatalog'):
                cmd += ' --service-catalog=true'

            self.execute("master", cmd, True)

        self.execute("master", "oc login -u system:admin", True)
        self.execute("master", "oc login localhost:8443 -u developer -p developer --insecure-skip-tls-verify=true", False)