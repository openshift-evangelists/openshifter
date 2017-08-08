from functools import reduce

import paramiko

from jinja2 import Template


class Ssh:
    def __init__(self, deployment, cluster):
        self.deployment = deployment
        self.cluster = cluster

        self.hosts = {"*": []}
        self.clients = {}

        self.connect("master", cluster.master.public_address)
        self.connect("infra", cluster.infra.public_address)

        if cluster.pvs:
            self.connect("pvs", cluster.pvs.public_address)

        for node in cluster.nodes:
            self.connect("node", node.public_address)

    def connect(self, tag, address):
        if address not in self.clients:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            client.connect(address, username="openshift", key_filename=self.deployment['ssh']['key'],
                        allow_agent=False, look_for_keys=False)
            self.clients[address] = SshClient(client, address, self.deployment, self.cluster)
            self.hosts["*"].append(address)

        self.clients[address].tag(tag)

        if tag not in self.hosts:
            self.hosts[tag] = []

        self.hosts[tag].append(address)

    def for_tags(self, tags):
        if isinstance(tags, str):
            tags = [tags]

        include = []
        exclude = []

        for tag in tags:
            if tag.startswith("-"):
                exclude.append(tag[1:])
            else:
                include.append(tag)

        hosts = []

        for tag in include:
            for host in self.hosts[tag]:
                if host not in hosts:
                    hosts.append(host)

        result = []

        for host in hosts:
            client = self.clients[host]
            if not client.is_tagged(exclude):
                result.append(client)

        return result

    def for_address(self, address):
        return self.clients[address]


class SshClient:
    def __init__(self, client, address, deployment, cluster):
        self.deployment = deployment
        self.cluster = cluster
        self.client = client
        self.address = address
        self.tags = []

    def tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)

    def is_tagged(self, tags):
        if isinstance(tags, str):
            tags = [tags]
        for tag in tags:
            if tag in self.tags:
                return True

    def execute(self, cmd, sudo=False):
        template = Template(cmd)
        cmd = template.render({'cluster': self.cluster, 'deployment': self.deployment.data})
        if sudo:
            cmd = 'sudo bash -c \'' + cmd + '\''

        channel = self.client.get_transport().open_session()
        channel.exec_command(cmd)
        stdout = channel.makefile('r', -1)
        stderr = channel.makefile_stderr('r', -1)

        return SshResult(channel.recv_exit_status(), stdout.read(), stderr.read(), self)

    def upload(self, target, content):
        template = Template(target)
        target = template.render({'cluster': self.cluster, 'deployment': self.deployment.data})

        sftp = self.client.open_sftp()
        file = sftp.file(target, 'w')
        file.write(content)
        file.close()

    def download(self, target):
        template = Template(target)
        target = template.render({'cluster': self.cluster, 'deployment': self.deployment.data})

        sftp = self.client.open_sftp()
        file = sftp.file(target, 'r')
        data = file.read()
        file.close()

        return data


class SshResult:
    def __init__(self, code, stdout, stderr, connection):
        self.code = code
        self.stdout = stdout.decode('utf-8')
        self.stderr = stderr.decode('utf-8')
        self.connection = connection