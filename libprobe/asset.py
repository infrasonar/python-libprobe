from typing import NamedTuple


class Asset(NamedTuple):
    id: int
    name: str
    check: str

    def __repr__(self) -> str:
        return f"asset: {self.name} ({self.id}) check: {self.check}"


if __name__ == "__main__":
    asset = Asset(123, 'test', 'myCheck')
    assert str(asset) == 'asset: test (123) check: myCheck'
