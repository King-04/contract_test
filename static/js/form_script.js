document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('certifyForm');
    const popup = document.getElementById('popupOverlay');
    const closePopup = document.getElementById('closePopup');
    const popupMessage = document.getElementById('popupMessage');

    form.addEventListener('submit', async function(e) {
        e.preventDefault(); // Prevent form from submitting traditionally

        const formData = new FormData(form);

        try {
            // Send AJAX request to submit the form and store the data in a JSON file
            const response = await fetch('/submit_form', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            // Display the response in a popup
            let message = `${data.message}\n\n`;
            message += `Certificate: ${data.details.certificate_name}\n`;
            message += `Recipient: ${data.details.recipient_name}\n`;
            message += `ID: ${data.details.recipient_id}`;

            // Store entry_hash for the next transaction step
            formData.append('entry_hash', data.details.entry_hash);

            popupMessage.textContent = message;
            popup.style.display = 'flex';

            // Proceed with the transaction preparation and signing
            await prepareTransaction(formData);

        } catch (error) {
            console.error('Error:', error);
            popupMessage.textContent = 'An error occurred while submitting the form.';
            popup.style.display = 'flex';
        }
    });

    closePopup.addEventListener('click', function() {
        popup.style.display = 'none';
        form.reset(); // Optional: reset the form after closing the popup
    });

    async function prepareTransaction(formData) {
        try {
            const nami = await connectNami();
            if (!nami) throw new Error("Nami Wallet connection failed.");
            const address = await nami.getUsedAddresses();
            console.log("Connected address:", address);

            formData.append('address', address[0]); // Use the first address
            const response = await fetch('/prepare_transaction', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorDetails = await response.json();
                throw new Error(errorDetails.error || 'Unknown error occurred');
            }

            const transactionData = await response.json();
            const signedTx = await nami.signTx(transactionData.unsignedTx);
            console.log("Signed Transaction:", signedTx);

            const submitResponse = await fetch('/submit_transaction', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({signedTx})
            });
            const submitResult = await submitResponse.json();

            const message = `Transaction submitted successfully!\nTransaction Hash: ${submitResult.txHash}`;
            popupMessage.textContent = message;
            popup.style.display = 'flex';

        } catch (error) {
            console.error('Error during transaction preparation and signing:', error);
            popupMessage.textContent = `An error occurred during the transaction: ${error.message}`;
            popup.style.display = 'flex';
        }
    }

    async function connectNami() {
        if (window.cardano && window.cardano.nami) {
            try {
                const nami = await window.cardano.nami.enable();
                const address = await nami.getUsedAddresses();
                console.log("Connected address:", address);
                return nami;
            } catch (error) {
                console.error("Failed to connect to Nami Wallet:", error);
                alert("Could not connect to Nami Wallet. Please make sure it's installed and unlocked.");
            }
        } else {
            console.log("Nami Wallet not installed.");
            alert("Nami Wallet is not installed. Please install it to proceed.");
        }
    }
});






////document.addEventListener('DOMContentLoaded', function() {
////  const form = document.getElementById('certifyForm');
////  const popup = document.getElementById('popupOverlay');
////  const closePopup = document.getElementById('closePopup');
////  const popupMessage = document.getElementById('popupMessage');
////
////  form.addEventListener('submit', function(e) {
////    e.preventDefault();
////
////    // Collect form data
////    const formData = new FormData(form);
////
////    // Send AJAX request
////    fetch('/submit_form', {
////      method: 'POST',
////      body: formData
////    })
////    .then(response => response.json())
////    .then(data => {
////      let message = `${data.message}\n\n`;
////      message += `Certificate: ${data.details.certificate_name}\n`;
////      message += `Recipient: ${data.details.recipient_name}\n`;
////      message += `ID: ${data.details.recipient_id}`;
////
////      popupMessage.textContent = message;
////      popup.style.display = 'flex';
////    })
////    .catch(error => {
////      console.error('Error:', error);
////      popupMessage.textContent = 'An error occurred while submitting the form.';
////      popup.style.display = 'flex';
////    });
////  });
////
////  closePopup.addEventListener('click', function() {
////    popup.style.display = 'none';
////    form.reset(); // Optional: reset the form after closing the popup
////  });
////});