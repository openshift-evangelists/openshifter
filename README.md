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

## Definition file 

```yaml
$ cat cluster01.yml
provider: gce
dns:
  zone: <zone name>
  suffix: <domain name>

# Generate SSH key pair: e.g. `ssh-keygen -t rsa -b 4096 -C "me@here.com" -f openshift-key`
ssh:
  key: <name of the key pair, e.g., openshift-key>

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
  type: n1-standard-1 # See a list of machine types: https://cloud.google.com/compute/docs/machine-types

gce:
  account: <json file name>
  # See a list of regions & zones: https://cloud.google.com/compute/docs/regions-zones/regions-zones
  region: us-west1
  zone: us-west1-a
  project: <GCP Project ID>
```

## Getting started

Create an empty directory. Add public and private SSH key that will be used to connect to the  provisioned machines. If
you do not want to reuse existing key, simply generate new one

```
$ ssh-keygen -f openshift-key
```

and you will get two files `mykey` and `mykey.pub`.
 
Create yaml definition for your cluster as defined above and name the file as the cluster should be named, e.g. 
`cluster01.yml`.

Check the provider documentation for provider-specific files and configuration to add to the definition.

Start the deployment process

```
$ docker run -ti -v (path to your directory):/root/data docker.io/osevg/openshifter create cluster01
```

## Provider documentation

### GCE

1. Create a Google Cloud Patlform Project
1. Enable Compute Engine API
1. Enable DNS API
1. Create Cloud DNS Zone (e.g., openshift-mydomain-com for openshift.mydomain.com suffix)
1. Create a new Service Account with Project Owner role, and furnish a new JSON key

### AWS

### Azure

### DigitalOcean