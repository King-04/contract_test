import os
from flask import Flask, request, render_template, jsonify, session
from datetime import datetime
import json
import hashlib
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

app.secret_key = os.getenv("SECRET_KEY")

# Retrieve BLOCKFROST_ID from environment variables
block_forst_project_id = os.getenv("BLOCKFROST_PROJECT_ID")

# Use BlockFrostChainContext for simplicity.
chain_context = BlockFrostChainContext(block_forst_project_id, base_url="https://cardano-preview.blockfrost.io/api")

AMOUNT_IN_ADA = 3  # Replace with the actual amount in ADA


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/create')
def create():
    return render_template('certificates/create.html')


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        recipient_id = request.form.get('recipient_id')
        matches = find_matches(recipient_id)
        return render_template('certificates/verify_result.html', recipient_id=recipient_id, matches=matches)
    return render_template('certificates/verify.html')


@app.route('/submit_form', methods=['POST'])
def submit_form():
    if request.method == 'POST':
        # Get form data
        certificate_name = request.form.get('certificate_name')
        certificate_description = request.form.get('certificate_description')
        issuer_information = request.form.get('issuer_information')
        recipient_name = request.form.get('recipient_name')
        recipient_id = request.form.get('recipient_id')
        validity_period = request.form.get('validity_period')
        tx_hash = request.form.get('tx_hash', None)

        # Generate hash from recipient_id and certificate_name
        entry_hash = generate_hash(recipient_id, certificate_name)

        # Store entry_hash in session
        session['entry_hash'] = entry_hash

        # Create a dictionary with the new form data
        new_data = {
            entry_hash: {
                "timestamp": datetime.now().isoformat(),
                "certificate_name": certificate_name,
                "certificate_description": certificate_description,
                "issuer_information": issuer_information,
                "recipient_name": recipient_name,
                "recipient_id": recipient_id,
                "validity_period": validity_period
            }
        }

        # Read existing data from the JSON file
        try:
            with open('form_submissions.json', 'r') as file:
                existing_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = {}

        # Update existing data with new data
        existing_data.update(new_data)

        # Write the updated data back to the JSON file
        with open('form_submissions.json', 'w') as file:
            json.dump(existing_data, file, indent=4)

        return jsonify({
            "message": "Form submitted successfully!",
            "details": {
                "certificate_name": certificate_name,
                "recipient_name": recipient_name,
                "recipient_id": recipient_id,
                'tx_hash': tx_hash,
            }
        }), 200


@app.route("/build_tx", methods=["POST"])
def build_tx():
    try:
        # Retrieve entry_hash from session
        entry_hash = session.get('entry_hash', None)
        if not entry_hash:
            raise ValueError("No entry_hash found in session.")

        tx = build_transaction(request.json, entry_hash)
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


def build_transaction(data, s_phrase):
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

        secret = s_phrase
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
        # builder.add_output(TransactionOutput(recipient_address, amount))

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


def find_matches(recipient_id):
    try:
        with open('form_submissions.json', 'r') as file:
            data = json.load(file)

        matches = []
        for entry_hash, entry_data in data.items():
            if entry_data['recipient_id'] == recipient_id:
                matches.append({
                    'entry_id': entry_hash,
                    'certificate_name': entry_data['certificate_name'],
                    'timestamp': entry_data['timestamp']
                })
        return matches
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def generate_hash(recipient_id, certificate_name):
    # Combine recipient_id and certificate_name
    data_to_hash = f"{recipient_id}|{certificate_name}"
    # Create SHA-256 hash
    return hashlib.sha256(data_to_hash.encode()).hexdigest()


if __name__ == '__main__':
    app.run(debug=True)
