import logging
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
            self.clients[address] = SshClient(address, self.deployment, self.cluster)
            self.clients[address].connect()
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
    def __init__(self, address, deployment, cluster):
        self.deployment = deployment
        self.cluster = cluster
        self.client = None
        self.address = address
        self.tags = []

        self.logger = logging.getLogger("SSH(%s)" % self.address)

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        self.client.connect(self.address, username="openshift", key_filename=self.deployment['ssh']['key'],
                       allow_agent=False, look_for_keys=False)

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

        self.logger.debug("Executing: %s", cmd)

        try:
            channel = self.client.get_transport().open_session()
        except TimeoutError:
            self.connect()
            channel = self.client.get_transport().open_session()

        channel.exec_command(cmd)
        stdout = channel.makefile('r', -1)
        stderr = channel.makefile_stderr('r', -1)

        result = SshResult(channel.recv_exit_status(), stdout.read(), stderr.read(), self)

        self.logger.debug("Exit code: %s", result.code)
        self.logger.debug("STDOUT: %s", result.stdout)
        self.logger.debug("STDERR: %s", result.stderr)
        return result

    def upload(self, target, content):
        template = Template(target)
        target = template.render({'cluster': self.cluster, 'deployment': self.deployment.data})

        try:
            sftp = self.client.open_sftp()
        except TimeoutError:
            self.connect()
            sftp = self.client.open_sftp()

        file = sftp.file(target, 'w')
        file.write(content)
        file.close()



    def download(self, target):
        template = Template(target)
        target = template.render({'cluster': self.cluster, 'deployment': self.deployment.data})

        try:
            sftp = self.client.open_sftp()
        except TimeoutError:
            self.connect()
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