FROM centos

RUN yum install -y epel-release centos-release-openshift-origin

RUN yum install -y git ansible openssh python-cryptography pyOpenSSL libselinux-python unzip && \
    yum clean all

WORKDIR /root

RUN git clone https://github.com/openshift/openshift-ansible.git
RUN cd openshift-ansible && git checkout release-1.4 && cd ..

RUN curl -o /root/terraform.zip https://releases.hashicorp.com/terraform/0.9.2/terraform_0.9.2_linux_amd64.zip && \
    unzip terraform.zip && rm terraform.zip && ls -la

ADD entrypoint.sh openshifter_linux_amd64 /root/

RUN mv openshifter_linux_amd64 openshifter

WORKDIR /root/data

ENV OPENSHIFT_ANSIBLE="/root/openshift-ansible"

VOLUME ['/root/data']

ENTRYPOINT [ "/root/entrypoint.sh" ]