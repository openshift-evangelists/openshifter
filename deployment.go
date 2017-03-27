package main

import (
	log "github.com/Sirupsen/logrus"
	"gopkg.in/yaml.v2"
	"io/ioutil"
	"os"
	"path/filepath"
)

// Deployment defines the top-level structure of the
// deployment definition file.
type Deployment struct {
	Name	string `yaml:"name"`
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
func Load(name string) (Deployment, error) {
	dpl := Deployment{}
	var raw []byte
	dpath, _ := filepath.Abs(name + ".yml")
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
	if dpl.Name == "" {
		dpl.Name = name
	}

	envup(dpl)

	return dpl, nil
}

func envup(dpl Deployment) {
	if dpl.Provider.Type == "AWS" {
		os.Setenv("AWS_ACCESS_KEY_ID", dpl.Provider.Key)
		os.Setenv("AWS_SECRET_ACCESS_KEY", dpl.Provider.Secret)
	}
}
