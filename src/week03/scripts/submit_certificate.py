import subprocess

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
from src.week03.lecture.certificate import VestingParams


@click.command()
@click.argument("name")
@click.argument("secret")  # Added secret string as an argument
@click.option("--amount", type=int, default=3000000, help="Amount of lovelace to send to the script address.")
@click.option("--parameterized", is_flag=True, help="If set, use parameterized vesting script.")
def main(name: str, secret: str, amount: int, parameterized: bool):
    context = get_chain_context()
    payment_address = get_address(name)
    # beneficiary_address = get_address(beneficiary)
    # vkey_hash: VerificationKeyHash = beneficiary_address.payment_part

    params = VestingParams(
        # beneficiary=bytes(vkey_hash),
        secret=secret.encode('utf-8')  # Store the secret as bytes
    )

    if parameterized:
        save_path = assets_dir.joinpath(f"parameterized_vesting_{name}")
        script_path = lecture_dir.joinpath("parameterized_vesting.py")
        subprocess.run(
            ["opshin", "-o", str(save_path), "build", "spending", str(script_path), params.to_json()],
            check=True,
        )
        script_path = save_path.joinpath("testnet.addr")
    else:
        script_path = assets_dir.joinpath("certificate", "testnet.addr")

    with open(script_path) as f:
        script_address = Address.from_primitive(f.read())

    if parameterized:
        datum = PlutusData()
    else:
        datum = params

    builder = TransactionBuilder(context)
    builder.add_input_address(payment_address)
    builder.add_output(TransactionOutput(address=script_address, amount=amount, datum=datum))

    payment_vkey, payment_skey, payment_address = get_signing_info(name)
    signed_tx = builder.build_and_sign(signing_keys=[payment_skey], change_address=payment_address)
    context.submit_tx(signed_tx)

    print(f"transaction id: {signed_tx.id}")
    print(f"Cardanoscan: https://preview.cexplorer.io/tx/{signed_tx.id}")


if __name__ == "__main__":
    main()
