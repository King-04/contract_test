from opshin.ledger.interval import *

from dataclasses import dataclass


@dataclass()
class VestingParams(PlutusData):
    CONSTR_ID = 0
    beneficiary: PubKeyHash
    deadline: POSIXTime
    secret: bytes  # Added secret string as bytes


def signed_by_beneficiary(params: VestingParams, context: ScriptContext) -> bool:
    return params.beneficiary in context.tx_info.signatories


def is_after(deadline: POSIXTime, valid_range: POSIXTimeRange) -> bool:
    from_interval: POSIXTimeRange = make_from(deadline)
    return contains(from_interval, valid_range)


def deadline_reached(params: VestingParams, context: ScriptContext) -> bool:
    return is_after(params.deadline, context.tx_info.valid_range)


def validate_secret(stored_secret: bytes, provided_secret: bytes) -> bool:
    return stored_secret == provided_secret


def validator(datum: VestingParams, redeemer: bytes, context: ScriptContext) -> None:
    assert signed_by_beneficiary(datum, context), "Beneficiary's signature missing"
    assert deadline_reached(datum, context), "Deadline not reached"
    assert validate_secret(datum.secret, redeemer), "Secret does not match"
