"""Read, write and validate notebook handoff JSON (schemas/notebook-handoff.schema.json)."""
from __future__ import annotations
import datetime as _dt
import json
from pathlib import Path

from ._resources import path as _res
SCHEMA = _res("schemas", "notebook-handoff.schema.json")


def validate(record: dict) -> list[str]:
    try:
        import jsonschema
    except ImportError:  # minimal fallback
        req = json.loads(SCHEMA.read_text())["required"]
        return [f"missing {k}" for k in req if k not in record]
    v = jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text()))
    return [e.message for e in v.iter_errors(record)]


def make(producer: str, scenario_id: str, assumptions: list[str], placeholders: list[str], **fields) -> dict:
    from . import __version__
    rec = {"handoff_version": "0.1.0", "producer": producer,
           "created": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
           "scenario_id": scenario_id, "library_version": __version__,
           "assumptions": assumptions, "placeholders": placeholders, **fields}
    errs = validate(rec)
    if errs:
        raise ValueError("; ".join(errs))
    return rec


def write(record: dict, path: str | Path) -> Path:
    errs = validate(record)
    if errs:
        raise ValueError("; ".join(errs))
    p = Path(path)
    p.write_text(json.dumps(record, indent=2))
    return p


def read(path: str | Path) -> dict:
    rec = json.loads(Path(path).read_text())
    errs = validate(rec)
    if errs:
        raise ValueError("; ".join(errs))
    return rec
