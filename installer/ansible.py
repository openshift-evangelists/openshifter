import logging
import subprocess
import threading
import os

from jinja2 import Template


class Ansible:
    def __init__(self, deployment):
        self.deployment = deployment
        pass

    def install(self, cluster):
        file = open(os.path.dirname(os.path.realpath(__file__)) + "/ansible.jinja", "r")
        template = file.read()
        file.close()
        template = Template(template)

        inventory = os.path.abspath(self.deployment.dir + "/ansible.ini")
        file = open(inventory, "w")
        file.write(template.render({'cluster': cluster, 'deployment': self.deployment.data}))
        file.close()
        os.environ['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
        os.environ['ANSIBLE_PRIVATE_KEY_FILE'] = os.path.abspath(self.deployment['ssh']['key'])

        if 'OPENSHIFT_ANSIBLE' in os.environ:
            path = os.environ['OPENSHIFT_ANSIBLE'] + '/playbooks/byo/config.yml'
        else:
            path = os.path.abspath('openshift-ansible') + '/playbooks/byo/config.yml'

        cmd = ["ansible-playbook", '-vvvv', '-i', inventory, path]

        logging.info("Executing " + str(cmd) + ' in ' + os.getcwd())

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
                    logging.info(label + " => " + buf)

        threading.Thread(target=reader, args=("stderr", process.stderr)).start()
        threading.Thread(target=reader, args=("stdout", process.stdout)).start()

        process.wait()

        logging.info("Exit code " + str(process.returncode))
