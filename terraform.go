package main

import (
	log "github.com/Sirupsen/logrus"
	"os"
	"os/exec"
	"text/template"
	"fmt"
	"io"
	"bufio"
	"regexp"
	"strings"
)

// Process deployment and prepare Terraform environment to run the tool against
func RenderTemplate(deployment Deployment) {
	log.Info("Generating Terraform data")

	err := os.MkdirAll(deployment.Name + ".data", os.ModePerm)
	if err != nil {
		panic(err)
	}

	data, err := Asset("templates/" + deployment.Provider + ".tf")
	if err != nil {
		panic(err)
	}

	tmpl, err := template.New("terraform").Parse(string(data))
	if err != nil {
		panic(err)
	}

	file, err := os.Create(deployment.Name + ".data/" + deployment.Provider + ".tf")
	if err != nil {
		panic(err)
	}

	err = tmpl.Execute(file, deployment)
	if err != nil {
		panic(err)
	}

	data, err = Asset("templates/" + deployment.Provider + "_variables.tf")
	if err == nil {
		tmpl, err = template.New("terraform").Parse(string(data))
		if err != nil {
			panic(err)
		}

		file, err = os.Create(deployment.Name + ".data/" + deployment.Provider + "variables.tf")
		if err != nil {
			panic(err)
		}

		err = tmpl.Execute(file, deployment)
		if err != nil {
			panic(err)
		}
	}
}

// Provision executes a Terraform template
// based on the provided deployment, provisioning a cluster.
func Provision(deployment Deployment) {
	log.Info("Creating new cluster")
	err := run("apply", "-state="+deployment.Name + ".data/terraform.tfstate", deployment.Name + ".data")
	if err != nil {
		log.WithFields(log.Fields{"func": "Provision"}).Error(fmt.Sprintf("Can't run Terraform %s", err))
	}
}

// Deprovision executes a Terraform template
// based on the provided deployment.
func Deprovision(deployment Deployment) {
	log.Info("Destroying cluster")
	err := run("destroy", "-force", "-state="+deployment.Name + ".data/terraform.tfstate", deployment.Name + ".data")
	if err != nil {
		log.WithFields(log.Fields{"func": "Deprovision"}).Error(fmt.Sprintf("Can't run Terraform %s", err))
	}
}

func LoadState(deployment Deployment) Deployment {
	log.Info("Gathering cluster information")

	out, err := exec.Command("terraform", "output", "-state=" + deployment.Name + ".data/terraform.tfstate").Output()
	if err != nil {
		panic(err)
	}

	state := string(out)
	deployment.State = DeploymentState{}

	re := regexp.MustCompile("master = ([0-9.]+)")
	deployment.State.Master = re.FindStringSubmatch(state)[1]

	re = regexp.MustCompile("infra = ([0-9.]+)")
	deployment.State.Infra = re.FindStringSubmatch(state)[1]

	re = regexp.MustCompile("nodes = ([0-9.,]+)")
	deployment.State.Nodes = strings.Split(re.FindStringSubmatch(state)[1], ",")

	return deployment
}

func run(cmd ...string) error {
	log.Info("Executing Terraform")
	command := exec.Command("terraform", cmd...)

	stdoutReader, err := command.StdoutPipe()
	if err != nil {
		return err
	}

	stderrReader, err := command.StderrPipe()
	if err != nil {
		return err
	}

	err = command.Start()
	if err != nil {
		return err
	}

	go func() {
		reader := bufio.NewReader(stdoutReader)
		for {
			line, _, err := reader.ReadLine()
			if err != nil {
				if err != io.EOF { log.Error("Problem reading stdout ", err) }
				break
			}
			log.WithFields(log.Fields{"source": "Terraform"}).Info(string(line))
		}
	}()

	go func() {
		reader := bufio.NewReader(stderrReader)
		for {
			line, _, err := reader.ReadLine()
			if err != nil {
				if err != io.EOF { log.Error("Problem reading stderr ", err) }
				break
			}
			log.WithFields(log.Fields{"source": "Terraform"}).Error(string(line))
		}
	}()

	command.Wait()

	log.Info("Terraform finished")

	return nil
}
