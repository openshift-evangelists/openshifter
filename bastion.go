package main

import (
	"io/ioutil"
	"os"
)

func BastionSetup(deployment Deployment) {
	deployment = LoadState(deployment)

	ConnectSsh("bastion", deployment.State.Master, deployment.Ssh.Key)

	ExecuteSsh("bastion", "mkdir -p bastion")

	var file string
	var data []byte
	var err error

	file = deployment.Name + ".yml"
	data, err = ioutil.ReadFile(file)
	if err != nil {
		panic(err)
	}
	UploadSsh("bastion", "bastion/" + file, data)

	file = deployment.Ssh.Key
	data, err = ioutil.ReadFile(file)
	if err != nil {
		panic(err)
	}
	UploadSsh("bastion", "bastion/" + file, data)

	file = deployment.Ssh.Key + ".pub"
	data, err = ioutil.ReadFile(file)
	if err != nil {
		panic(err)
	}
	UploadSsh("bastion", "bastion/" + file, data)

	if deployment.Provider == "gce" {
		file = deployment.Gce.Account
		data, err = ioutil.ReadFile(file)
		if err != nil {
			panic(err)
		}
		UploadSsh("bastion", "bastion/" + file, data)
	}

	ExecuteSsh("bastion", "sudo bash -c 'docker run -ti -e BASTION_NODE=true -v `pwd`/bastion:/root/data:Z docker.io/osevg/openshifter:edge create cluster01'")
}

func IsBastionNode() bool {
	return os.Getenv("BASTION_NODE") == "true"
}