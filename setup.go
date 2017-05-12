package main

import (
	"path/filepath"

	log "github.com/Sirupsen/logrus"
)

func SetupEnvironment(deployment Deployment) {
	// toDo https://github.com/marekjelen/openshifter/blob/master/openshifter/src/main/java/eu/mjelen/openshifter/task/openshift/OpenShiftMaster.java
	// toDo https://github.com/marekjelen/openshifter/blob/master/openshifter/src/main/java/eu/mjelen/openshifter/task/component/NodePorts.java
	// toDo https://github.com/marekjelen/openshifter/blob/master/openshifter/src/main/java/eu/mjelen/openshifter/task/component/PersistentVolumes.java
	// todo https://github.com/marekjelen/openshifter/blob/master/openshifter/src/main/java/eu/mjelen/openshifter/task/component/Cockpit.java

	// todo https://github.com/marekjelen/openshifter/blob/master/openshifter/src/main/java/eu/mjelen/openshifter/task/installer/OcuTask.java

	deployment = LoadState(deployment)

	key, _ := filepath.Abs(deployment.Ssh.Key)

	ConnectSsh("master", deployment.State.Master, key)

	if deployment.Components["runAsRoot"] {
		log.Info("Allowing the usage of 'root' containers")
		_, err := ExecuteSsh("master", "sudo bash -c '/usr/local/bin/oc adm policy analyze-scc-to-group anyuid system:authenticated'")
		if err != nil {
			panic(err)
		}
	}

	log.Info("Setting up Robot account")

	_, err := ExecuteSsh("master", "sudo bash -c '/usr/local/bin/oc create serviceaccount robot --namespace=default'")
	if err != nil {
		panic(err)
	}

	_, err = ExecuteSsh("master", "sudo bash -c '/usr/local/bin/oc adm policy analyze-cluster-role-to-user cluster-admin system:serviceaccount:default:robot'")
	if err != nil {
		panic(err)
	}

	_, err = ExecuteSsh("master", "/usr/local/bin/oc sa get-token robot --namespace=default")

	setupUsers(deployment)

	log.Info("Executing custom commands")

	for _, cmd := range deployment.Execute {
		log.Info("Command ", cmd)
		_, err := ExecuteSsh("master", "sudo bash -c '/usr/local/bin/oc "+cmd+"'")
		if err != nil {
			panic(err)
		}
	}

}

func setupUsers(deployment Deployment) {
	log.Info("Setting up user accounts")

	for _, u := range deployment.Users {
		log.Info("Setting up user account: ", u.Username)

		if u.Generic {
			for i := u.Min; i <= u.Max; i++ {
				username := u.Username + string(i)
				password := u.Password + string(i)

				log.Info("Generic user ", username)

				_, err := ExecuteSsh("master", "sudo bash -c 'htpasswd -b /etc/origin/master/htpasswd "+username+" "+password+"'")
				if err != nil {
					panic(err)
				}

				executeIn(username, u.Execute)

			}
		} else {
			_, err := ExecuteSsh("master", "sudo bash -c 'htpasswd -b /etc/origin/master/htpasswd "+u.Username+" "+u.Password+"'")
			if err != nil {
				panic(err)
			}

			if u.Admin {
				log.Info("Making user omnipotent")
				_, err := ExecuteSsh("master", "sudo bash -c '/usr/local/bin/oc adm policy add-cluster-role-to-user cluster-admin "+u.Username+"'")
				if err != nil {
					panic(err)
				}
			}

			if u.Sudoer {
				log.Info("Making user sudoer")
				_, err := ExecuteSsh("master", "sudo bash -c '/usr/local/bin/oc adm policy add-cluster-role-to-user sudoer "+u.Username+"'")
				if err != nil {
					panic(err)
				}
			}

			executeIn(u.Username, u.Execute)
		}
	}
}

func executeIn(namespace string, cmds []string) {
	log.Info("Creating user project")

	_, err := ExecuteSsh("master", "sudo bash -c '/usr/local/bin/oc new-project "+namespace+"'")
	if err != nil {
		panic(err)
	}

	_, err = ExecuteSsh("master", "sudo bash -c '/usr/local/bin/oc adm policy add-role-to-user admin  "+namespace+" -n "+namespace+"'")
	if err != nil {
		panic(err)
	}

	for _, cmd := range cmds {
		log.Info("Executing for user ", cmd)

		_, err := ExecuteSsh("master", "sudo bash -c '/usr/local/bin/oc "+cmd+" -n "+namespace+"'")
		if err != nil {
			panic(err)
		}
	}
}
