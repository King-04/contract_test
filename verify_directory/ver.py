import os
from flask import Flask, render_template, request
from dotenv import load_dotenv
from pycardano import Address, TransactionBuilder, UTxO, PlutusV2Script, plutus_script_hash, Redeemer, \
    VerificationKeyHash, RawPlutusData, RawCBOR, BlockFrostChainContext, Transaction, TransactionWitnessSet
from src.utils import get_address, get_signing_info, network, get_chain_context
from src.week03.lecture.certificate import VestingParams, validate_secret
from src.week03 import assets_dir, lecture_dir

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Retrieve BLOCKFROST_ID from environment variables
block_forst_project_id = os.getenv("BLOCKFROST_PROJECT_ID")

# Use BlockFrostChainContext for simplicity.
chain_context = BlockFrostChainContext(block_forst_project_id, base_url="https://cardano-preview.blockfrost.io/api")


def build_transaction(data):
    context = get_chain_context()

    try:
        sender_address = Address.from_primitive(bytes.fromhex(data["sender"]))
        change_address = Address.from_primitive(bytes.fromhex(data["change_address"]))
        # recipient_address = Address.from_primitive(data["recipient"][0])
        secret = str(data["recipient"][1])

        script_path = assets_dir.joinpath("certificate", "script.cbor")

        with open(script_path) as f:
            cbor_hex = f.read()

        cbor = bytes.fromhex(cbor_hex)
        plutus_script = PlutusV2Script(cbor)
        script_hash = plutus_script_hash(plutus_script)
        script_address = Address(script_hash, network=network)

        print(f"Sender address: {sender_address}")
        print(f"cbor_hex: {cbor_hex}")
        print(f"Secret: {secret}")
        print(f"Change address: {change_address}")

        # utxo_to_spend = None
        reference_utxo = None
        for utxo in context.utxos(script_address):
            if utxo.output.datum:
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
        utxos = context.utxos(sender_address)
        for utxo in utxos:
            builder.add_input(utxo)  # Add UTxOs to the builder to cover transaction fees

        # Set the required signers
        vkey_hash: VerificationKeyHash = sender_address.payment_part
        builder.required_signers = [vkey_hash]

        # Set the validity range and time-to-live (TTL) for the transaction
        builder.validity_start = context.last_block_slot
        num_slots = 60 * 60 // context.genesis_param.slot_length
        builder.ttl = builder.validity_start + num_slots

        tx_body = builder.build(change_address=change_address)
        tx = Transaction(tx_body, TransactionWitnessSet())

        return tx
    except Exception as e:
        print(f"Error in build_transaction: {e}")
        raise e


def compose_tx_and_witness(data):
    try:
        tx = Transaction.from_cbor(bytes.fromhex(data["tx"]))
        witness = TransactionWitnessSet.from_cbor(bytes.fromhex(data["witness"]))
        tx.transaction_witness_set = witness
        return tx
    except Exception as e:
        print(f"Error in compose_tx_and_witness: {e}")
        raise e


@app.route("/")
def home_page():
    return render_template("index.html")


@app.route("/build_tx", methods=["POST"])
def build_tx():
    try:
        tx = build_transaction(request.json)
        cbor_hex = tx.to_cbor().hex()  # Convert bytes to hex string
        print(f"Transaction CBOR (hex): {cbor_hex}")
        return {"tx": cbor_hex}
    except Exception as e:
        print(f"Error building transaction: {e}")
        return {"error": str(e)}, 500


@app.route("/submit_tx", methods=["POST"])
def submit_tx():
    tx = compose_tx_and_witness(request.json)
    tx_id = tx.transaction_body.hash().hex()
    print(f"Transaction: \n {tx}")
    print(f"Transaction cbor: {tx.to_cbor()}")
    print(f"Transaction ID: {tx_id}")
    chain_context.submit_tx(tx.to_cbor())
    return {"tx_id": tx_id}


if __name__ == "__main__":
    app.run(debug=True)
