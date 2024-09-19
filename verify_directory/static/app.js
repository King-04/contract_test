document.addEventListener('DOMContentLoaded', function () {
    const verifyForm = document.getElementById('verifyForm');
    const connectWalletButton = document.getElementById('connectWallet');
    const submitTxButton = document.getElementById('submitTx');
    let connected = false;
    let verifyItem = null;

    connectWalletButton.addEventListener('click', function () {
        if (!connected) {
            window.cardano.nami.enable().then(() => {
                connected = true;
                submitTxButton.disabled = false;
                alert("Nami Wallet connected!");
            });
        }
    });

    verifyForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const address = 'dummy'
        // const amount = 3
        // const address = document.getElementById('address').value;
         const secret = document.getElementById('secret').value;

        if (address && secret) {
            verifyItem = { newAddressValue: address, newSecretValue: secret };
            prepareVerSender();
        }
    });

    function prepareVerSender() {
        window.cardano.getUsedAddresses().then((senders) => {
            const sender = senders[0];
            window.cardano.getChangeAddress().then((changeAddress) => {
                submitVerRequest(sender, changeAddress);
            });
        });
    }

    function submitVerRequest(sender, changeAddress) {
        fetch('/build_ver_tx', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'sender': sender,
                'change_address': changeAddress,
                'recipient': [verifyItem.newAddressValue, verifyItem.newSecretValue]
            })
        })
        .then(response => response.json())
        //.then(signVerTx)
        //.catch(error => console.error('Error:', error));
        .then(data => {
            if (data.error) {
                // Display the error message in the result div
                // document.getElementById('result').innerText = data.error;
                document.getElementById('result').innerText = "Sorry, no certificate with this hash is on-chain";
            } else {
                signVerTx(data);
            }
        })
        .catch(error => console.error('Error:', error));
    }

    function signVerTx(tx) {
        window.cardano.signTx(tx.tx).then((witness) => {
            sendVerTxAndWitnessBack(tx.tx, witness);
        });
    }

    function sendVerTxAndWitnessBack(tx, witness) {
        fetch('/submit_ver_tx', {
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
            document.getElementById('result').innerText = "This hash has a certificate on-chain. \n \n Transaction ID: " + data.tx_id;
        })
        .catch(error => console.error('Error:', error));
    }
});

