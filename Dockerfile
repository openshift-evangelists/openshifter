FROM centos

RUN yum install -y https://centos7.iuscommunity.org/ius-release.rpm epel-release centos-release-openshift-origin
RUN yum install -y python36u python36u-libs python36u-devel python36u-pip git ansible openssh python-cryptography \
  gcc gcc-c++ pyOpenSSL libselinux-python unzip java-1.8.0-openjdk openssl-devel && yum clean all

WORKDIR /root

RUN git clone https://github.com/openshift/openshift-ansible.git
RUN cd openshift-ansible && git checkout release-1.5 && cd ..

ADD entrypoint.sh requirements.txt /root/

RUN pip3.6 install -r requirements.txt

ADD main.py /root/
ADD dns /root/dns
ADD installer /root/installer
ADD openshifter /root/openshifter
ADD provider /root/provider

WORKDIR /root/data

ENV OPENSHIFT_ANSIBLE="/root/openshift-ansible"

VOLUME ['/root/data']

ENTRYPOINT [ "/root/entrypoint.sh" ]