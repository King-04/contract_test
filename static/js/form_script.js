document.addEventListener('DOMContentLoaded', function() {
    const recipientForm = document.getElementById('certifyForm');
    const popup = document.getElementById('popupOverlay');
    const closePopup = document.getElementById('closePopup');
    const popupMessage = document.getElementById('popupMessage');
    const connectWalletButton = document.getElementById('connectWallet');
    const submitTxButton = document.getElementById('submitTx');

    let connected = false;
    let recipientItem = null;

    connectWalletButton.addEventListener('click', function () {
        if (!connected) {
            window.cardano.nami.enable().then(() => {
                connected = true;
                submitTxButton.disabled = false;
                alert("Nami Wallet connected!");
            });
        }
    });

    recipientForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Collect form data
        const formData = new FormData(recipientForm);

        //setting up tx
        const address = 'dummy'
        const amount = 3
        // const address = document.getElementById('address').value;
        // const amount = document.getElementById('amount').value;

        if (address && amount) {
            recipientItem = { newAddressValue: address, newAmountValue: amount };
            prepareSender();
        }

        // Send AJAX request
        fetch('/submit_form', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            let message = `${data.message}\n\n`;
            message += `Certificate: ${data.details.certificate_name}\n`;
            message += `Recipient: ${data.details.recipient_name}\n`;
            message += `ID: ${data.details.recipient_id}\n`;
            message += `Copy CERTIFICATE HASH: ${data.details.certificate_hash}`;


            popupMessage.textContent = message;
            popup.style.display = 'flex';
        })
        .catch(error => {
            console.error('Error:', error);
            popupMessage.textContent = 'An error occurred while submitting the form.';
            popup.style.display = 'flex';
        });
    });

    function prepareSender() {
        window.cardano.getUsedAddresses().then((senders) => {
            const sender = senders[0];
            window.cardano.getChangeAddress().then((changeAddress) => {
                submitRequest(sender, changeAddress);
            });
        });
    }

    function submitRequest(sender, changeAddress) {
        fetch('/build_tx', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'sender': sender,
                'change_address': changeAddress,
                'recipient': [recipientItem.newAddressValue, recipientItem.newAmountValue]
            })
        })
        .then(response => response.json())
        .then(signTx)
        .catch(error => console.error('Error:', error));
    }

    function signTx(tx) {
        window.cardano.signTx(tx.tx).then((witness) => {
            sendTxAndWitnessBack(tx.tx, witness);
        });
    }

    closePopup.addEventListener('click', function() {
        popup.style.display = 'none';
        recipientForm.reset(); // Optional: reset the form after closing the popup
    });

    function sendTxAndWitnessBack(tx, witness) {
        fetch('/submit_tx', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'tx': tx,
                'witness': witness
            })
        })
        .then(response => response.json())
        .then(data => {
            alert("Transaction: " + data.tx_id + " submitted!");
            document.getElementById('result').innerText = "Transaction ID: " + data.tx_id;
        })
        .catch(error => console.error('Error:', error));
    }
});
