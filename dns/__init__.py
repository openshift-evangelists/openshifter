from dns.google import Google
from dns.nip import Nip

PROVIDERS = {
    'gce': Google,
    'nip': Nip
}


def find(deployment):
    return PROVIDERS[deployment['dns']['provider']](deployment)