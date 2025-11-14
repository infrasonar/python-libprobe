def _item_name(item: dict) -> str:
    return item['name'

                ]
def order(result: dict) -> dict:
    """Return the result ordered by items name."""
    for items in result.values():
        items.sort(key=_item_name)
    return result
