#!/usr/bin/env bash

go-bindata templates/...
go build

gox -osarch="linux/amd64"
docker build --no-cache -t docker.io/osevg/openshifter:15 .
docker push docker.io/osevg/openshifter:15
