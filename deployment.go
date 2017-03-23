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
	Provider string `yaml:"provider"`
}

// Load loads a YAML representation of the
// deployment definition from the file provided
// by the -definition argument.
func Load() (Deployment, error) {
	dpl := Deployment{}
	dpath, _ := filepath.Abs(ddfile)
	if _, err := os.Stat(dpath); err != nil {
		return dpl, err
	}
	if raw, err := ioutil.ReadFile(dpath); err != nil { // can't read from file
		return dpl, err
	} else {
		if err := yaml.Unmarshal([]byte(raw), &dpl); err != nil { // can't de-serialize
			return dpl, err
		}
	}
	return dpl, nil
}

// Create provisions an OpenShift cluster
// based on the deployment definition.
func Create(dpl Deployment) {
	log.WithFields(log.Fields{"func": "Create"}).Info(fmt.Sprintf("Creating OpenShift cluster on %s", dpl.Provider))
}

// Destroy destroys an OpenShift cluster
// based on the deployment definition.
func Destroy(dpl Deployment) {

}
