import provider.gce
from provider import byo

DRIVERS = {
    "gce": gce.Gce,
    "byo": byo.Byo
}


def find(deployment):
    return DRIVERS[deployment['provider']](deployment)
