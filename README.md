[![CI](https://github.com/infrasonar/python-libprobe/workflows/CI/badge.svg)](https://github.com/infrasonar/python-libprobe/actions)
[![Release Version](https://img.shields.io/github/release/infrasonar/python-libprobe)](https://github.com/infrasonar/python-libprobe/releases)

# Python library for building InfraSonar Probes

This library is created for building [InfraSonar](https://infrasonar.com) probes.

## Environment variable

Variable            | Default                        | Description
------------------- | ------------------------------ | ------------
`AGENTCORE_HOST`    | `127.0.0.1`                    | Hostname or Ip address of the AgentCore.
`AGENTCORE_PORT`    | `8750`                         | AgentCore port to connect to.
`ENCRYPTION_KEY`    | _default_                      | Use your own encryption key for encrypting secrets in the YAML file.
`INFRASONAR_CONF`   | `/data/config/infrasonar.yaml` | File with probe and asset configuration like credentials.
`MAX_PACKAGE_SIZE`  | `500`                          | Maximum package size in kilobytes _(1..2000)_.
`MAX_CHECK_TIMEOUT` | `300`                          | Check time-out is 80% of the interval time with `MAX_CHECK_TIMEOUT` in seconds as absolute maximum.
`DRY_RUN`           | _none_                         | Do not run demonized, just return checks and assets specified in the given yaml _(see the [Dry run section](#dry-run) below)_.
`LOG_LEVEL`         | `warning`                      | Log level (`debug`, `info`, `warning`, `error` or `critical`).
`LOG_COLORIZED`     | `0`                            | Log using colors (`0`=disabled, `1`=enabled).
`LOG_FTM`           | `%y%m%d %H:%M:%S`              | Log format prefix.

## Usage

Building an InfraSonar.get_state

```python
import logging
from libprobe.asset import Asset
from libprobe.probe import Probe
from libprobe.severity import Severity
from libprobe.exceptions import (
    CheckException,
    IgnoreResultException,
    IgnoreCheckException,
    IncompleteResultException,
    NoCountException,
)

__version__ = "0.1.0"


async def my_first_check(asset: Asset, asset_config: dict, check_config: dict):
    """My first check.
    Arguments:
      asset:        Asset contains an id, name and check which should be used
                    for logging;
      asset_config: local configuration for this asset, for example credentials;
      check_config: configuration for this check; contains for example the
                    interval at which the check is running and an address of
                    the asset to probe;
    """
    if "ignore_this_check_iteration":
        # nothing will be send to InfraSonar for this check iteration;
        raise IgnoreResultException()

    if "no_longer_try_this_check":
        # nothing will be send to InfraSonar for this check iteration and the
        # check will not start again until the probe restarts or configuration
        # has been changed;
        raise IgnoreCheckException()

    if "something_has_happened":
        # send a check error to InfraSonar because something has happened which
        # prevents us from building a check result; The default severity for a
        # CheckException is MEDIUM but this can be overwritten;
        raise CheckException("something went wrong", severity=Severity.LOW)

    if "something_unexpected_has_happened":
        # other exceptions will be converted to CheckException, MEDIUM severity
        raise Exception("something went wrong")

    # A check result may have multiple types, items, and/or metrics
    result = {"myType": [{"name": "my item"}]}

    if "result_is_incomplete":
        # optionally, IncompleteResultException can be given another severity;
        # the default severity is LOW.
        raise IncompleteResultException('missing type x', result)

    if "not_count_as_check_result":
        # optionally, NoCountException can be raised in which case the check
        # result is not counted by InfraSonar; Thus, the last seen services
        # will not "see" this check result.
        # A severity can be given if we also want a check error; (similar to
        # the IncompleteResultException exception)
        raise NoCountException('do not count this check result', result)

    # Use the asset in logging; this will include asset info and the check key
    logging.info(f"log something; {asset}")

    # Return the check result
    return result


if __name__ == "__main__":
    checks = {
        "myFirstCheck": my_first_check,
    }

    # Initialize the probe with a name, version and checks
    probe = Probe("myProbe", __version__, checks)

    # Start the probe
    probe.start()
```

## ASCII item names

InfraSonar requires each item to have a unique _name_ property. The value for _name_ must be a _string_ with ASCII compatible character.
When your _name_ is not guaranteed to be ASCII compatible, the following code replaces the incompatible characters with question marks (`?`):

```python
name = name.encode('ascii', errors='replace').decode()
```

## Config

When using a `password` or `secret` within a _config_ section, the library
will encrypt the value so it will be unreadable by users. This must not be
regarded as true encryption as the encryption key is publicly available.

Example yaml configuration:

```yaml
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
otherProbe:
  use: exampleProbe  # use the exampleProbe config for this probe
```

## Dry run

Create a yaml file, for example _(test.yaml)_:

```yaml
asset:
  name: "foo.local"
  check: "system"
  config:
    address: "192.168.1.2"
```

Run the probe with the `DRY_RUN` environment variable set the the yaml file above.

```
DRY_RUN=test.yaml python main.py
```

> Note: Optionally an asset _id_ might be given which can by used to find asset configuration in the local asset configuration file. Asset _config_ is also optional.

### Dump to JSON
A dry run writes all log to _stderr_ and only the JSON dump is written to _stdout_. Therefore, writing the output to JSON is easy:
```
DRY_RUN=test.yaml python main.py > dump.json
```
