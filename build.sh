#!/usr/bin/env bash

go generate
go build

gox -osarch="linux/amd64"
docker build -t docker.io/osevg/openshifter:latest .
docker push docker.io/osevg/openshifter:latest
