#!/usr/bin/env bash

docker build -t docker.io/osevg/openshifter:python .
docker push docker.io/osevg/openshifter:python