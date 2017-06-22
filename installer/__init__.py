from installer.ansible import Ansible

INSTALLERS = {
    'ansible': Ansible
}


def find(deployment):
    return INSTALLERS[deployment['installer']](deployment)