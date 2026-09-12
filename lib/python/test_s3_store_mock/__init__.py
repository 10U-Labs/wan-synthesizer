from types import SimpleNamespace
from typing import Any


class NoSuchKey(Exception):
    pass


_NULL_VERSION = "null"


def fake_s3(objects: dict[str, bytes], keys: list[str] | None = None) -> Any:
    markers: set[str] = set()

    def _listed(prefix: str) -> list[str]:
        listed = keys if keys is not None else list(objects)
        return [key for key in listed if key.startswith(prefix)]

    def _as_null_version(key: str) -> dict[str, Any]:
        return {"Key": key, "VersionId": _NULL_VERSION, "IsLatest": True}

    def get_object(**kwargs: Any) -> dict[str, Any]:
        key = kwargs["Key"]
        if key not in objects:
            raise NoSuchKey()
        return {"Body": SimpleNamespace(read=lambda: objects[key])}

    def put_object(**kwargs: Any) -> dict[str, Any]:
        objects[kwargs["Key"]] = kwargs["Body"]
        markers.discard(kwargs["Key"])
        return {}

    def delete_object(**kwargs: Any) -> dict[str, Any]:
        key = kwargs["Key"]
        objects.pop(key, None)
        if kwargs.get("VersionId") == _NULL_VERSION:
            markers.discard(key)
        else:
            markers.add(key)
        return {}

    def list_objects_v2(**kwargs: Any) -> dict[str, Any]:
        return {"Contents": [{"Key": key} for key in _listed(kwargs.get("Prefix", ""))]}

    def list_object_versions(**kwargs: Any) -> dict[str, Any]:
        prefix = kwargs.get("Prefix", "")
        return {
            "Versions": [_as_null_version(key) for key in _listed(prefix)],
            "DeleteMarkers": [
                _as_null_version(key) for key in sorted(markers) if key.startswith(prefix)
            ],
        }

    listings = {
        "list_objects_v2": list_objects_v2,
        "list_object_versions": list_object_versions,
    }

    def get_paginator(name: str) -> Any:
        return SimpleNamespace(paginate=lambda **kwargs: iter([listings[name](**kwargs)]))

    return SimpleNamespace(
        get_object=get_object,
        put_object=put_object,
        delete_object=delete_object,
        list_objects_v2=list_objects_v2,
        list_object_versions=list_object_versions,
        get_paginator=get_paginator,
        exceptions=SimpleNamespace(NoSuchKey=NoSuchKey),
    )


def fake_lambda(invocations: list[dict[str, Any]]) -> Any:
    def invoke(**kwargs: Any) -> dict[str, Any]:
        invocations.append(kwargs)
        return {"StatusCode": 202}

    return SimpleNamespace(invoke=invoke)
