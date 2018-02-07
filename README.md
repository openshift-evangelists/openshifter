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
$ docker run -ti -v (path to your directory):/root/data docker.io/osevg/openshifter create cluster01
```

__NOTE__: If running `docker` directly from the same folder where descriptors and SSH keys are located, you can pass in ``pwd`` as path to your directory, e.g.

    $ docker run -ti -v `pwd`:/root/data ...


## Provider documentation

### GCE

Following are instructions required to get OpenShift working on top Google Cloud Platform (GCP).

First install the [Google Cloud SDK](register for an account in Google Cloud ()) in your local environment. 
Then, get a GCP account if you don't already own one.

Next, you need to create a project for running OpenShift on it. 
Creating the project can be done either using the GCP user interface or via the [`gce/create-project-gce.sh`](gce/create-project-gce.sh) script.
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

#### Billing under control

When not using OpenShift instance on Google Cloud, make sure you shutdown cluster master and other nodes.
To do that go to `Compute Engine / VM instances` and stop all VM instances.


### AWS

### Azure

### DigitalOcean

## Debugging

In this section you will find instruction on things to try if things are not working:

First, try to remove all OpenShifter images locally and get a fresh one, e.g.

    docker ps -a | awk '{ print $1,$2 }' | grep openshifter | awk '{print $1 }' | xargs -I {} docker rm {}
    docker rmi osevg/openshifter

If that does not solve your problem and you have a partially installed cluster, try destroying it:

    docker run -e -ti -v (path to your directory):/root/data docker.io/osevg/openshifter destroy cluster01

Note that at times, destroying a cluster might timeout. If that happens, simply try again until it completes. 

Finally, you can find out more information about what OpenShifter does by passing in `DEBUG=true` as environment variable:

    docker run -e "DEBUG=true" -ti -v (path to your directory):/root/data docker.io/osevg/openshifter create cluster01


## Logs

If having issues, you should check the logs in the following locations:

Start by looking at the `Serial port 1 console` within the Google Cloud VM instance.
It shows system log of the VM instance and should be your starting point.

OpenShift logs are stored in `/var/log/messages` within the VM instance and they're accessible via SSH.
To access this log you need root access, so to download them you need to do some work.
In the VM instance, copy the log file to the `openshift` user home and change ownership:

```bash
sudo su
cp /var/log/messages /home/openshift
cd /home/openshift
chown openshift:openshift messages 
```   

Then, use the openshifter SSH key in your machine to download it:

```bash
scp -i openshifter-key openshift@<ip address>:messages .
```


## Errors

This section explains common errors found and how to resolve them: 

### `SSHException: not a valid OPENSSH private key file` 

When trying to create the OpenShift cluster, you might see an error like this:

    paramiko.ssh_exception.SSHException: not a valid OPENSSH private key file

This error is complaining about the SSH keys generated above.
There's no need to generate `OPENSSH` keys here, the `RSA` keys generated above should work.
Normally, this error appears when trying to connect to a partially installed OpenShift cluster which maybe used a different key to the one you're passing in now.
So, to overcome this problem, simply destroy the OpenShift cluster and recreate it:

    docker run -e -ti -v (path to your directory):/root/data docker.io/osevg/openshifter destroy cluster01
    docker run -e -ti -v (path to your directory):/root/data docker.io/osevg/openshifter create cluster01     

### `PasswordRequiredException: Private key file is encrypted`

The generated SSH keys are password protected.
Either unencrypt them or regenerate them with an empty password. 
You can pass in `-N ""` to `ssh-keygen` to automate this.

### `UnicodeDecodeError: 'ascii' codec can't decode byte...`

If you get this error, the yaml file contains a non-ASCII character.
To find the offending line(s) call:

    perl -lne 'print if /[^[:ascii:]]/' cluster01.yml

### `InvalidRequestError: 'Invalid JWT: Token must be a short-lived token...`

This error can appear when your computer has gone to sleep and the Docker VM's clock got out of sync.
Restarting the Docker daemon should fix it.

### Accessing console returns `ERR_CONNECTION_TIMED_OUT` 

If OpenShift console times out, you should check whether you can SSH into it.
You can try SSH into the master by pressing the `SSH` button next to the VM instance in the Google Cloud console.
If SSH doesn't work, the machine is unreachable in which case you should click `RESET` button.
Clicking `RESET` restarts the machine.

When the master comes back up, the console might not be available returning `ERR_CONNECTION_REFUSED`.
In this case, check the next section.

### Accessing console returns `ERR_CONNECTION_REFUSED`

If accessing OpenShift console returns `ERR_CONNECTION_REFUSED`, most likely neither `docker` nor OpenShift are running.
Even if the OpenShift console is not accessible, SSH should work.

If using `ocu` installer, it could be that when the machine was restarted, neither `docker` not OpenShift were booted up.
This can be fixed by redeploying the OpenShift cluster, e.g.

```bash
docker run -ti -v (path to your directory):/root/data docker.io/osevg/openshifter create cluster01
```

If still getting `ERR_CONNECTION_REFUSED` after executing this, you might have to manually start `docker`.
To do that, SSH into the machine and execute:

```bash
$ docker ps
Cannot connect to the Docker daemon. Is the docker daemon running on this host?
$ systemctl start docker
$ docker ps
CONTAINER ID        IMAGE                         
<empty>
```

Once `docker` is running again, redeploy the OpenShift cluster, e.g.

```bash
docker run -ti -v (path to your directory):/root/data docker.io/osevg/openshifter create cluster01
```
 
If you go back to the SSH session in the machine, OpenShift should appear as a `docker` container process:

```bash
CONTAINER ID        IMAGE                         
ad22cdca3811        openshift/origin-pod:v3.6.1   
b0e6721aadb0        openshift/origin:v3.6.1       
```

You should now be able to access OpenShift console.
