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
name: cluster-name # file base name wihtou .yml if not specified
bastion: false # Bationed deployment, WIP, do not use
provider: gce
type: origin # origin or ocp
release: v1.5.1 # full version for Origin; for OCP master.minor is enough
installer: ansible # currently only Ansible

dns:
  zone: <zone name> # zone name depends on provider; if set to "nip" will use nip.io
  suffix: <domain name> # DNS to access cluster (console, *.apps).cluster-name.suffix

# Generate SSH key pair: e.g. `ssh-keygen -t rsa -b 4096 -C "me@here.com" -f openshift-key`
ssh:
  key: <name of the key pair, e.g., openshift-key>

components:
  cockpit: false # if true, deploys Cockpit
  metrics: false # if true, deploys Metrics
  logging: false # if true, deploys Logging
  pvs: false # enables PersistentVolumes

users: # creates user and associated project named as the user
  - username: admin
    password: password
    admin: true # cluster-admin role
  - username: user
    password: password
    sudoer: true
    execute:
      - new-app mjelen/example # execute in the context of user project
  - username: user
    password: password
    generic: true # generates user0 up to user3 with password0 up to password3
    min: 0
    max: 3

pvs: # PVs always use hostPath
  type: '' # if set to "gluster" will deploy gluster node and setup the hostPath into Gluster backed directory
  size: 1 # Size of the generated PVs in GB
  count: 1 # Generate 1 PV

nodes:
  count: 1 # container nodes in the cluster
  infra: false # separate master and infra
  podsPerCore: 10 # how many pods can be on a node per core
  type: n1-standard-1 # See a list of machine types: https://cloud.google.com/compute/docs/machine-types
  disk:
    size: 100 # The docker storage disk in GB

execute:
  - oc new-app mjelen/example # execute commands on master node

docker:
  prime: # pre-pull images on all container nodes
    - mjelen/example

gce:
  account: <json file name>
  # See a list of regions & zones: https://cloud.google.com/compute/docs/regions-zones/regions-zones
  region: us-west1
  zone: us-west1-a
  project: <GCP Project ID>
  serviceaccount: <secvice account e-mail> # associate the SA with the VM
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
