package main

//go:generate go run templates-gen/main.go

import (
	"fmt"
	"os"

	log "github.com/Sirupsen/logrus"
	"github.com/spf13/cobra"
)

var RootCmd = &cobra.Command{
	Use:   "openshifter",
	Short: "OpenShifter helps with deploying OpenShift clusters",
	Long:  `OpenShifter helps with deploying OpenShift clusters`,
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print the version number of OpenShifter",
	Long:  "It's nice to have a version",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("OpenShifter v0.1")
		os.Exit(0)
	},
}

var createCmd = &cobra.Command{
	Use:   "create [name]",
	Short: "Create new OpenShift cluster as defined in [name].yml",
	Run: func(cmd *cobra.Command, args []string) {
		deployment := loadDeployment(args[0])
		RenderTemplate(deployment)
		Provision(deployment)
		if deployment.Bastion && !IsBastionNode() {
			BastionSetup(deployment)
		} else {
			InstallUsingAnsible(deployment)
			SetupEnvironment(deployment)
		}
	},
}

var provisionCmd = &cobra.Command{
	Use:   "provision [name]",
	Short: "Provisions new OpenShift cluster infrastructure as defined in [name].yml",
	Run: func(cmd *cobra.Command, args []string) {
		deployment := loadDeployment(args[0])
		RenderTemplate(deployment)
		Provision(deployment)
	},
}

var installCmd = &cobra.Command{
	Use:   "install [name]",
	Short: "Install OpenShift on existing cluster as defined in [name].yml",
	Run: func(cmd *cobra.Command, args []string) {
		deployment := loadDeployment(args[0])
		InstallUsingAnsible(deployment)
	},
}

var setupCmd = &cobra.Command{
	Use:   "setup [name]",
	Short: "Sets up installed OpenShift environment",
	Run: func(cmd *cobra.Command, args []string) {
		deployment := loadDeployment(args[0])
		SetupEnvironment(deployment)
	},
}

var destroyCmd = &cobra.Command{
	Use:   "destroy [name]",
	Short: "Destroy existing OpenShift cluster defined using [name].yml",
	Run: func(cmd *cobra.Command, args []string) {
		deployment := loadDeployment(args[0])
		RenderTemplate(deployment)
		Deprovision(deployment)
	},
}

var Verbose bool

func init() {
	RootCmd.PersistentFlags().BoolVarP(&Verbose, "verbose", "v", false, "verbose output")

	RootCmd.AddCommand(versionCmd)
	RootCmd.AddCommand(createCmd)
	RootCmd.AddCommand(provisionCmd)
	RootCmd.AddCommand(installCmd)
	RootCmd.AddCommand(setupCmd)
	RootCmd.AddCommand(destroyCmd)

	if envd := os.Getenv("DEBUG"); envd != "" {
		log.SetLevel(log.DebugLevel)
	}

	if Verbose {
		log.SetLevel(log.DebugLevel)
	}
}

func loadDeployment(name string) Deployment {
	if d, err := Load(name); err != nil {
		log.WithFields(log.Fields{"func": "init"}).Error("Can't load deployment definition due to ", err)
		os.Exit(1)
		return d
	} else {
		return d
	}
}

func main() {
	if err := RootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(-1)
	}
}
