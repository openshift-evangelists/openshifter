import click

import logging

from openshifter.deployment import Deployment
from openshifter.ssh import Ssh
import openshifter.instances
import provider
import dns
import installer


def load_environment(name):
    deployment = Deployment(name)
    infrastructure = provider.find(deployment)
    cluster = infrastructure.validate()
    return deployment, infrastructure, cluster


@click.group()
def cli():
    pass


@click.command()
@click.argument('name')
def provision(name):
    """Provision infrastructure"""
    deployment, infrastructure, cluster = load_environment(name)
    if not cluster.valid:
        cluster = infrastructure.create()
    driver = dns.find(deployment)
    driver.create(cluster)
    ssh = Ssh(deployment, cluster)
    openshifter.instances.post_provision(ssh)


@click.command()
@click.argument('name')
def install(name):
    """Install OpenShift on infrastructure"""
    deployment, infrastructure, cluster = load_environment(name)
    if cluster.valid:
        driver = installer.find(deployment)
        driver.install(cluster)
    else:
        logging.error("Cluster is not valid. Did you provision it?")


@click.command()
@click.argument('name')
def setup(name):
    """Run post-installation setup"""
    deployment, infrastructure, cluster = load_environment(name)
    if cluster.valid:
        ssh = Ssh(deployment, cluster)
        openshifter.instances.post_install(ssh, deployment)
    else:
        logging.error("Cluster is not valid. Did you provision it?")


@click.command()
@click.argument('name')
@click.pass_context
def create(ctx, name):
    """Provision + Install + Setup"""
    ctx.forward(provision)
    ctx.forward(install)
    ctx.forward(setup)


@click.command()
@click.argument('name')
def destroy(name):
    """Destroy infrastructure"""
    deployment, infrastructure, cluster = load_environment(name)
    infrastructure.destroy()
    driver = dns.find(deployment)
    driver.destroy(cluster)

cli.add_command(provision)
cli.add_command(install)
cli.add_command(setup)
cli.add_command(create)
cli.add_command(destroy)
