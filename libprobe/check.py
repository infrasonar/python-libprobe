import abc
from .asset import Asset


class Check(abc.ABC):
    key: str  # Check key
    unchanged_eol: int = 0  # For example: 14400 for 4 hours, 0 for disabled

    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, 'key'):
            raise NotImplementedError('key not implemented')
        if not isinstance(cls.key, str):
            raise NotImplementedError('key must be type str')
        return super().__init_subclass__(**kwargs)

    # Method run(..) must return a check result, it receives:
    #   asset: Asset
    #   local_config: Local configuration (credentials etc.)
    #   config: Asset configuration from InfraSonar
    @staticmethod
    @abc.abstractmethod
    async def run(asset: Asset, local_config: dict, config: dict) -> dict:
        ...
