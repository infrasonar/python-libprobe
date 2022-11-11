[![CI](https://github.com/infrasonar/python-libprobe/workflows/CI/badge.svg)](https://github.com/infrasonar/python-libprobe/actions)
[![Release Version](https://img.shields.io/github/release/infrasonar/python-libprobe)](https://github.com/infrasonar/python-libprobe/releases)

# Python library for building InfraSonar Probes

This library is created for building [InfraSonar](https://infrasonar.com) probes.

## Environment variable

Variable         | Default                       | Description
---------------- | ----------------------------- | ------------
`AGENTCORE_HOST` | `127.0.0.1`                   | Hostname or Ip address of the AgentCore.
`AGENTCORE_PORT` | `8750`                        | AgentCore port to connect to.
`INFRASONAR_CONF` | `/data/config/infrasonar.yaml` | File with probe and asset configuration like credentials.
`LOG_LEVEL`      | `warning`                     | Log level (`debug`, `info`, `warning`, `error` or `critical`).
`LOG_COLORIZED`  | `0`                           | Log using colors (`0`=disabled, `1`=enabled).
`LOG_FTM`        | `%y%m%d %H:%M:%S`             | Log format prefix.


## Usage

Building an InfraSonar.

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

    result = {"myType": {"myItem": {"myMetric": "some value"}}}

    if "result_is_incomplete":
        # optionally, IncompleteResultException can be given another severity;
        # the default severity is LOW.
        raise IncompleteResultException('missing type x', result)

    # Use the asset in logging; this will include asset info and the check name
    logging.info(f"log something; {asset}")

    # A check result may have multiple types, items, and/or metrics
    return {"myType": {"myItem": {"myMetric": "some value"}}}


if __name__ == "__main__":
    checks = {
        "myFirstCheck": my_first_check,
    }

    # Initialize the probe with a name, version and checks
    probe = Probe("myProbe", __version__, checks)

    # Start the probe
    probe.start()
```
