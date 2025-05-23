import datetime

def convert_datetime(obj):
    if isinstance(obj, dict):
        return {k: convert_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime(item) for item in obj]
    elif isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%dT%H:%M:%S%z")
    else:
        return obj