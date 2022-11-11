import logging
import time
from typing import Callable
from .net.package import Package
from .net.protocol import Protocol


class AgentcoreProtocol(Protocol):

    PROTO_FAF_DUMP = 0x00

    PROTO_REQ_ANNOUNCE = 0x01

    PROTO_FAF_SET_ASSETS = 0x02  # Overwites all assets

    PROTO_REQ_INFO = 0x03

    PROTO_FAF_UPSERT_ASSET = 0x04  # Overwite/Add a single asset

    PROTO_FAF_UNSET_ASSETS = 0x05  # Remove given assets

    PROTO_RES_ANNOUNCE = 0x81

    PROTO_RES_INFO = 0x82

    def __init__(
        self,
        on_set_assets: Callable,
        on_unset_assets: Callable,
        on_upsert_asset: Callable,
    ):
        super().__init__()
        self._on_set_assets = on_set_assets
        self._on_unset_assets = on_unset_assets
        self._on_upsert_asset = on_upsert_asset

    def _on_res_announce(self, pkg: Package):
        logging.debug(f"on announce; data size: {len(pkg.data)}")
        self._on_set_assets(pkg.data)

        future = self._get_future(pkg)
        if future is None:
            return
        future.set_result(pkg.data)

    def _on_faf_set_assets(self, pkg: Package):
        logging.debug(f"on set assets; data size: {len(pkg.data)}")
        self._on_set_assets(pkg.data)

    def _on_req_info(self, pkg: Package):
        logging.debug(f"on heartbeat; data size: {len(pkg.data)}")

        resp_pkg = Package.make(
            AgentcoreProtocol.PROTO_RES_INFO,
            pid=pkg.pid,
            data=time.time()
        )
        self.transport.write(resp_pkg.to_bytes())

    def _on_faf_upsert_asset(self, pkg: Package):
        logging.debug(f"on upsert asset; data size: {len(pkg.data)}")
        self._on_upsert_asset(pkg.data)

    def _on_faf_unset_assets(self, pkg: Package):
        logging.debug(f"on unset assets; data size: {len(pkg.data)}")
        self._on_unset_assets(pkg.data)

    def on_package_received(self, pkg: Package, _map={
        PROTO_RES_ANNOUNCE: _on_res_announce,
        PROTO_FAF_SET_ASSETS: _on_faf_set_assets,
        PROTO_REQ_INFO: _on_req_info,
        PROTO_FAF_UPSERT_ASSET: _on_faf_upsert_asset,
        PROTO_FAF_UNSET_ASSETS: _on_faf_unset_assets,
    }):
        handle = _map.get(pkg.tp)
        if handle is None:
            logging.error(f'unhandled package type: {pkg.tp}')
        else:
            handle(self, pkg)
