def _item_name(item: dict) -> str:
    return item['name']


def order(result: dict):
    """Order result items by item name."""
    for items in result.values():
        items.sort(key=_item_name)
