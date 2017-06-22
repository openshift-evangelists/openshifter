import logging

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


def _check_component(deployment, name):
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
    if _check_component(deployment, 'logging'):
        ssh.execute("master", "systemctl restart origin-master", True)

    if _check_component(deployment, 'runAsRoot'):
        ssh.execute("master", "oc adm policy add-scc-to-group anyuid system:authenticated", False)

    ssh.execute("master", "oc create serviceaccount robot --namespace=default", False)
    ssh.execute("master", "oc adm policy add-cluster-role-to-user cluster-admin system:serviceaccount:default:robot", False)
    ssh.execute("master", "oc sa get-token robot --namespace=default", False)

    for user in deployment['users']:
        if 'generic' in user and user['generic']:
            for x in range(user['min'], user['max']):
                username = user['username'] + str(x)
                password = user['password'] + str(x)

                ssh.execute("master", "htpasswd -b /etc/origin/master/htpasswd " + username + " " + password, True)
        else:
            username = user['username']
            password = user['password']

            ssh.execute("master", "htpasswd -b /etc/origin/master/htpasswd " + username + " " + password, True)

            if 'admin' in user and user['admin']:
                ssh.execute("master", "oc adm policy add-cluster-role-to-user cluster-admin " + username, False)

            if 'sudoer' in user and user['sudoer']:
                ssh.execute("master", "c adm policy add-cluster-role-to-user sudoer " + username, False)

    if 'execute' in deployment.data:
        for cmd in deployment['execute']:
            ssh.execute("master", cmd, False)

    if 'docker' in deployment.data and 'prime' in deployment['docker']:
        for image in deployment['docker']['prime']:
            ssh.execute("*", "docker pull " + image, True)


