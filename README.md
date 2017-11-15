# OpenShifter

[![Build Status](https://travis-ci.org/openshift-evangelists/openshifter.svg?branch=master)](https://travis-ci.org/openshift-evangelists/openshifter)
[![Dependency Status](https://gemnasium.com/badges/github.com/openshift-evangelists/openshifter.svg)](https://gemnasium.com/github.com/openshift-evangelists/openshifter)

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

Create an empty directory. Add public and private SSH key that will be used to connect to the provisioned machines. If
you do not want to reuse existing key, simply generate new one

```
$ ssh-keygen -f openshift-key -N ""
```

and you will get two files `mykey` and `mykey.pub`.

If you want to reuse existing keys, make sure they're unencrypted or have empty password.

Create yaml definition for your cluster as defined above and name the file as the cluster should be named, e.g.
`cluster01.yml`.

Check the provider documentation for provider-specific files and configuration to add to the definition.

Start the deployment process

```
$ docker run -ti -v `pwd`:/root/data docker.io/osevg/openshifter create cluster01
```

## Provider documentation

### GCE

Following are instructions required to get OpenShift working on top Google Cloud Platform (GCP).

First, you need to get a GCP account and create a project for running OpenShift on it.
Creating the project can be done using the GCP user interface or via the [`gce/create-project-gce.sh`](gce/create-project-gce.sh) script.
The instructions for using the user interface are not available yet, so the best would be to use the script.

To run the script, you just need to provide a name and the email registered with your GCP account:

    ./gce/create-project-gce.sh openshift-on-google me@here.com

Calling this script will generate a project on GCP called `openshift-on-google-me-here-com`.
The script also generates `openshift-on-google-me-here-com.json` file which is needed for OpenShifter to talk to GCP.  
This JSON file name, along with the generate project name, need to be added to the cluster yaml file:

    gce:
      account: os-v1-me-here-com.json
      region: us-west1
      zone: us-west1-a
      project: os-v1-me-here-com

Next, call create on OpenShifter as shown in the general instructions above.

### AWS

### Azure

### DigitalOcean

## Debugging

In this section you will find instruction on things to try if things are not working:

First, try to remove all OpenShifter images locally and get a fresh one, e.g.

    docker ps -a | awk '{ print $1,$2 }' | grep openshifter | awk '{print $1 }' | xargs -I {} docker rm {}
    docker rmi osevg/openshifter

If that does not solve your problem and you have a partially installed cluster, try destroying it:

    docker run -e -ti -v `pwd`:/root/data docker.io/osevg/openshifter destroy cluster01

Note that at times, destroying a cluster might timeout. If that happens, simply try again until it completes. 

Finally, you can find out more information about what OpenShifter does by passing in `DEBUG=true` as environment variable:

    docker run -e "DEBUG=true" -ti -v `pwd`:/root/data docker.io/osevg/openshifter create cluster01


## Errors

This section explains common errors found and how to resolve them: 

### `SSHException: not a valid OPENSSH private key file` 

When trying to create the OpenShift cluster, you might see an error like this:

    paramiko.ssh_exception.SSHException: not a valid OPENSSH private key file

This error is complaining about the SSH keys generated above.
There's no need to generate `OPENSSH` keys here, the `RSA` keys generated above should work.
Normally, this error appears when trying to connect to a partially installed OpenShift cluster which maybe used a different key to the one you're passing in now.
So, to overcome this problem, simply destroy the OpenShift cluster and recreate it:

    docker run -e -ti -v `pwd`:/root/data docker.io/osevg/openshifter destroy cluster01
    docker run -e -ti -v `pwd`:/root/data docker.io/osevg/openshifter create cluster01     

## `PasswordRequiredException: Private key file is encrypted`

The generated SSH keys are password protected.
Either unencrypt them or regenerate them with an empty password. 
You can pass in `-N ""` to `ssh-keygen` to automate this.

## `UnicodeDecodeError: 'ascii' codec can't decode byte...`

If you get this error, the yaml file contains a non-ASCII character.
To find the offending line(s) call:

    perl -lne 'print if /[^[:ascii:]]/' cluster01.yml
