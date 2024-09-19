document.addEventListener('DOMContentLoaded', function () {
    const recipientForm = document.getElementById('recipientForm');
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

    recipientForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const address = 'dummy'
        const amount = 3
        // const address = document.getElementById('address').value;
        // const amount = document.getElementById('amount').value;

        if (address && amount) {
            recipientItem = { newAddressValue: address, newAmountValue: amount };
            prepareSender();
        }
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

