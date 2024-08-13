import click
from pycardano import Address, TransactionBuilder, UTxO, PlutusV2Script, plutus_script_hash, Redeemer, \
    VerificationKeyHash, RawPlutusData, RawCBOR
from src.utils import get_address, get_signing_info, network, get_chain_context
from src.week03 import assets_dir
from src.week03.lecture.certificate import VestingParams, validate_secret


@click.command()
@click.argument("name")
@click.argument("secret")  # Added secret string as an argument
@click.option("--parameterized", is_flag=True, help="If set, use parameterized vesting script.")
def main(name: str, secret: str, parameterized: bool):
    context = get_chain_context()

    if parameterized:
        script_path = assets_dir.joinpath(f"parameterized_vesting_{name}", "script.cbor")
    else:
        script_path = assets_dir.joinpath("certificate", "script.cbor")
    with open(script_path) as f:
        cbor_hex = f.read()

    cbor = bytes.fromhex(cbor_hex)
    plutus_script = PlutusV2Script(cbor)
    script_hash = plutus_script_hash(plutus_script)
    script_address = Address(script_hash, network=network)

    payment_address = get_address(name)

    # utxo_to_spend = None
    reference_utxo = None
    for utxo in context.utxos(script_address):
        if utxo.output.datum:
            if parameterized:
                reference_utxo = utxo
                break
            else:
                if isinstance(utxo.output.datum, RawPlutusData):
                    try:
                        params = VestingParams.from_cbor(utxo.output.datum.to_cbor())
                    except Exception:
                        continue
                elif isinstance(utxo.output.datum, RawCBOR):
                    try:
                        params = VestingParams.from_cbor(utxo.output.datum.cbor)
                    except Exception:
                        continue
                elif isinstance(utxo.output.datum, VestingParams):
                    params = utxo.output.datum
                else:
                    continue
                # if (
                #         params.beneficiary == bytes(payment_address.payment_part)
                #         and validate_secret(params.secret, secret.encode('utf-8'))
                # ):
                #     utxo_to_spend = utxo
                #     break
                if validate_secret(params.secret, secret.encode('utf-8')):
                    reference_utxo = utxo
                    break

    assert isinstance(reference_utxo, UTxO), "No script UTxOs found!"

    # No need to consume any UTxO; just verify the secret string using the reference UTxO.
    # non_nft_utxo = None
    # for utxo in context.utxos(payment_address):
    #     if not utxo.output.amount.multi_asset and utxo.output.amount.coin >= 5000000:
    #         non_nft_utxo = utxo
    #         break
    # assert isinstance(non_nft_utxo, UTxO), "No collateral UTxOs found!"

    # redeemer = Redeemer(secret.encode('utf-8'))  # Pass the secret as the redeemer

    builder = TransactionBuilder(context)
    builder.reference_inputs.add(reference_utxo)  # Use the reference UTxO without consuming it
    # builder.add_script_input(utxo_to_spend, script=plutus_script, redeemer=redeemer)
    # builder.collaterals.append(non_nft_utxo)

    # Explicitly add UTxOs from the payment address to ensure sufficient funds
    utxos = context.utxos(payment_address)
    for utxo in utxos:
        builder.add_input(utxo)  # Add UTxOs to the builder to cover transaction fees

    # Set the required signers
    vkey_hash: VerificationKeyHash = payment_address.payment_part
    builder.required_signers = [vkey_hash]

    # Set the validity range and time-to-live (TTL) for the transaction
    builder.validity_start = context.last_block_slot
    num_slots = 60 * 60 // context.genesis_param.slot_length
    builder.ttl = builder.validity_start + num_slots

    # Sign and submit the transaction
    payment_vkey, payment_skey, payment_address = get_signing_info(name)
    signed_tx = builder.build_and_sign(signing_keys=[payment_skey], change_address=payment_address)
    context.submit_tx(signed_tx)

    print("Certificate is valid !!")
    print(f"transaction id: {signed_tx.id}")
    print(f"Cardanoscan: https://preview.cexplorer.io/tx/{signed_tx.id}")


if __name__ == "__main__":
    main()
