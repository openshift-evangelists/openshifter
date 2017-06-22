import provider.gce

DRIVERS = {
    "gce": gce.Gce
}


def find(deployment):
    return DRIVERS[deployment['provider']](deployment)
