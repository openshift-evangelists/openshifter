package main

import (
	"fmt"
	log "github.com/Sirupsen/logrus"
	flag "github.com/ogier/pflag"
	"os"
)

var (
	// the operation to carry out:
	op     string
	oplist = [...]string{"create", "destroy"}
	// the deployment definition file:
	ddfile string
	// the deployment definition:
	dpl Deployment
)

func init() {
	flag.StringVarP(&op, "operation", "o", "create", fmt.Sprintf("The operation to carry out.\n\tSupported values are %v", oplist))
	flag.StringVarP(&ddfile, "definition", "d", "cluster.yml", fmt.Sprintf("The file containing the deployment definition."))
	flag.Usage = func() {
		fmt.Printf("Usage: openshifter [args]\n\n")
		fmt.Println("Arguments:")
		flag.PrintDefaults()
	}
	flag.Parse()

	if envd := os.Getenv("DEBUG"); envd != "" {
		log.SetLevel(log.DebugLevel)
	}

	if d, err := Load(); err != nil {
		log.WithFields(log.Fields{"func": "init"}).Error(fmt.Sprintf("Can't load deployment definition due to %s", err))
		os.Exit(1)
	} else {
		dpl = d
	}
}

func main() {
	switch op {
	case "create":
		Create(dpl)
	case "destroy":
		Destroy(dpl)
	}
}
