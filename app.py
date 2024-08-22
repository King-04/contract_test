from flask import Flask, request, render_template, jsonify
from datetime import datetime
import json
import hashlib

from pycardano import (
    TransactionBuilder,
    TransactionOutput,
    Address,
    PlutusData,
    VerificationKeyHash,
)
from src.utils import get_chain_context
from src.week03.lecture.certificate import VestingParams

app = Flask(__name__)


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


# @app.route('/submit_form', methods=['POST'])
# def submit_form():
#     if request.method == 'POST':
#         # Get form data
#         certificate_name = request.form.get('certificate_name')
#         certificate_description = request.form.get('certificate_description')
#         issuer_information = request.form.get('issuer_information')
#         recipient_name = request.form.get('recipient_name')
#         recipient_id = request.form.get('recipient_id')
#         validity_period = request.form.get('validity_period')
#         tx_hash = request.form.get('tx_hash', None)
#
#         # Generate hash from recipient_id and certificate_name
#         entry_hash = generate_hash(recipient_id, certificate_name)
#
#         # Create a dictionary with the new form data
#         new_data = {
#             entry_hash: {
#                 "timestamp": datetime.now().isoformat(),
#                 "certificate_name": certificate_name,
#                 "certificate_description": certificate_description,
#                 "issuer_information": issuer_information,
#                 "recipient_name": recipient_name,
#                 "recipient_id": recipient_id,
#                 "validity_period": validity_period
#             }
#         }
#
#         # Read existing data from the JSON file
#         try:
#             with open('form_submissions.json', 'r') as file:
#                 existing_data = json.load(file)
#         except (FileNotFoundError, json.JSONDecodeError):
#             existing_data = {}
#
#         # Update existing data with new data
#         existing_data.update(new_data)
#
#         # Write the updated data back to the JSON file
#         with open('form_submissions.json', 'w') as file:
#             json.dump(existing_data, file, indent=4)
#
#         return jsonify({
#             "message": "Form submitted successfully!",
#             "details": {
#                 "certificate_name": certificate_name,
#                 "recipient_name": recipient_name,
#                 "recipient_id": recipient_id,
#                 'tx_hash': tx_hash,
#             }
#         }), 200
#


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

        # Generate hash from recipient_id and certificate_name
        entry_hash = generate_hash(recipient_id, certificate_name)

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
                "entry_hash": entry_hash
            }
        }), 200


@app.route('/prepare_transaction', methods=['POST'])
def prepare_transaction():
    try:
        # Step 1: Get the address and entry_hash (to be used as the datum) from the frontend
        address = request.form.get('address')
        entry_hash = request.form.get('entry_hash')

        if not address or not entry_hash:
            raise ValueError("Address or entry_hash is missing")

        # Log received data for debugging
        print(f"Received address: {address}")
        print(f"Received entry_hash: {entry_hash}")

        # Step 2: Construct the transaction
        context = get_chain_context()
        payment_address = Address.from_primitive(address)

        # Ensure the payment address is valid and has UTxOs
        utxos = context.utxos(payment_address)
        if not utxos:
            raise ValueError("No UTxOs found for the given address")

        # Use the entry_hash as the datum
        datum = VestingParams(entry_hash.encode('utf-8'))

        builder = TransactionBuilder(context)
        builder.add_input_address(payment_address)

        builder.add_output(
            TransactionOutput(
                address=payment_address,  # Send back to the same address for simplicity
                amount=1000000,  # Amount in lovelace
                datum=datum
            )
        )

        unsigned_tx = builder.build()  # Build the unsigned transaction

        # Return the unsigned transaction to the frontend for signing
        return jsonify({'unsignedTx': unsigned_tx.to_cbor().hex()})

    except Exception as e:
        # Log the exception for debugging
        print(f"Error in prepare_transaction: {str(e)}")
        return jsonify({'error': str(e)}), 400


@app.route('/submit_transaction', methods=['POST'])
def submit_transaction():
    try:
        data = request.json
        signed_tx_cbor = data['signedTx']

        # Submit the signed transaction to the blockchain
        context = get_chain_context()
        signed_tx = context.tx_from_cbor(signed_tx_cbor)
        tx_id = context.submit_tx(signed_tx)

        return jsonify({'txHash': tx_id})

    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True)
