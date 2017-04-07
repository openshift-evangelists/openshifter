package main

import (
	log "github.com/Sirupsen/logrus"
	"golang.org/x/crypto/ssh"
	"github.com/pkg/sftp"
	"io/ioutil"
)

type SshConnection struct {
	Client *ssh.Client
}

var sshConnections map[string][]SshConnection

func init() {
	sshConnections = make(map[string][]SshConnection)
}

func ConnectSsh(name string, address string, key string) {
	connection := SshConnection{}

	sshConfig := &ssh.ClientConfig{
		User: "openshift",
		Auth: []ssh.AuthMethod{
			publicKeyFile(key),
		},
	}

	conn, err := ssh.Dial("tcp", address + ":22", sshConfig)
	if err != nil {
		panic(err)
	}

	connection.Client = conn
	sshConnections[name] = append(sshConnections[name], connection)

	log.Info("Successfully connected to ", address, " as ", name)
}

func ExecuteSsh(name string, command string) ([][]byte, error) {
	result := make([][]byte, len(sshConnections[name]))

	for i, connection := range sshConnections[name] {
		session, err := connection.Client.NewSession()
		if err != nil {
			panic(err)
		}

		modes := ssh.TerminalModes{
			ssh.ECHO:          0,
			ssh.TTY_OP_ISPEED: 14400,
			ssh.TTY_OP_OSPEED: 14400,
		}

		if err := session.RequestPty("xterm", 80, 40, modes); err != nil {
			panic(err)
		}

		data, err := session.Output(command)
		if err != nil {
			result[i] = nil
		}
		result[i] = data
	}
	return result, nil
}

func UploadSsh(name string, remote string, data []byte) error {
	for _, connection := range sshConnections[name] {
		ftp, err := sftp.NewClient(connection.Client)
		if err != nil {
			return err
		}

		defer ftp.Close()

		f, err := ftp.Create(remote)
		if err != nil {
			return err
		}

		if _, err := f.Write(data); err != nil {
			return err
		}
	}
	return nil
}

func publicKeyFile(file string) ssh.AuthMethod {
	buffer, err := ioutil.ReadFile(file)
	if err != nil {
		return nil
	}

	key, err := ssh.ParsePrivateKey(buffer)
	if err != nil {
		return nil
	}
	return ssh.PublicKeys(key)
}
