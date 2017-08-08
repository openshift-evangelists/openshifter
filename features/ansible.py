import subprocess
import threading
import os

from jinja2 import Template

from features import Base


class Ansible(Base):
    def check(self):
        return self.deployment['installer'] == 'ansible'

    def setup(self):
        file = open(os.path.dirname(os.path.realpath(__file__)) + "/ansible.jinja", "r")
        template = file.read()
        file.close()
        template = Template(template)

        inventory = os.path.abspath(self.deployment.dir + "/ansible.ini")
        file = open(inventory, "w")
        file.write(template.render({'cluster': self.cluster, 'deployment': self.deployment.data}))
        file.close()
        os.environ['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
        os.environ['ANSIBLE_PRIVATE_KEY_FILE'] = os.path.abspath(self.deployment['ssh']['key'])

        if 'OPENSHIFT_ANSIBLE' in os.environ:
            ansible_dir = os.environ['OPENSHIFT_ANSIBLE']
        else:
            ansible_dir = os.path.abspath('openshift-ansible')

        path = os.path.join(ansible_dir, 'playbooks/byo/config.yml')

        cmd = ["ansible-playbook", '-i', inventory, path]

        process = subprocess.Popen(["git", "checkout", self.deployment.version.git()], cwd=ansible_dir,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, universal_newlines=True)

        def reader(label, pipe):
            while True:
                buf = pipe.readline()
                if buf == '':
                    break
                else:
                    buf = buf.strip()
                if buf != '':
                    self.logger.info(label + " => " + buf)

        threading.Thread(target=reader, args=("stderr", process.stderr)).start()
        threading.Thread(target=reader, args=("stdout", process.stdout)).start()

        process.wait()

        self.logger.info("Executing " + str(cmd) + ' in ' + os.getcwd())

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
                                   universal_newlines=True)

        def reader(label, pipe):
            while True:
                buf = pipe.readline()
                if buf == '':
                    break
                else:
                    buf = buf.strip()
                if buf != '':
                    self.logger.info(label + " => " + buf)

        threading.Thread(target=reader, args=("stderr", process.stderr)).start()
        threading.Thread(target=reader, args=("stdout", process.stdout)).start()

        process.wait()

        self.logger.info("Exit code " + str(process.returncode))