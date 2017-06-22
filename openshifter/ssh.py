import paramiko


class Ssh:
    def __init__(self, deployment, cluster):
        self.deployment = deployment
        self.cluster = cluster
        self.hosts = {"*": []}

        self.connect("master", cluster.master)
        self.connect("infra", cluster.infra)
        for node in cluster.nodes:
            self.connect("node", node)

    def connect(self, tag, address):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        client.connect(address, username="openshift", key_filename=self.deployment['ssh']['key'],
                       allow_agent=False, look_for_keys=False)

        if tag not in self.hosts:
            self.hosts[tag] = []
        self.hosts[tag].append(client)
        self.hosts["*"].append(client)

    def execute(self, tag, cmd, sudo=False):
        if sudo:
            cmd = 'sudo bash -c \'' + cmd + '\''
        for client in self.hosts[tag]:
            channel = client.get_transport().open_session()
            channel.exec_command(cmd)
            stdout = channel.makefile('r', -1)
            stderr = channel.makefile_stderr('r', -1)
            return SshResult(channel.recv_exit_status(), stdout.read(), stderr.read())

class SshResult:
    def __init__(self, code, stdout, stderr ):
        self.code = code
        self.stdout = stdout
        self.stderr = stderr