package main

import (
	log "github.com/Sirupsen/logrus"
	"os"
	"os/exec"
	"text/template"
	"fmt"
	"io"
	"bytes"
)

// Process deployment and prepare Terraform environment to run the tool against
func RenderTemplate(deployment Deployment) {
	log.Info("Generating Terraform data")

	err := os.MkdirAll(deployment.Name + ".data", os.ModePerm)
	if err != nil {
		panic(err)
	}

	data, err := Asset("templates/aws.tf")
	if err != nil {
		panic(err)
	}

	file, err := os.Create(deployment.Name + ".data/aws.tf")
	if err != nil {
		panic(err)
	}

	io.Copy(file, bytes.NewReader(data))

	data, err = Asset("templates/variables.tf")
	if err != nil {
		panic(err)
	}

	tmpl, err := template.New("terraform").Parse(string(data))
	if err != nil {
		panic(err)
	}

	file, err = os.Create(deployment.Name + ".data/variables.tf")
	if err != nil {
		panic(err)
	}

	err = tmpl.Execute(file, deployment)
	if err != nil {
		panic(err)
	}
}

// Provision executes a Terraform template
// based on the provided deployment, provisioning a cluster.
func Provision(deployment Deployment) {
	log.Info("Creating new cluster")
	err := run("apply", deployment.Name + ".data")
	if err != nil {
		log.WithFields(log.Fields{"func": "Provision"}).Error(fmt.Sprintf("Can't run Terraform %s", err))
	}
}

// Deprovision executes a Terraform template
// based on the provided deployment.
func Deprovision(deployment Deployment) {
	log.Info("Destroying cluster")
	err := run("destroy", "-force",  deployment.Name + ".data")
	if err != nil {
		log.WithFields(log.Fields{"func": "Deprovision"}).Error(fmt.Sprintf("Can't run Terraform %s", err))
	}
}

func run(cmd ...string) error {
	log.Info("Executing Terraform")
	command := exec.Command("terraform", cmd...)

	var stdout, stderr bytes.Buffer
	command.Stdout = &stdout
	command.Stderr = &stderr

	err := command.Start()
	if err != nil {
		return err
	}

	go func() {
		for {
			line, err := stdout.ReadBytes('\n')
			if err != nil {
				if err != io.EOF { log.Error("Problem reading stdout ", err) }
				break
			}
			log.WithFields(log.Fields{"source": "Terraform"}).Info(line)
		}
	}()

	go func() {
		for {
			line, err := stderr.ReadBytes('\n')
			if err != nil {
				if err != io.EOF { log.Error("Problem reading stderr ", err) }
				break
			}
			log.WithFields(log.Fields{"source": "Terraform"}).Error(line)
		}
	}()

	command.Wait()

	log.Info("Terraform finished")

	return nil
}
