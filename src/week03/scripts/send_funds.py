import subprocess
import time

import click
from pycardano import (
    Address,
    TransactionBuilder,
    TransactionOutput,
    VerificationKeyHash,
    PlutusData,
)

from src.utils import get_address, get_signing_info, get_chain_context
from src.week03 import assets_dir, lecture_dir



@click.command()
@click.argument("name")
@click.argument("beneficiary")
@click.option(
    "--amount",
    type=int,
    default=8000000,
    help="Amount of lovelace to send to the beneficiary address.",
)

def main(name: str, beneficiary: str, amount: int):
    # Load chain context
    context = get_chain_context()

    # Get payment address
    payment_address = get_address(name)

    # Get the beneficiary VerificationKeyHash (PubKeyHash)
    beneficiary_address = get_address(beneficiary)

    # Build the transaction
    builder = TransactionBuilder(context)
    builder.add_input_address(payment_address)
    builder.add_output(
        TransactionOutput(address=beneficiary_address, amount=amount)
    )

    # Sign the transaction
    payment_vkey, payment_skey, payment_address = get_signing_info(name)
    signed_tx = builder.build_and_sign(
        signing_keys=[payment_skey],
        change_address=payment_address,
    )

    # Submit the transaction
    context.submit_tx(signed_tx)

    print(f"transaction id: {signed_tx.id}")
    print(f"Cardanoscan: https://preview.cexplorer.io/tx/{signed_tx.id}")


if __name__ == "__main__":
    main()
