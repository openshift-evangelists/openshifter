# OpenShifter

[![Build Status](https://travis-ci.org/openshift-evangelists/openshifter.svg?branch=python)](https://travis-ci.org/openshift-evangelists/openshifter)

A tool to provision and install OpenShift clusters.

Usage:

```bash
Usage: main.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  create     Provision + Install + Setup
  destroy    Destroy infrastructure
  install    Install OpenShift on infrastructure
  provision  Provision infrastructure
  setup      Run post-installation setup
```

## Definition file

See `examples` directory.

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
