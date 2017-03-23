# OpenShifter

A tool to provision and install OpenShift clusters.

Usage:

```bash
Usage: openshifter [args]

Arguments:
  -d, --definition string
        The file containing the deployment definition. (default "cluster.yml")
  -o, --operation string
        The operation to carry out.
        Supported values are [create destroy] (default "create")
```

Example:

```bash
$ cat work/aws.yml
provider:
  type: AWS
  region: eu-west-1
  key: ***********************
  secret: *************************************

$ openshifter -d work/aws.yml
INFO[0000] Creating OpenShift cluster on AWS in eu-west-1  func=Create
```
