from dns.google import Google

PROVIDERS = {
    'gce': Google
}


def find(deployment):
    return PROVIDERS[deployment['dns']['provider']](deployment)