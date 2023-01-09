"""Configuration tool for InfraSonar probes.

Example yaml configuration:


exampleProbe:
  config:
    username: alice
    password: secret_password
  assets:
    - id: 123
      config:
        username: bob
        password: "my secret"
    - id: [456, 789]
      config:
        username: charlie
        password: "my other secret"
"""
from typing import Optional
import logging


def encrypt(layer, fernet) -> bool:
    changed = False
    for k, v in layer.items():
        if k in ('secret', 'password') and isinstance(v, str):
            layer[k] = {"encrypted": fernet.encrypt(str.encode(v))}
            changed = True
        elif isinstance(v, (list, tuple)):
            for item in v:
                if isinstance(item, dict):
                    changed = encrypt(item, fernet) or changed
        elif isinstance(v, dict):
            changed = encrypt(v, fernet) or changed
    return changed


def decrypt(layer, fernet):
    for k, v in layer.items():
        if k in ('secret', 'password') and isinstance(v, dict):
            ecrypted = v.get("encrypted")
            if ecrypted and isinstance(ecrypted, bytes):
                layer[k] = fernet.decrypt(ecrypted).decode()
        elif isinstance(v, (list, tuple)):
            for item in v:
                if isinstance(item, dict):
                    decrypt(item, fernet)
        elif isinstance(v, dict):
            decrypt(v, fernet)


def get_config(conf: dict, probe_name: str, asset_id: int, use: Optional[str]):
    # use might both be None or an empty string, depending if the `_use` option
    # is available for the probe; both must be ignored
    probe = conf.get(use or probe_name)

    if not isinstance(probe, dict):
        if use:
            logging.warning(
                f'probe config `{use}` is '
                'explicitly configured but is not found')
        return {}

    use = probe.get('use')
    if isinstance(use, str):
        return get_config(conf, use, asset_id, None)

    assets = probe.get('assets')
    if assets:
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            # id can be either a single id or a list of ids
            _asset_id = asset.get('id')
            if _asset_id == asset_id or \
                    (isinstance(_asset_id, list) and asset_id in _asset_id):
                config = asset.get('config')
                return config if isinstance(config, dict) else {}

    config = probe.get('config')
    return config if isinstance(config, dict) else {}
