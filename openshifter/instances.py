import logging
import re
from functools import reduce
from eventbrite import Eventbrite

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

PVS = [
    "yum -y update",
    "yum install -y centos-release-gluster310",
    "yum install -y glusterfs gluster-cli glusterfs-libs glusterfs-server",
    "pvcreate /dev/sdb",
    "vgcreate PVS /dev/sdb",
    "lvcreate -l 100%FREE -n PVS PVS",
    "mkfs.xfs -i size=512 /dev/mapper/PVS-PVS",
    "mkdir -p /data/brick1",
    "echo \"/dev/mapper/PVS-PVS /data/brick1 xfs defaults 1 2\" >> /etc/fstab",
    "mount -a && mount",
    "systemctl start glusterd",
    "systemctl enable glusterd",
    "mkdir -p /data/brick1/pvs",
    "gluster volume create pvs {{name}}-pvs:/data/brick1/pvs",
    "gluster volume start pvs",
    "gluster volume info",
]


def check_component(deployment, name):
    return name in deployment['components'] and deployment['components'][name]


def post_provision(ssh, deployment):
    cmds = POST_PROVISION
    if 'pvs' in deployment['components'] and deployment['components']['pvs'] and 'pvs' in deployment.data:
        if 'type' in deployment['pvs'] and deployment['pvs']['type'] == 'gluster':
            for cmd in PVS:
                cmd = cmd.replace("{{name}}", deployment.name)
                logging.info("Executing %s" % cmd)
                result = ssh.execute("pvs", cmd, True)
                if reduce(lambda c, r: c and r.code == 0, result, True):
                    logging.info("Successfully finished")
                else:
                    logging.error("Command failed")
            cmds += [
                "yum install -y centos-release-gluster310",
                "yum install -y glusterfs gluster-cli glusterfs-libs glusterfs-fuse",
                "mount -t glusterfs {{name}}-pvs:/pvs /pvs"
            ]

    for cmd in cmds:
        cmd = cmd.replace("{{name}}", deployment.name)
        logging.info("Executing %s" % cmd)
        result = ssh.execute("master", cmd, True)

        if deployment['nodes']['infra']:
            result += ssh.execute("infra", cmd, True)

        if deployment['nodes']['count'] > 0:
            result += ssh.execute("node", cmd, True)

        if reduce(lambda c,r: c and r.code == 0, result, True):
            logging.info("Successfully finished")
        else:
            logging.error("Command failed")


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
        if 'eventbrite' in user:
            token = deployment['eventbrite']['token']
            event = user['eventbrite']

            eventbrite = Eventbrite(token)
            attendees = eventbrite.get_event_attendees(event)

            for attendee in attendees['attendees']:
                project = generate_user(attendee['profile']['email'], attendee['profile']['email'], ssh)

                if 'execute' in user:
                    execute_for_user(project, user['execute'], ssh)

        elif 'generic' in user and user['generic']:
            for x in range(user['min'], user['max']):
                username = user['username'] + str(x)
                password = user['password'] + str(x)

                project = generate_user(username, password, ssh)

                if 'execute' in user:
                    execute_for_user(project, user['execute'], ssh)

        else:
            username = user['username']
            project = generate_user(username, user['password'], ssh)

            if 'admin' in user and user['admin']:
                ssh.execute("master", "oc adm policy add-cluster-role-to-user cluster-admin " + username, False)

            if 'sudoer' in user and user['sudoer']:
                ssh.execute("master", "oc adm policy add-cluster-role-to-user sudoer " + username, False)

            if 'execute' in user:
                execute_for_user(project, user['execute'], ssh)

    if 'execute' in deployment.data:
        for cmd in deployment['execute']:
            ssh.execute("master", cmd, False)

    if 'docker' in deployment.data and 'prime' in deployment['docker']:
        for image in deployment['docker']['prime']:
            ssh.execute("*", "docker pull " + image, True)


def generate_user(username, password, ssh):
    project = re.sub(r'[^-0-9a-z]', '-', username)

    logging.info("Generating user %s with password %s and project %s", username, password, project)

    ssh.execute("master", "htpasswd -b /etc/origin/master/htpasswd " + username + " " + password, True)
    ssh.execute("master", "oc new-project " + project, False)
    ssh.execute("master", "oc adm policy add-role-to-user admin " + username + " -n " + project, False)

    return project


def execute_for_user(project, execute, ssh):
    for cmd in execute:
        ssh.execute("master", cmd + " -n " + project, False)