"""Configuration tool for InfraSonar probes.

Example yaml configuration:


exampleProbe:
  config:
    username: alice
    password: secret_password
  assets:
    - id: 12345
      config:
        username: bob
        password: "my secret"
"""


def encrypt(layer, fernet):
    for k, v in layer.items():
        if k in ('secret', 'password') and isinstance(v, str):
            layer[k] = {"encrypted": fernet.encrypt(str.encode(v))}
        elif isinstance(v, (list, tuple)):
            for item in v:
                if isinstance(item, dict):
                    encrypt(item, fernet)
        elif isinstance(v, dict):
            encrypt(v, fernet)


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


def get_config(conf: dict, probe_name: str, asset_id):
    probe = conf.get(probe_name)
    if not isinstance(probe, dict):
        return {}

    assets = probe.get('assets')
    if assets:
        for asset in assets:
            if isinstance(asset, dict) and asset.get('id') == asset_id:
                config = asset.get('config')
                return config if isinstance(config, dict) else {}

    config = probe.get('config')
    return config if isinstance(config, dict) else {}
