provider "google" {
  credentials = "${file(var.account)}"
  project     = "{{.Gce.Project}}"
  region      = "{{.Gce.Region}}"
}

variable "account" {
  type = "string"
  default = "{{.Gce.Account}}"
}

variable "type" {
  type = "string"
  default = "{{.Type}}"
}

variable "sshKey" {
  type = "string"
  default = "{{.Ssh.Key}}"
}

resource "google_compute_network" "network" {
  name                    = "{{.Name}}"
  auto_create_subnetworks = "true"
}

resource "google_compute_firewall" "bastion" {
  name    = "{{.Name}}-bastion"
  network = "${google_compute_network.network.name}"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  target_tags = ["bastion"]
}

resource "google_compute_firewall" "internal" {
  name    = "{{.Name}}-internal"
  network = "${google_compute_network.network.name}"

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  source_ranges = ["10.128.0.0/9"]
}

resource "google_compute_address" "bastion" {
  name = "{{.Name}}-bastion"
}

resource "google_compute_instance" "bastion" {
  count        = 1
  name         = "{{.Name}}-bestion"
  machine_type = "{{.Nodes.Type}}"
  zone         = "{{.Gce.Zone}}"

  tags         = ["bastion"]

  disk {
    image = "${var.type == "ocp" ? "rhel-cloud/rhel-7" : "centos-cloud/centos-7"}"
  }

  metadata {
    ssh-keys = "openshift:${file("${var.sshKey}.pub")}"
  }

  can_ip_forward = true

  network_interface {
    network = "${google_compute_network.network.name}"
    access_config {
      nat_ip = "${google_compute_address.bastion.address}"
    }
  }

  provisioner "remote-exec" {
    connection {
      user = "openshift"
      private_key = "${file("${var.sshKey}")}"
    }
    inline = [
      "sudo bash -c 'echo 1 > /proc/sys/net/ipv4/ip_forward'",
      "sudo bash -c 'echo net.ipv4.ip_forward=1 >> /etc/sysctl.conf'",
      "sudo bash -c 'iptables -t nat -A POSTROUTING -o eth0 -s 10.0.0.0/8 -j MASQUERADE'",
      "sudo bash -c 'yum -y update'",
      "sudo bash -c 'yum install -y docker'",
      "sudo bash -c 'systemctl start docker'",
      "sudo bash -c 'docker pull docker.io/osevg/openshifter:edge'"
    ]
  }

}

resource "google_compute_route" "foobar" {
  name        = "{{.Name}}-router"
  network     = "${google_compute_network.network.name}"
  tags        = ["master", "infra", "node"]
  next_hop_ip = "${google_compute_instance.bastion.network_interface.0.address}"
  dest_range  = "0.0.0.0/0"
  priority    = 100
}

output "master" {
  value = "${google_compute_address.bastion.address}"
}