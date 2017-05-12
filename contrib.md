# Development and Contributing

The following is a description of the build process and how to contribute
to the OpenShifter project.

- [Preparing your development environment](#preparing-your-development-environment)
- [Building locally](#building-locally)
- [Contribute](#contribute)
 - [Coding conventions](#coding-conventions)
 - [Testing](#testing)
 - [Handling of templates](#handling-of-templates)
 - [Shipping](#shipping)
 - [CI pipeline](#ci-pipeline)

## Preparing your development environment

OpenShifter is developed in [Go](https://golang.org/) and uses [Terraform](https://www.terraform.io/)
and [Ansible](https://www.ansible.com/) to provision the runtime environment and
install OpenShift, as well as Docker to ship all artifacts necessary.

Before you start, make sure that you have Go [1.8](https://golang.org/doc/go1.8) installed.

## Building locally

You will need the following to build and execute OpenShifter locally:

```bash
# to get the source code:
$ go get github.com/osevg/openshifter
# to populate the templates (more details below):
$ go generate
# to build the `openshifter` binary, making it available in $GOPATH/bin/
$ go install
# now you can execute it:
$ openshifter
OpenShifter helps with deploying OpenShift clusters

Usage:
  openshifter [command]

Available Commands:
  create      Create new OpenShift cluster as defined in [name].yml
  destroy     Destroy existing OpenShift cluster defined using [name].yml
  install     Install OpenShift on existing cluster as defined in [name].yml
  provision   Provisions new OpenShift cluster infrastructure as defined in [name].yml
  setup       Sets up installed OpenShift environment
  version     Print the version number of OpenShifter

Flags:
  -v, --verbose   verbose output

Use "openshifter [command] --help" for more information about a command.
```

## Contribute

If you want to contribute to OpenShifter, make sure that first you create your
own fork of [osevg/openshifter](https://github.com/osevg/openshifter).

In the following we walk you through how to set up your environment in order to
contribute to OpenShifter.

### Coding conventions

Whenever you edit an existing `.go` source file or add a new one, either on save
in your editor or IDE (preferred) or manually on the CLI, make sure that you run
the following tools in order to ensure uniformity and code quality:

The Go Meta Linter [alecthomas/gometalinter](https://github.com/alecthomas/gometalinter) with
the following parameters:

```--vendor, --disable-all, --enable=vet, --enable=vetshadow, --enable=golint, --enable=ineffassign, --enable=goconst, --enable=errcheck, --tests, --json, .
```

The [goimports](https://godoc.org/golang.org/x/tools/cmd/goimports) tool.

### Testing

Whenever you edit an existing `.go` source file or add a new one, either on save
in your editor or IDE (preferred) or manually on the CLI, make sure that you run
`go test -coverprofile -short` to execute the tests and display test coverage.
We aim for a [test coverage](https://blog.golang.org/cover) of over 50%.

### Handling of templates

We want to ship the `openshifter` binary without external dependencies
as such (leaving the Terraform and Ansible binaries aside, for now).
This means that the Terraform and Ansible templates you find in
[templates/](templates/) somehow need to be made part of the `openshifter` binary.
For this, we're using [go generate](https://blog.golang.org/generate):

- In [main.go](main.go) you find the line `//go:generate go run templates-gen/main.go`
- Before a `go build` or `go install`, you need to execute `go generate`
- The `go generate` command will execute [templates-gen/main.go](templates-gen/main.go) which in turn will generate `templates/templates.go`
- In the generated file `templates/templates.go` you find the function `templates.Asset()` that you use to load the content of the respective template file

Note: `templates/templates.go` is not checked into Git and at least,
whenever you change or add any template you need to run `go generate`
in the repo root directory to generate the templates.

### Shipping

To bundle and ship all required artifacts, that is, the `openshifter` binary
itself, Terraform and Ansible, we use Docker with the following build steps
as defined in the [build.sh](build.sh) script:

1. Build the `openshifter` binary
1. Build the Docker image `openshifter:latest` based on the [Dockerfile](Dockerfile), which installs all dependencies incl. Terraform and Ansible
1. Push the Docker image to `docker.io/osevg/openshifter:latest`

### CI pipeline

We use Travis for automated builds: https://travis-ci.org/osevg/openshifter

The build definition is available in [.travis.yml](.travis.yml) and a build
is triggered on push to a branch and on PRs.
