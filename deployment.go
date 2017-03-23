package main

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
	"gopkg.in/yaml.v2"
	"io/ioutil"
	"os"
	"path/filepath"
)

// Deployment defines the top-level structure of the
// deployment definition file.
type Deployment struct {
	Provider Provider `yaml:"provider"`
}

// Provider defines properties specific to
// infrastructure provider; not all fields
// may be defined for all providers
type Provider struct {
	Type    string `yaml:"type"`
	Nodes   int    `yaml:"nodes"`
	Machine string `yaml:"machine"`
	Region  string `yaml:"region"`
	Key     string `yaml:"key"`
	Secret  string `yaml:"secret"`
}

// Load loads a YAML representation of the
// deployment definition from the file provided
// by the -definition argument.
func Load() (Deployment, error) {
	dpl := Deployment{}
	var raw []byte
	dpath, _ := filepath.Abs(ddfile)
	_, err := os.Stat(dpath)
	if err != nil {
		return dpl, err
	}
	raw, err = ioutil.ReadFile(dpath)
	if err != nil { // can't read from file
		return dpl, err
	}
	if err := yaml.Unmarshal(raw, &dpl); err != nil { // can't de-serialize
		return dpl, err
	}
	log.WithFields(log.Fields{"func": "Load"}).Debug(dpl)
	return dpl, nil
}

// Create provisions an OpenShift cluster
// based on the deployment definition.
func Create(dpl Deployment) {
	log.WithFields(log.Fields{"func": "Create"}).Info(fmt.Sprintf("Creating OpenShift cluster on %s in %s", dpl.Provider.Type, dpl.Provider.Region))
	envup(dpl)
	Provision(dpl)
}

// Destroy destroys an OpenShift cluster
// based on the deployment definition.
func Destroy(dpl Deployment) {
	log.WithFields(log.Fields{"func": "Destroy"}).Info(fmt.Sprintf("Destroying OpenShift cluster on %s in %s", dpl.Provider.Type, dpl.Provider.Region))
	envup(dpl)
	Deprovision(dpl)
}

func envup(dpl Deployment) {
	if dpl.Provider.Type == "AWS" {
		os.Setenv("AWS_ACCESS_KEY_ID", dpl.Provider.Key)
		os.Setenv("AWS_SECRET_ACCESS_KEY", dpl.Provider.Secret)
	}
}
