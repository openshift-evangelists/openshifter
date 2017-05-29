package main

import (
	"io/ioutil"
	"os"
	"path/filepath"

	log "github.com/Sirupsen/logrus"
	"gopkg.in/yaml.v2"
)

// Deployment defines the top-level structure of the
// deployment definition file.
type Deployment struct {
	Name       string                `yaml:"name"`
	Bastion    bool                  `yaml:"bastion"`
	Provider   string                `yaml:"provider"`
	Type       string                `yaml:"type"`
	Release    string                `yaml:"release"`
	Installer  string                `yaml:"installer"`
	Dns        DeploymentDns         `yaml:"dns"`
	Ssh        DeploymentSsh         `yaml:"ssh"`
	Nodes      DeploymentNodes       `yaml:"nodes"`
	Components map[string]bool       `yaml:"components"`
	Users      []DeploymentUser      `yaml:"users"`
	Execute    []string              `yaml:"execute"`
	Docker     DeploymentDocker      `yaml:"docker"`
	Pvs        DeploymentPvs         `yaml:"pvs"`
	Aws        DeploymentAwsProvider `yaml:"aws"`
	Gce        DeploymentGceProvider `yaml:"gce"`
	State      DeploymentState       `yaml:"-"`
}

type DeploymentState struct {
	Master string
	Infra  string
	Nodes  []string
}

type DeploymentDns struct {
	Zone   string `yaml:"zone"`
	Suffix string `yaml:"suffix"`
}

type DeploymentSsh struct {
	Key string `yaml:"key"`
}

type DeploymentNodes struct {
	Type  string                         `yaml:"type"`
	Count int                            `yaml:"count"`
	Infra bool                           `yaml:"infra"`
	Disks []DeploymentNodesDisk          `yaml:"disks"`
	Nodes map[string]DeploymentNodesNode `yaml:"nodes"`
}

type DeploymentNodesNode struct {
	Disks []DeploymentNodesDisk `yaml:"disks"`
}

type DeploymentNodesDisk struct {
	Name string `yaml:"name"`
	Size int    `yaml:"size"`
	Boot string `yaml:"boot"`
	Type string `yaml:"Type"`
}

type DeploymentUser struct {
	Username string   `yaml:"username"`
	Password string   `yaml:"password"`
	Sudoer   bool     `yaml:"sudoer"`
	Admin    bool     `yaml:"admin"`
	Generic  bool     `yaml:"generic"`
	Min      int      `yaml:"min"`
	Max      int      `yaml:"max"`
	Execute  []string `yaml:"execute"`
}

type DeploymentDocker struct {
	Prime []string `yaml:"prime"`
}

type DeploymentPvs struct {
	Type  string `yaml:"prime"`
	Count int    `yaml:"count"`
	Size  int    `yaml:"size"`
}

type DeploymentAwsProvider struct {
	Zone   string `yaml:"zone"`
	Region string `yaml:"region"`
	Key    string `yaml:"key"`
	Secret string `yaml:"secret"`
}

type DeploymentGceProvider struct {
	Zone    string `yaml:"zone"`
	Region  string `yaml:"region"`
	Project string `yaml:"project"`
	Account string `yaml:"account"`
}

// Load loads a YAML representation of the
// deployment definition from the file provided
// by the -definition argument.
func Load(name string) (Deployment, error) {
	deployment := defaults(name)
	var raw []byte
	dpath, _ := filepath.Abs(name + ".yml")
	_, err := os.Stat(dpath)
	if err != nil {
		return deployment, err
	}
	raw, err = ioutil.ReadFile(dpath)
	if err != nil { // can't read from file
		return deployment, err
	}
	if err := yaml.Unmarshal(raw, &deployment); err != nil { // can't de-serialize
		return deployment, err
	}
	log.WithFields(log.Fields{"func": "Load"}).Debug(deployment)
	if deployment.Name == "" {
		deployment.Name = name
	}

	envup(deployment)

	return deployment, nil
}

func defaults(name string) Deployment {
	return Deployment{
		Name:      name,
		Type:      "origin",
		Release:   "v1.5.1",
		Installer: "ansible",
		Nodes: DeploymentNodes{
			Count: 0,
			Infra: false,
		},
	}
}

func envup(deployment Deployment) {
	if deployment.Provider == "AWS" {
		os.Setenv("AWS_ACCESS_KEY_ID", deployment.Aws.Key)
		os.Setenv("AWS_SECRET_ACCESS_KEY", deployment.Aws.Secret)
	}
}
