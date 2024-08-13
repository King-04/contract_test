from opshin.ledger.interval import *

from dataclasses import dataclass


@dataclass()
class VestingParams(PlutusData):
    CONSTR_ID = 0
    secret: bytes  # Added secret string as bytes


def validate_secret(stored_secret: bytes, provided_secret: bytes) -> bool:
    return stored_secret == provided_secret


def validator(datum: VestingParams, redeemer: bytes, context: ScriptContext) -> None:
    assert validate_secret(datum.secret, redeemer), "Secret does not match"
