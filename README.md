# OpenShifter

A tool to provision and install OpenShift clusters.

Usage:

```bash
OpenShifter helps with deploying OpenShift clusters

Usage:
  openshifter [command]

Available Commands:
  create      Create new OpenShift cluster as defined in [name].yml
  destroy     Destroy existing OpenShift cluster defined using [name].yml
  help        Help about any command
  install     Install OpenShift on existing cluster as defined in [name].yml
  setup       Sets up installed OpenShift environment
  version     Print the version number of OpenShifter

Flags:
  -v, --verbose   verbose output

Use "openshifter [command] --help" for more information about a command.
```

Example:

```bash
$ cat cluster01.yml
provider: gce
dns:
  zone: <zone name>
  suffix: <domain name>

ssh:
  key: cluster

users:
  - username: admin
    password: password
    admin: true
  - username: user
    password: password
    sudoer: true
  - username: user
    password: password
    generic: true
    min: 0
    max: 3

nodes:
  count: 1
  infra: false
  type: n1-standard-1

gce:
  account: <json file name>
  region: us-west1
  zone: us-west1-a
  project: <project name/id>

$ openshifter create clutser01
...

$ openshifter destroy cluster01
...
```