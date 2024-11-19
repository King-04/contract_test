document.addEventListener('DOMContentLoaded', function () {
    const verifyForm = document.getElementById('verifyForm');
    const connectWalletButton = document.getElementById('connectWallet');
    const submitTxButton = document.getElementById('submitTx');
    let connected = false;
    let verifyItem = null;

     // Check if Nami Wallet is installed
    if (!window.cardano || !window.cardano.nami) {
        displayWalletError();
    } else {
        console.log("Nami Wallet detected!");
        alert("Nami Wallet detected!");
    }

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

    function displayWalletError() {
    const errorMessage = document.createElement('div');
    errorMessage.id = 'walletError';
    errorMessage.style.position = 'fixed';
    errorMessage.style.top = '0';
    errorMessage.style.left = '0';
    errorMessage.style.width = '100%';
    errorMessage.style.padding = '15px';
    errorMessage.style.backgroundColor = '#f8d7da';
    errorMessage.style.color = '#721c24';
    errorMessage.style.fontSize = '16px';
    errorMessage.style.textAlign = 'center';
    errorMessage.style.zIndex = '1000';
    errorMessage.innerHTML = `
        <strong>Nami Wallet not detected:</strong>
        Please install the Nami Wallet extension to continue.
        <a href="https://namiwallet.io/" target="_blank" style="color: #0056b3; text-decoration: underline;">Click here to download Nami Wallet</a>.
    `;
    document.body.appendChild(errorMessage);
    }

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

