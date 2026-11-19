MAX_ITEM_NAME_LEN = 255


def _item_name(item: dict) -> str:
    return item['name']


def order(result: dict):
    """Order result items by item name."""
    for items in result.values():
        items.sort(key=_item_name)


def ensure_item_name(name: object = None, replace_char: str = '?') -> str:
    """Sanitize a value into a valid, non-empty printable ASCII item name.

    Use when `name` may be bytes, exceed `MAX_ITEM_NAME_LEN`,
    or contain non-ASCII or control characters.
    """
    if name is None:
        raw = ""
    elif isinstance(name, bytes):
        raw = name.decode("utf-8", errors="replace")
    else:
        raw = str(name)

    cleaned = "".join(
        ch if (ch.isascii() and ch.isprintable()) else replace_char
        for ch in raw
    ).strip()

    if len(cleaned) > MAX_ITEM_NAME_LEN:
        cleaned = cleaned[:MAX_ITEM_NAME_LEN].rstrip()

    if not cleaned:
        raise ValueError("empty name not allowed")

    return cleaned


def is_valid_item_name(name: object) -> bool:
    return (
        isinstance(name, str)
        and 0 < len(name) <= MAX_ITEM_NAME_LEN
        and name.isascii()
        and name.isprintable()
        and name.strip() == name
    )


def validate_check_result(res: object) -> None:
    if not isinstance(res, dict):
        raise TypeError(
            'expecting type `dict` as check result '
            f'but got type `{type(res).__name__}`')

    for type_name, items in res.items():
        if not is_valid_item_name(type_name):
            raise ValueError(
                f'invalid type name `{type_name!r}` in check result')

        if items is None:
            continue

        if not isinstance(items, list):
            raise TypeError(
                f'expecting type `list` for type `{type_name}` '
                f'but got type `{type(items).__name__}`')

        seen_names: set[str] = set()
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                raise TypeError(
                    f'expecting type `dict` for item {idx} in '
                    f'type `{type_name}` but got type `{type(item).__name__}`')

            if 'name' not in item:
                raise ValueError(
                    f'missing required `name` key for '
                    f'item {idx} in type `{type_name}`')

            name = item['name']
            if not is_valid_item_name(name):
                raise ValueError(
                    f'invalid item `name` {name!r} at index {idx} in '
                    f'type `{type_name}`')

            if name in seen_names:
                raise ValueError(
                    f'duplicate item `name` {name!r} in type `{type_name}`')
            seen_names.add(name)
