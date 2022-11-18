import asyncio
import logging
import os
import random
import signal
import time
import yaml
from cryptography.fernet import Fernet
from pathlib import Path
from setproctitle import setproctitle
from typing import Optional, Dict, Tuple, Callable
from .exceptions import (
    CheckException,
    IgnoreResultException,
    IgnoreCheckException,
    IncompleteResultException,
)
from .logger import setup_logger
from .net.package import Package
from .protocol import AgentcoreProtocol
from .asset import Asset
from .severity import Severity
from .config import encrypt, decrypt, get_config

HEADER_FILE = """
# WARNING: InfraSonar will make `password` and `secret` values unreadable but
# this must not be regarded as true encryption as the encryption key is
# publically available.
#
# Example configuration for `myprobe` collector:
#
#  myprobe:
#    config:
#      username: alice
#      password: "secret password"
#    assets:
#      - id: 12345
#        config:
#          username: bob
#          password: "my secret"
""".lstrip()

AGENTCORE_HOST = os.getenv('AGENTCORE_HOST', '127.0.0.1')
AGENTCORE_PORT = int(os.getenv('AGENTCORE_PORT', 8750))
INFRASONAR_CONF_FN = \
    os.getenv('INFRASONAR_CONF', '/data/config/infrasonar.yaml')

# Index in path
ASSET_ID, CHECK_ID = range(2)

# Index in names
ASSET_NAME_IDX, CHECK_NAME_IDX = range(2)

# This is the InfraSonar encryption key used for local configuration files.
# Note that this is not intended as a real security measure but prevents users
# from reading a passwords directly from open configuration files.
FERNET = Fernet(b"4DFfx9LZBPvwvCpwmsVGT_HzjgiGUHduP1kq_L2Fbjw=")


class Probe:
    """This class should only be initialized once."""

    def __init__(
        self,
        name: str,
        version: str,
        checks: Dict[str, Callable[[Asset, dict, dict], dict]],
        config_path: Optional[str] = INFRASONAR_CONF_FN
    ):
        setproctitle(name)
        setup_logger()
        logging.warning(f'starting probe collector: {name} v{version}')
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.name: str = name
        self.version: str = version
        self._checks_funs: Dict[
            str,
            Callable[[Asset, dict, dict], dict]] = checks
        self._config_path: Path = Path(config_path)
        self._connecting: bool = False
        self._protocol: Optional[AgentcoreProtocol] = None
        self._retry_next: int = 0
        self._retry_step: int = 1
        self._local_config: Optional[dict] = None
        self._local_config_mtime: Optional[float] = None
        self._checks_config: Dict[
            Tuple[int, int],
            Tuple[Tuple[str, str], dict]] = {}
        self._checks: Dict[Tuple[int, int], asyncio.Future] = {}

        if not os.path.exists(config_path):
            try:
                parent = os.path.dirname(config_path)
                if not os.path.exists(parent):
                    os.mkdir(parent)
                with open(self._config_path, 'w') as file:
                    file.write(HEADER_FILE)
            except Exception:
                logging.exception(f"cannot write file: {config_path}")
                exit(1)
            logging.warning(f"created a new configuration file: {config_path}")
        try:
            self._read_local_config()
        except Exception:
            logging.exception(f"configuration file invalid: {config_path}")
            exit(1)

    def is_connected(self) -> bool:
        return self._protocol is not None and self._protocol.is_connected()

    def is_connecting(self) -> bool:
        return self._connecting

    def _stop(self, signame, *args):
        logging.warning(
            f'signal \'{signame}\' received, stop {self.name} probe')
        for task in asyncio.all_tasks():
            task.cancel()

    async def _start(self):
        initial_step = 2
        step = 2
        max_step = 2 ** 7

        while True:
            if not self.is_connected() and not self.is_connecting():
                asyncio.ensure_future(self._connect())
                step = min(step * 2, max_step)
            else:
                step = initial_step
            for _ in range(step):
                await asyncio.sleep(1)

    def start(self):
        signal.signal(signal.SIGINT, self._stop)
        signal.signal(signal.SIGTERM, self._stop)

        self.loop = asyncio.get_event_loop()
        try:
            self.loop.run_until_complete(self._start())
        except asyncio.exceptions.CancelledError:
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    async def _connect(self):
        conn = self.loop.create_connection(
            lambda: AgentcoreProtocol(
                self._on_set_assets,
                self._on_unset_assets,
                self._on_upsert_asset,
            ),
            host=AGENTCORE_HOST,
            port=AGENTCORE_PORT
        )
        self._connecting = True

        try:
            _, self._protocol = await asyncio.wait_for(conn, timeout=10)
        except Exception as e:
            error_msg = str(e) or type(e).__name__
            logging.error(f'connecting to agentcore failed: {error_msg}')
        else:
            pkg = Package.make(
                AgentcoreProtocol.PROTO_REQ_ANNOUNCE,
                data=[self.name, self.version]
            )
            if self._protocol and self._protocol.transport:
                try:
                    await self._protocol.request(pkg, timeout=10)
                except Exception as e:
                    logging.error(e)
        finally:
            self._connecting = False

    def send(
            self,
            path: tuple,
            result: Optional[dict],
            error: Optional[dict],
            ts: float):
        assert (result is None) ^ (error is None)
        asset_id, _ = path
        check_data = {
            'result': result,
            'error': error,
            'framework': {
                'duration': time.time() - ts,
                'timestamp': ts,
            }
        }
        pkg = Package.make(
            AgentcoreProtocol.PROTO_FAF_DUMP,
            partid=asset_id,
            data=[path, check_data]
        )

        if self._protocol and self._protocol.transport:
            self._protocol.transport.write(pkg.to_bytes())

    def close(self):
        if self._protocol and self._protocol.transport:
            self._protocol.transport.close()
        self._protocol = None

    def _read_local_config(self):
        if self._config_path.stat().st_mtime == self._local_config_mtime:
            return

        with open(self._config_path, 'r') as file:
            config = yaml.safe_load(file)

        if config:
            # First encrypt everything
            encrypt(config, FERNET)

            # Re-write the file
            with open(self._config_path, 'w') as file:
                file.write(HEADER_FILE)
                file.write(yaml.dump(config))

            # Now decrypt everything so we can use the configuration
            decrypt(config, FERNET)
        else:
            config = {}

        self._local_config_mtime = self._config_path.stat().st_mtime
        self._local_config = config

    def _asset_config(self, asset_id: int) -> dict:
        try:
            self._read_local_config()
        except Exception:
            logging.warning('new config file invalid, keep using previous')

        return get_config(self._local_config, self.name, asset_id)

    def _on_unset_assets(self, asset_ids: list):
        asset_ids = set(asset_ids)
        new_checks_config = {
            path: config
            for path, config in self._checks_config.items()
            if path[ASSET_ID] not in asset_ids}
        self._set_new_checks_config(new_checks_config)

    def _on_upsert_asset(self, asset: list):
        asset_id, checks = asset
        new_checks_config = {
            path: config
            for path, config in self._checks_config.items()
            if path[ASSET_ID] != asset_id}
        new = {
            tuple(path): (names, config)
            for path, names, config in checks
            if names[CHECK_NAME_IDX] in self._checks_funs}
        new_checks_config.update(new)
        self._set_new_checks_config(new_checks_config)

    def _on_set_assets(self, assets: list):
        new_checks_config = {
            tuple(path): (names, config)
            for path, names, config in assets
            if names[CHECK_NAME_IDX] in self._checks_funs}
        self._set_new_checks_config(new_checks_config)

    def _set_new_checks_config(self, new_checks_config: dict):
        desired_checks = set(new_checks_config)

        for path in set(self._checks):
            if path not in desired_checks:
                # the check is no longer required, pop and cancel the task
                self._checks.pop(path).cancel()
            elif new_checks_config[path] != self._checks_config[path] and \
                    self._checks[path].cancelled():
                # this task is desired but has previously been cancelled;
                # now the config has been changed so we want to re-scheduled.
                del self._checks[path]

        # overwite check_config
        self._checks_config = new_checks_config

        # start new checks
        for path in desired_checks - set(self._checks):
            self._checks[path] = asyncio.ensure_future(
                self._run_check_loop(path)
            )

    async def _run_check_loop(self, path: tuple):
        asset_id, _ = path
        (asset_name, check_name), config = self._checks_config[path]
        interval = config.get('_interval')
        fun = self._checks_funs[check_name]
        asset = Asset(asset_id, asset_name, check_name)

        my_task = self._checks[path]

        assert isinstance(interval, int) and interval > 0

        ts = time.time()
        ts_next = int(ts + random.random() * interval) + 1

        while True:
            assert ts < ts_next

            try:
                await asyncio.sleep(ts_next - ts)
            except asyncio.CancelledError:
                logging.info(f'cancelled; {asset}')
                break
            ts = ts_next

            asset_config = self._asset_config(asset.id)
            (asset_name, _), config = self._checks_config[path]
            interval = config.get('_interval')
            timeout = 0.8 * interval
            if asset.name != asset_name:
                # asset_id and check_name are truly immutable, name is not
                asset = Asset(asset_id, asset_name, check_name)

            logging.debug(f'run check; {asset}')

            try:
                try:
                    res = await asyncio.wait_for(
                        fun(asset, asset_config, config), timeout=timeout)
                    if not isinstance(res, dict):
                        raise TypeError(
                            'expecting type `dict` as check result '
                            f'but got type `{type(res).__name__}`')
                except asyncio.TimeoutError:
                    raise CheckException('timed out')
                except asyncio.CancelledError:
                    if my_task is self._checks.get(path):
                        # cancelled from within, just raise
                        raise CheckException('cancelled')
                    logging.warning(f'cancelled; {asset}')
                    break
                except (IgnoreCheckException,
                        IgnoreResultException,
                        CheckException):
                    raise
                except Exception as e:
                    # fall-back to exception class name
                    error_msg = str(e) or type(e).__name__
                    raise CheckException(error_msg)

            except IgnoreResultException:
                logging.info(f'ignore result; {asset}')

            except IgnoreCheckException:
                # log as warning; the user is able to prevent this warning by
                # disabling the check if not relevant for the asset;
                logging.warning(f'ignore check; {asset}')
                break

            except IncompleteResultException as e:
                logging.warning(
                    'incomplete result; '
                    f'{asset} error: `{e}` severity: {e.severity}')
                self.send(path, e.result, e.to_dict(), ts)

            except CheckException as e:
                logging.error(
                    'check error; '
                    f'{asset} error: `{e}` severity: {e.severity}')
                self.send(path, None, e.to_dict(), ts)

            else:
                logging.debug(f'run check ok; {asset}')
                self.send(path, res, None, ts)

            ts = time.time()
            ts_next += interval
