import logging
import re

import yaml

POST_PROVISION = [
    "yum -y update",
    "yum install -y docker",
    "echo DEVS=/dev/sdb >> /etc/sysconfig/docker-storage-setup",
    "echo VG=DOCKER >> /etc/sysconfig/docker-storage-setup",
    "echo SETUP_LVM_THIN_POOL=yes >> /etc/sysconfig/docker-storage-setup",
    "echo DATA_SIZE=\"70%FREE\" >> /etc/sysconfig/docker-storage-setup",
    "systemctl stop docker",
    "rm -rf /var/lib/docker",
    "wipefs --all /dev/sdb",
    "docker-storage-setup",
    "systemctl start docker",
    "lvcreate -l 100%FREE -n PVS DOCKER",
    "mkfs.xfs /dev/mapper/DOCKER-PVS",
    "mkdir -p /var/lib/origin/openshift.local.volumes",
    "mount /dev/mapper/DOCKER-PVS /var/lib/origin/openshift.local.volumes",
    "echo \"/dev/mapper/DOCKER-PVS /var/lib/origin/openshift.local.volumes xfs defaults 0 1\" >> /etc/fstab",
    "mkdir -p /pvs",
]


def check_component(deployment, name):
    return name in deployment['components'] and deployment['components'][name]


def post_provision(ssh):
    for cmd in POST_PROVISION:
        logging.info("Executing " + cmd)
        result = ssh.execute("*", cmd, True)
        if result.code == 0:
            logging.info("Successfully finished")
            logging.error(result.stdout)
        else:
            logging.error("Command failed")
            logging.error(result.stderr)


def post_install(ssh, deployment):
    if check_component(deployment, 'logging'):
        ssh.execute("master", "systemctl restart origin-master", True)

    if check_component(deployment, 'runAsRoot'):
        ssh.execute("master", "oc adm policy add-scc-to-group anyuid system:authenticated", False)

    if check_component(deployment, 'pvs'):
        for i in range(0, deployment['pvs']['count']):
            name = 'pv-' + str(i)
            pv = {
                'apiVersion': 'v1',
                'kind': 'PersistentVolume',
                'metadata': {
                    'name': name
                },
                'spec': {
                    'capacity': {
                        'storage': str(deployment['pvs']['size']) + 'Gi'
                    },
                    'accessModes': [
                        'ReadWriteMany',
                        'ReadWriteOnce',
                        'ReadOnlyMany'
                    ],
                    'hostPath': {
                        'path': '/pvs/' + name
                    },
                    'persistentVolumeReclaimPolicy': 'Recycle'
                }
            }
            ssh.execute("master", "mkdir -p /pvs/" + name, True)
            ssh.execute("master", "chmod 777 /pvs/" + name, True)
            ssh.execute("master", "restorecon /pvs/" + name, True)

            ssh.write("master", "pv.yml", yaml.dump(pv))
            ssh.execute("master", "oc create -f pv.yml", False)

    ssh.execute("master", "oc create serviceaccount robot --namespace=default", False)
    ssh.execute("master", "oc adm policy add-cluster-role-to-user cluster-admin system:serviceaccount:default:robot",
                False)
    ssh.execute("master", "oc sa get-token robot --namespace=default", False)

    for user in deployment['users']:
        if 'generic' in user and user['generic']:
            for x in range(user['min'], user['max']):
                username = user['username'] + str(x)
                password = user['password'] + str(x)
                project = re.sub(r'[^-0-9a-z]', '-', username)

                ssh.execute("master", "htpasswd -b /etc/origin/master/htpasswd " + username + " " + password, True)
                ssh.execute("master", "oc new-project " + project, False)
                ssh.execute("master", "oc adm policy add-role-to-user admin " + username + " -n " + project, False)

                if 'execute' in user:
                    for cmd in user['execute']:
                        ssh.execute("master", cmd + " -n " + project, False)
        else:
            username = user['username']
            password = user['password']
            project = re.sub(r'[^-0-9a-z]', '-', username)

            ssh.execute("master", "htpasswd -b /etc/origin/master/htpasswd " + username + " " + password, True)
            ssh.execute("master", "oc new-project " + project, False)
            ssh.execute("master", "oc adm policy add-role-to-user admin " + username + " -n " + project, False)

            if 'admin' in user and user['admin']:
                ssh.execute("master", "oc adm policy add-cluster-role-to-user cluster-admin " + username, False)

            if 'sudoer' in user and user['sudoer']:
                ssh.execute("master", "oc adm policy add-cluster-role-to-user sudoer " + username, False)

            if 'execute' in user:
                for cmd in user['execute']:
                    ssh.execute("master", cmd + " -n " + username, False)

    if 'execute' in deployment.data:
        for cmd in deployment['execute']:
            ssh.execute("master", cmd, False)

    if 'docker' in deployment.data and 'prime' in deployment['docker']:
        for image in deployment['docker']['prime']:
            ssh.execute("*", "docker pull " + image, True)
