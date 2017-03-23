package main

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
	"io/ioutil"
	"os"
	"os/exec"
	"strconv"
	"strings"
)

// Provision executes a Terraform template
// based on the provided deployment, provisioning a cluster.
func Provision(dpl Deployment) {
	err := os.MkdirAll("tmp/", os.ModePerm)
	if err != nil {
		log.WithFields(log.Fields{"func": "Provision"}).Error(fmt.Sprintf("Can't create temporary working directory for Terraform %s", err))
		return
	}
	copy("templates/main.tf", "tmp/main.tf")
	replace("templates/variables.tf", "tmp/variables.tf")
	err = run("apply", "tmp/")
	if err != nil {
		log.WithFields(log.Fields{"func": "Provision"}).Error(fmt.Sprintf("Can't run Terraform %s", err))
	}
}

// Deprovision executes a Terraform template
// based on the provided deployment.
func Deprovision(dpl Deployment) {
	err := run("destroy", "-force", "tmp/")
	if err != nil {
		log.WithFields(log.Fields{"func": "Deprovision"}).Error(fmt.Sprintf("Can't run Terraform %s", err))
	}
}

func replace(from, to string) error {
	b, err := ioutil.ReadFile(from)
	if err != nil {
		return err
	}
	v := strings.Replace(string(b), "AWS_REGION", dpl.Provider.Region, 1)
	v = strings.Replace(v, "MACHINE_TYPE", dpl.Provider.Machine, 1)
	v = strings.Replace(v, "NUM_WORKER_NODES", strconv.Itoa(dpl.Provider.Nodes), 1)
	err = ioutil.WriteFile(to, []byte(v), 0644)
	if err != nil {
		return err
	}
	return nil
}

func run(cmd ...string) error {
	out, err := exec.Command("terraform", cmd...).Output()
	if err != nil {
		return err
	}
	log.WithFields(log.Fields{"func": "run"}).Info(fmt.Sprintf("%s", out))
	return nil
}
