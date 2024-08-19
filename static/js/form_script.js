document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('certifyForm');
  const popup = document.getElementById('popupOverlay');
  const closePopup = document.getElementById('closePopup');
  const popupMessage = document.getElementById('popupMessage');

  form.addEventListener('submit', async function(e) {
    e.preventDefault();

    // Collect form data
    const formData = new FormData(form);

    // Display the collected data in the popup (before submitting to the backend)
    let message = `Certificate: ${formData.get('certificate_name')}\n`;
    message += `Recipient: ${formData.get('recipient_name')}\n`;
    message += `ID: ${formData.get('recipient_id')}`;
    popupMessage.textContent = message;
    popup.style.display = 'flex';

    try {
      // Connect to Nami Wallet
      const nami = await connectNami();
      if (!nami) throw new Error("Nami Wallet connection failed.");

      // Prepare the transaction (adjust as needed for your contract)
      const transaction = {
        to: "addr_test1vzp9wsa4gm64tj4jqp89yt6cv5py6wjtrsmpz0efrhjtpfswpldp7", // Replace with your contract address
        amount: "1000000", // Adjust the amount as needed
        //datum: "optional_datum", // Optional: if you want to attach a datum, this is where it goes
      };

      // Sign and submit the transaction
      const signedTx = await nami.signTx(transaction);
      const txHash = await nami.submitTx(signedTx);

      console.log("Transaction submitted with hash:", txHash);

      // Optionally, include the transaction hash in the form data to send to your backend
      formData.append('tx_hash', txHash);

      // Send the AJAX request with the transaction hash to the backend
      const response = await fetch('/submit_form', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();

      message += `\n\nTransaction Hash: ${txHash}`;
      popupMessage.textContent = message;
      popup.style.display = 'flex';

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

  async function connectNami() {
    if (window.cardano && window.cardano.nami) {
      try {
        const nami = await window.cardano.nami.enable();
        const address = await nami.getUsedAddresses();
        console.log("Connected address:", address);
        return nami; // Return the nami object for further use
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