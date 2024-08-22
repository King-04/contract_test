var recipientItem = null;

class RecipientForm extends React.Component {
    constructor(props) {
        super(props);
        this.onSubmit = this.onSubmit.bind(this);
    }
    componentDidMount() {
        this.refs.address.focus();
        this.refs.amount.focus();
    }
    onSubmit(event) {
        event.preventDefault();
        var newAddressValue = this.refs.address.value;
        var newAmountValue = this.refs.amount.value;

        if(newAddressValue && newAmountValue) {
            this.props.setRecipient({ newAddressValue, newAmountValue });
            this.refs.form.reset();
        }
    }
    render () {
        return (
            <form ref="form" onSubmit={this.onSubmit} className="form-inline">
                <input type="text" ref="address" className="form-control" placeholder="Add recipient address..." required/>
                <input type="number" ref="amount" className="form-control" placeholder="Amount in ADA" required/>
                <button type="submit" className="btn btn-default">Set Recipient</button>
            </form>
        );
    }
}

class RecipientApp extends React.Component {
    constructor (props) {
        super(props);
        this.state = {
            recipientItem: null,
            connected: false
        };
        this.prepareSender = this.prepareSender.bind(this);
        this.connectWallet = this.connectWallet.bind(this);
        this.signTx = this.signTx.bind(this);
        this.sendTxAndWitnessBack = this.sendTxAndWitnessBack.bind(this);
    }

    setRecipient(recipientItem) {
        this.setState({ recipientItem: recipientItem });
    }

    submitRequest(sender, changeAddress) {
        fetch('/build_tx', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'sender': sender,
                'change_address': changeAddress,
                'recipient': [this.state.recipientItem.newAddressValue, this.state.recipientItem.newAmountValue]
            })
        })
        .then(response => response.json())
        .then(this.signTx)
        .catch(error => console.error('Error:', error));
    }


    signTx(tx) {
        window.cardano.signTx(tx['tx']).then((witness) => {
            this.sendTxAndWitnessBack(tx['tx'], witness)
        })
    }

    sendTxAndWitnessBack(tx, witness) {
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
            alert("Transaction: " + data["tx_id"] + " submitted!");
        })
        .catch(error => console.error('Error:', error));
    }


    prepareSender() {
        window.cardano.getUsedAddresses().then((senders) => {
            const sender = senders[0];
            window.cardano.getChangeAddress().then((changeAddress) => {
                this.submitRequest(sender, changeAddress);
            });
        });
    }

    connectWallet(event) {
        if (!this.state.connected) {
            window.cardano.nami.enable().then(() => {
                this.setState({ connected: true });
            });
        }
    }

    render() {
        return (
            <div id="main">
                <h1>Send ADA using Nami Wallet</h1>
                <RecipientForm setRecipient={this.setRecipient.bind(this)} />
                <br/>
                <button disabled={!this.state.connected || !this.state.recipientItem} onClick={this.prepareSender}>Submit Tx</button>
                <button disabled={this.state.connected} onClick={this.connectWallet}>Connect Nami Wallet</button>
            </div>
        );
    }
}

ReactDOM.render(<RecipientApp />, document.getElementById('app'));
