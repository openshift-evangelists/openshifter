# OpenShifter

A tool to provision and install OpenShift clusters.

Usage:

```bash
penShifter helps with deploying OpenShift clusters

Usage:
  openshifter [command]

Available Commands:
  create      Create new OpenShift cluster as defined in [name].yml
  destroy     Destroy existing OpenShift cluster defined using [name].yml
  help        Help about any command
  version     Print the version number of OpenShifter

Flags:
  -v, --verbose   verbose output

Use "openshifter [command] --help" for more information about a command.
```

Example:

```bash
$ cat work/aws.yml
provider:
  type: AWS
  nodes: 1
  machine: t2.large
  region: eu-west-1
  key: ***********************
  secret: *************************************

$ openshifter create -d work/aws.yml
INFO[0000] Creating OpenShift cluster on AWS in eu-west-1  func=Create
...

$ openshifter destroy -d work/aws.yml
INFO[0000] Destroying OpenShift cluster on AWS in eu-west-1  func=Destroy
...
```
