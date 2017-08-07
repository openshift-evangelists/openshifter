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
            self.clients[address] = client
            self.hosts["*"].append(client)

        if tag not in self.hosts:
            self.hosts[tag] = []
        self.hosts[tag].append(self.clients[address])

    def execute(self, tag, cmd, sudo=False):
        result = []
        template = Template(cmd)
        cmd = template.render({'cluster': self.cluster, 'deployment': self.deployment.data})
        if sudo:
            cmd = 'sudo bash -c \'' + cmd + '\''
        for client in self.hosts[tag]:
            channel = client.get_transport().open_session()
            channel.exec_command(cmd)
            stdout = channel.makefile('r', -1)
            stderr = channel.makefile_stderr('r', -1)
            result.append(SshResult(channel.recv_exit_status(), stdout.read(), stderr.read(), self))
        return result

    def write(self, tag, target, content):
        template = Template(target)
        target = template.render({'cluster': self.cluster, 'deployment': self.deployment.data})
        for client in self.hosts[tag]:
            sftp = client.open_sftp()
            file = sftp.file(target, 'w')
            file.write(content)
            file.close()

    def read(self, tag, target):
        template = Template(target)
        target = template.render({'cluster': self.cluster, 'deployment': self.deployment.data})
        for client in self.hosts[tag]:
            sftp = client.open_sftp()
            file = sftp.file(target, 'r')
            data = file.read()
            file.close()
            return data

class SshResult:
    def __init__(self, code, stdout, stderr, connection):
        self.code = code
        self.stdout = stdout
        self.stderr = stderr
        self.connection = connection