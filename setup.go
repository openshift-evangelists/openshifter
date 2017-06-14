package main

import (
	"bytes"
	"fmt"
	"path/filepath"
	"text/template"

	log "github.com/Sirupsen/logrus"
)

func SetupEnvironment(deployment Deployment) {
	// toDo https://github.com/marekjelen/openshifter/blob/master/openshifter/src/main/java/eu/mjelen/openshifter/task/openshift/OpenShiftMaster.java
	// toDo https://github.com/marekjelen/openshifter/blob/master/openshifter/src/main/java/eu/mjelen/openshifter/task/component/NodePorts.java
	// todo https://github.com/marekjelen/openshifter/blob/master/openshifter/src/main/java/eu/mjelen/openshifter/task/installer/OcuTask.java

	deployment = LoadState(deployment)

	key, _ := filepath.Abs(deployment.Ssh.Key)

	ConnectSsh("master", deployment.State.Master, key)

	if deployment.Components["logging"] {
		log.Info("Restarting master to provide logging integration in web console")
		_, err := ExecuteSsh("master", "sudo bash -c 'systemctl restart origin-master'")
		if err != nil {
			panic(err)
		}
	}

	if deployment.Components["runAsRoot"] {
		log.Info("Allowing the usage of 'root' containers")
		_, err := ExecuteSsh("master", "sudo bash -c '/usr/local/bin/oc adm policy add-scc-to-group anyuid system:authenticated'")
		if err != nil {
			panic(err)
		}
	}

	log.Info("Setting up Robot account")

	_, err := ExecuteSsh("master", "sudo bash -c '/usr/local/bin/oc create serviceaccount robot --namespace=default'")
	if err != nil {
		panic(err)
	}

	_, err = ExecuteSsh("master", "sudo bash -c '/usr/local/bin/oc adm policy add-cluster-role-to-user cluster-admin system:serviceaccount:default:robot'")
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

	if deployment.Components["pvs"] {
		log.Info("Setting up PVs")

		data, err := Asset("templates/pvs.yml")
		if err != nil {
			panic(err)
		}
		tmpl, err := template.New("pvs").Parse(string(data))
		if err != nil {
			panic(err)
		}
		for i := 1; i <= deployment.Pvs.Count; i++ {
			var doc bytes.Buffer
			var env = make(map[string]interface{})
			var name = "pv-" + fmt.Sprintf("%d", i)
			env["name"] = name
			env["size"] = deployment.Pvs.Size
			err = tmpl.Execute(&doc, env)
			if err != nil {
				panic(err)
			}
			UploadSsh("master", "pv.yml", doc.Bytes())
			_, err = ExecuteSsh("master", "sudo bash -c 'mkdir -p /pvs/"+name+"'")
			if err != nil {
				panic(err)
			}
			_, err = ExecuteSsh("master", "sudo bash -c 'chmod 777 /pvs/"+name+"'")
			if err != nil {
				panic(err)
			}
			_, err = ExecuteSsh("master", "sudo bash -c 'restorecon /pvs/"+name+"'")
			if err != nil {
				panic(err)
			}
			_, err = ExecuteSsh("master", "sudo bash -c '/usr/local/bin/oc create -f pv.yml'")
			if err != nil {
				panic(err)
			}
		}

		if deployment.Gce.ServiceAccount != "" {
			data, err := Asset("templates/gce.pvs.yml")
			if err != nil {
				panic(err)
			}
			tmpl, err := template.New("ansible").Parse(string(data))
			if err != nil {
				panic(err)
			}
			var doc bytes.Buffer
			tmpl.Execute(&doc, deployment)
			UploadSsh("master", "disks.yml", doc.Bytes())
			_, err = ExecuteSsh("master", "sudo bash -c '/usr/local/bin/oc create -f disks.yml'")
			if err != nil {
				panic(err)
			}
		}
	}

	for _, img := range deployment.Docker.Prime {
		_, err = ExecuteSsh("*", "sudo bash -c 'docker pull "+img+"'")
		if err != nil {
			panic(err)
		}
	}

	for _, exec := range deployment.Execute {
		_, err = ExecuteSsh("master", exec)
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
				username := u.Username + fmt.Sprintf("%d", i)
				password := u.Password + fmt.Sprintf("%d", i)

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
