package main

import (
	"bufio"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"text/template"

	log "github.com/Sirupsen/logrus"
	"github.com/osevg/openshifter/templates"
)

func InstallUsingAnsible(deployment Deployment) {
	deployment = LoadState(deployment)

	err := os.MkdirAll(deployment.Name+".data", os.ModePerm)
	if err != nil {
		panic(err)
	}

	data, err := templates.Asset("templates/ansible.tmpl")
	if err != nil {
		panic(err)
	}

	tmpl, err := template.New("ansible").Parse(string(data))
	if err != nil {
		panic(err)
	}

	file, err := os.Create(deployment.Name + ".data/ansible.ini")
	if err != nil {
		panic(err)
	}

	err = tmpl.Execute(file, deployment)
	if err != nil {
		panic(err)
	}

	runAnsible(deployment)
}

func runAnsible(deployment Deployment) error {
	log.Info("Executing Ansible")

	path, err := filepath.Abs("openshift-ansible")

	if pth, ok := os.LookupEnv("OPENSHIFT_ANSIBLE"); ok {
		path = pth
	}

	path = filepath.Join(path, "playbooks/byo/config.yml")

	key, err := filepath.Abs(deployment.Ssh.Key)

	os.Setenv("ANSIBLE_HOST_KEY_CHECKING", "False")
	os.Setenv("ANSIBLE_PRIVATE_KEY_FILE", key)

	command := exec.Command("ansible-playbook", "-i", deployment.Name+".data/ansible.ini", path)

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
				if err != io.EOF {
					log.Error("Problem reading stdout ", err)
				}
				break
			}
			log.WithFields(log.Fields{"source": "Ansible"}).Info(string(line))
		}
	}()

	go func() {
		reader := bufio.NewReader(stderrReader)
		for {
			line, _, err := reader.ReadLine()
			if err != nil {
				if err != io.EOF {
					log.Error("Problem reading stderr ", err)
				}
				break
			}
			log.WithFields(log.Fields{"source": "Ansible"}).Error(string(line))
		}
	}()

	command.Wait()

	log.Info("Ansible finished")

	return nil
}
