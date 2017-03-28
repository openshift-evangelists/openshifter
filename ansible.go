package main

import (
	log "github.com/Sirupsen/logrus"
	"os/exec"
	"regexp"
	"strings"
	"os"
	"text/template"
	"bufio"
	"io"
	"path/filepath"
)

func InstallUsingAnsible(deployment Deployment) {
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

	err = os.MkdirAll(deployment.Name + ".data", os.ModePerm)
	if err != nil {
		panic(err)
	}

	data, err := Asset("templates/ansible.tmpl")
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

	command := exec.Command("ansible-playbook", "-i", deployment.Name + ".data/ansible.ini", path)

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
			log.WithFields(log.Fields{"source": "Ansible"}).Info(string(line))
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
			log.WithFields(log.Fields{"source": "Ansible"}).Error(string(line))
		}
	}()

	command.Wait()

	log.Info("Ansible finished")

	return nil
}
