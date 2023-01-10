def cleaner(items: list):
    for item in items:
        if "_id" in item:
            del item["_id"]

    return items
