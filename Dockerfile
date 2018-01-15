FROM centos

RUN yum install -y https://centos7.iuscommunity.org/ius-release.rpm epel-release
RUN yum install -y python36u python36u-libs python36u-devel python36u-pip git ansible openssh python-cryptography \
  gcc gcc-c++ pyOpenSSL libselinux-python unzip java-1.8.0-openjdk openssl-devel python-passlib && yum clean all

RUN localedef -i en_US -f UTF-8 en_US.UTF-8

WORKDIR /root

RUN git clone https://github.com/openshift/openshift-ansible.git
RUN cd openshift-ansible && git checkout release-3.6 && cd ..

ADD entrypoint.sh requirements.txt /root/

RUN pip3.6 install -r requirements.txt

ADD main.py /root/
ADD dns /root/dns
ADD features /root/features
ADD openshifter /root/openshifter
ADD provider /root/provider

WORKDIR /root/data

ENV OPENSHIFT_ANSIBLE="/root/openshift-ansible"
ENV ROOT_DIR="/root/"

VOLUME ['/root/data']

ENTRYPOINT [ "/root/entrypoint.sh" ]
