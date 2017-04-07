variable "account" {
  type = "string"
  default = "{{.Gce.Account}}"
}

variable "infra" {
  type = "string"
  default = "{{if .Nodes.Infra}}true{{else}}false{{end}}"
}

variable "nodes" {
  type = "string"
  default = "{{.Nodes.Count}}"
}

variable "type" {
  type = "string"
  default = "{{.Type}}"
}

variable "ssh_key" {
  type = "string"
  default = "{{.Ssh.Key}}"
}

variable "post_install" {
  type = "list"
  default = [
    "sudo bash -c 'yum -y update'",
    "sudo bash -c 'yum install -y docker'",
    "sudo bash -c 'echo DEVS=/dev/sdb >> /etc/sysconfig/docker-storage-setup'",
    "sudo bash -c 'echo VG=DOCKER >> /etc/sysconfig/docker-storage-setup'",
    "sudo bash -c 'systemctl stop docker'",
    "sudo bash -c 'rm -rf /var/lib/docker'",
    "sudo bash -c 'wipefs --all /dev/sdb'",
    "sudo bash -c 'docker-storage-setup'",
    "sudo bash -c 'systemctl start docker'"
  ]
}

provider "google" {
  credentials = "${file(var.account)}"
  project     = "{{.Gce.Project}}"
  region      = "{{.Gce.Region}}"
}

resource "google_compute_disk" "disk_master_root" {
  name  = "{{.Name}}-master-root"
  type  = "pd-ssd"
  zone  = "{{.Gce.Zone}}"
  image = "${var.type == "ocp" ? "rhel-cloud/rhel-7" : "centos-cloud/centos-7"}"
}

resource "google_compute_disk" "disk_master_docker" {
  name  = "{{.Name}}-master-docker"
  type  = "pd-ssd"
  zone  = "{{.Gce.Zone}}"
  size  = "100"
}

resource "google_compute_instance" "master" {
  count        = 1
  name         = "{{.Name}}-master"
  machine_type = "{{.Nodes.Type}}"
  zone         = "{{.Gce.Zone}}"

  tags         = ["master", "${var.infra == "true" ? "master" : "infra"}", "${var.nodes == "0" ? "node" : "master"}"]

  disk {
    disk = "${google_compute_disk.disk_master_root.name}"
  }

  disk {
    disk = "${google_compute_disk.disk_master_docker.name}"
  }

  metadata {
    ssh-keys = "openshift:${file("${var.ssh_key}.pub")}"
  }

  network_interface {
    network = "{{.Name}}"
  }

  provisioner "remote-exec" {
    connection {
      user = "openshift"
      private_key = "${file("${var.ssh_key}")}"
    }
    inline = "${var.post_install}"
  }

}

resource "google_compute_disk" "disk_infra_root" {
  count = "{{if .Nodes.Infra}}1{{else}}0{{end}}"
  name  = "{{.Name}}-infra-root"
  type  = "pd-ssd"
  zone  = "{{.Gce.Zone}}"
  image = "${var.type == "ocp" ? "rhel-cloud/rhel-7" : "centos-cloud/centos-7"}"
}

resource "google_compute_disk" "disk_infra_docker" {
  count = "{{if .Nodes.Infra}}1{{else}}0{{end}}"
  name  = "{{.Name}}-infra-docker"
  type  = "pd-ssd"
  zone  = "{{.Gce.Zone}}"
  size  = "100"
}

resource "google_compute_instance" "infra" {
  count        = "{{if .Nodes.Infra}}1{{else}}0{{end}}"
  name         = "{{.Name}}-infra"
  machine_type = "{{.Nodes.Type}}"
  zone         = "{{.Gce.Zone}}"
  tags = ["infra"]

  disk {
    disk = "${google_compute_disk.disk_infra_root.name}"
  }

  disk {
    disk = "${google_compute_disk.disk_infra_docker.name}"
  }

  metadata {
    ssh-keys = "openshift:${file("${var.ssh_key}.pub")}"
  }

  network_interface {
    network = "{{.Name}}"
  }

  provisioner "remote-exec" {
    connection {
      user = "openshift"
      private_key = "${file("${var.ssh_key}")}"
    }
    inline = "${var.post_install}"
  }

}

resource "google_compute_disk" "disk_node_root" {
  count = "${var.nodes}"
  name  = "{{.Name}}-node-${count.index}-root"
  type  = "pd-ssd"
  zone  = "{{.Gce.Zone}}"
  image = "${var.type == "ocp" ? "rhel-cloud/rhel-7" : "centos-cloud/centos-7"}"
}

resource "google_compute_disk" "disk_node_docker" {
  count = "${var.nodes}"
  name  = "{{.Name}}-node-${count.index}-docker"
  type  = "pd-ssd"
  zone  = "{{.Gce.Zone}}"
  size  = "100"
}

resource "google_compute_instance" "node" {
  count        = "${var.nodes}"
  name         = "{{.Name}}-node-${count.index}"
  machine_type = "{{.Nodes.Type}}"
  zone         = "{{.Gce.Zone}}"
  tags         = ["node"]

  depends_on = ["google_compute_disk.disk_node_docker", "google_compute_disk.disk_node_root"]

  disk {
    disk = "{{.Name}}-node-${count.index}-root"
  }

  disk {
    disk = "{{.Name}}-node-${count.index}-docker"
  }

  metadata {
    ssh-keys = "openshift:${file("${var.ssh_key}.pub")}"
  }

  network_interface {
    network = "{{.Name}}"
  }

  provisioner "remote-exec" {
    connection {
      user = "openshift"
      private_key = "${file("${var.ssh_key}")}"
    }
    inline = "${var.post_install}"
  }

}

resource "google_compute_target_pool" "masters" {
  name                  = "{{.Name}}-masters"
  instances             = ["${google_compute_instance.master.self_link}"]
}

resource "google_compute_target_pool" "infras" {
  name                  = "{{.Name}}-infras"
  instances             = ["{{if .Nodes.Infra}}${google_compute_instance.infra.self_link}{{else}}${google_compute_instance.master.self_link}{{end}}"]
}

resource "google_compute_address" "cluster" {
  name = "{{.Name}}-cluster"
}

resource "google_compute_forwarding_rule" "masters" {
  name                  = "{{.Name}}-masters"
  load_balancing_scheme = "EXTERNAL"
  ip_address            = "${google_compute_address.cluster.self_link}"
  port_range            = "8443"
  target                = "${google_compute_target_pool.masters.self_link}"
}

resource "google_compute_forwarding_rule" "infras-http" {
  name                  = "{{.Name}}-infras-http"
  load_balancing_scheme = "EXTERNAL"
  ip_address            = "${google_compute_address.cluster.self_link}"
  port_range            = "80"
  target                = "${google_compute_target_pool.infras.self_link}"
}

resource "google_compute_forwarding_rule" "infras-https" {
  name                  = "{{.Name}}-infras-https"
  load_balancing_scheme = "EXTERNAL"
  ip_address            = "${google_compute_address.cluster.self_link}"
  port_range            = "443"
  target                = "${google_compute_target_pool.infras.self_link}"
}

output "master" {
  value = "${google_compute_instance.master.network_interface.0.address}"
}

output "infra" {
  value = "{{if .Nodes.Infra}}${google_compute_instance.infra.network_interface.0.address}{{else}}${google_compute_instance.master.network_interface.0.address}{{end}}"
}

output "nodes" {
  value = "${join(",", google_compute_instance.node.*.network_interface.0.address)}"
}