from enum import StrEnum


class SSH_KEYS(StrEnum):
    # TODO: alternatively look into listing via `pydo.ssh_keys`
    # <https://docs.digitalocean.com/reference/pydo/reference/ssh_keys/>
    id_ed25519 = "c1:e9:aa:64:23:92:ae:e3:2b:60:74:f3:cb:73:18:d3"
