from opshin.ledger.interval import *
from dataclasses import dataclass
from typing import List


@dataclass()
class VestingParams(PlutusData):
    CONSTR_ID = 0
    secret: bytes  # Secret (hashed certificate) stored on-chain
    valid: bool  # Indicates whether the certificate is valid


@dataclass()
class MultisigDatum(PlutusData):
    CONSTR_ID = 1
    signatories: List[PubKeyHash]  # List of Admin Council members' public keys
    min_signatures: int  # Minimum number of signatures required for revocation


# Validate that the provided secret matches the stored secret
def validate_secret(stored_secret: bytes, provided_secret: bytes) -> bool:
    return stored_secret == provided_secret


# Certificate issuance function (certificate is marked valid by default)
def issue_certificate(datum: VestingParams, context: ScriptContext) -> None:
    assert not datum.valid, "Certificate already exists"
    datum.valid = True  # Mark the certificate as valid


# Certificate revocation function (requires multisig approval)
def revoke_certificate(datum: VestingParams, multisig_datum: MultisigDatum, context: ScriptContext) -> None:
    # Ensure the certificate is valid before revocation
    assert datum.valid, "Certificate is already revoked"

    # Collect signatures and check if the required number of signatories have approved
    approved_signatures = [signer for signer in multisig_datum.signatories if signer in context.tx_info.signatories]
    assert len(approved_signatures) >= multisig_datum.min_signatures, "Not enough signatures to revoke certificate"

    # Revoke the certificate
    datum.valid = False  # Mark the certificate as revoked


# Main validator function for both verification and revocation
def validator(datum: VestingParams, redeemer: PlutusData, context: ScriptContext) -> None:
    if isinstance(redeemer, bytes):  # Case 1: Verifying the certificate
        assert validate_secret(datum.secret, redeemer), "Secret does not match"
        assert datum.valid, "Certificate has been revoked"

    elif isinstance(redeemer, MultisigDatum):  # Case 2: Revoking the certificate
        revoke_certificate(datum, redeemer, context)
