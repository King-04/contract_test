import os
from flask import Flask, render_template, request
from dotenv import load_dotenv
from pycardano import (
    Address,
    BlockFrostChainContext,
    Transaction,
    TransactionBuilder,
    TransactionOutput,
    TransactionWitnessSet,
)
from src.week03.lecture.certificate import VestingParams
from src.week03 import assets_dir, lecture_dir

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Retrieve BLOCKFROST_ID from environment variables
block_forst_project_id = os.getenv("BLOCKFROST_PROJECT_ID")

# Use BlockFrostChainContext for simplicity.
chain_context = BlockFrostChainContext(block_forst_project_id, base_url="https://cardano-preview.blockfrost.io/api")

AMOUNT_IN_ADA = 3  # Replace with the actual amount in ADA


def build_transaction(data):
    try:
        sender_address = Address.from_primitive(bytes.fromhex(data["sender"]))
        change_address = Address.from_primitive(bytes.fromhex(data["change_address"]))
        # recipient_address = Address.from_primitive(data["recipient"][0])
        # amount = int(data["recipient"][1]) * 1000000
        amount = AMOUNT_IN_ADA * 1000000  # Convert ADA to Lovelace

        script_path = assets_dir.joinpath("certificate", "testnet.addr")

        with open(script_path) as f:
            recipient_address = Address.from_primitive(f.read())

        # recipient_address = Address.from_primitive("addr_test1vzp9wsa4gm64tj4jqp89yt6cv5py6wjtrsmpz0efrhjtpfswpldp7")
        # amount = AMOUNT_IN_ADA * 1000000  # Convert ADA to Lovelace

        secret = 'key'
        params = VestingParams(
            secret=secret.encode('utf-8')  # Store the secret as bytes
        )

        print(f"Sender address: {sender_address}")
        print(f"Recipient address: {recipient_address}")
        print(f"Amount (Lovelace): {amount}")
        print(f"Change address: {change_address}")

        datum = params

        builder = TransactionBuilder(chain_context)
        builder.add_input_address(sender_address)
        builder.add_output(TransactionOutput(recipient_address, amount, datum=datum))

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
