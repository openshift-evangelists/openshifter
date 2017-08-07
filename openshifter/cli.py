import click

from openshifter import OpenShifter

openshifter = OpenShifter()


@click.group()
def cli():
    pass


@click.command()
def web():
    import web


@click.command()
@click.argument('name')
def provision(name):
    """Provision infrastructure"""
    openshifter.load(name)
    openshifter.provision()


@click.command()
@click.argument('name')
def install(name):
    """Install OpenShift on infrastructure"""
    openshifter.load(name)
    openshifter.install()

@click.command()
@click.argument('name')
def setup(name):
    """Run post-installation setup"""
    openshifter.load(name)
    openshifter.setup()


@click.command()
@click.argument('name')
@click.pass_context
def create(ctx, name):
    """Provision + Install + Setup"""
    openshifter.load(name)
    openshifter.create()


@click.command()
@click.argument('name')
def destroy(name):
    """Destroy infrastructure"""
    openshifter.load(name)
    openshifter.destroy()

cli.add_command(web)
cli.add_command(provision)
cli.add_command(install)
cli.add_command(setup)
cli.add_command(create)
cli.add_command(destroy)
