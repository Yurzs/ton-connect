# TonConnect

TonConnect is a Python library that allows you to connect to TON wallets, manage connections, handle messages, and send requests to the wallet. It provides a convenient way to interact with TON wallets and perform various operations.

## Installation

To install TonConnect, you can use pip:

```bash
pip install ton-connect
```

## Usage

### TonConnect Class

The `TonConnect` class is responsible for managing connections to TON wallets. It provides methods to connect to a wallet, restore a connection, handle messages, start and stop listeners, and send requests to the wallet.

### Initializing TonConnect

To initialize the `TonConnect` class, you need to provide the manifest URL and a storage instance. The manifest URL is the URL to the manifest file of your app, and the storage instance is used to store connection data. Note that the first argument to `DictStorage` is the user id.

```python
from ton_connect.connector import TonConnect
from ton_connect.storage import DictBridgeStorage


manifest_url = "https://example.com/manifest.json"
storage = DictBridgeStorage("user_id")

ton_connect = TonConnect(manifest_url, storage)
```

### Connecting to a Wallet

To connect to a wallet, you need to provide a `WalletApp` instance. The `WalletApp` class represents a wallet app and contains information such as the app name, bridge URL, and universal URL.

You can also use the `TonConnect.get_wallets` method to get a list of supported wallet apps.

```python
from ton_connect.model.app.wallet import WalletApp
from ton_connect.connector import TonConnect

wallets = await TonConnect.get_wallets()
wallet = wallets[0]

connect_url = await ton_connect.connect(wallet)
print("Connect URL:", connect_url)
```

### Restoring a Connection

To restore a connection to a wallet, you can use the `restore_connection` method. This method restores the connection using the stored connection data.

```python
await ton_connect.restore_connection(wallet)
```

### Sending Requests

The `TonConnect` class provides methods to send various requests to the wallet. For example, you can send a transaction request using the `SendTransactionRequest` class.

```python
from ton_connect.model.app.request import SendTransactionRequest, SendTransactionMessage

request = SendTransactionRequest(
    address="0:1234567890abcdef",
    network=1,
    messages=[
        SendTransactionMessage(
            address="0:abcdef1234567890",
            amount="1000000000"
        )
    ]
)

response = await ton_connect.send(wallet.app_name, request)
print("Response:", response)
```

### Listening for Wallet Events

The `TonConnect` class allows you to listen for wallet events by adding event listeners. You can add event listeners for events such as connect, disconnect, and errors.

```python
from ton_connect.model.wallet.event import WalletEventName
from ton_connect.connector import ConnectorEvent

async def on_connect(event: ConnectorEvent):
    print("Connected:", event)

async def on_disconnect(event: ConnectorEvent):
    print("Disconnected:", event)

ton_connect.listen(WalletEventName.CONNECT, on_connect)
ton_connect.listen(WalletEventName.DISCONNECT, on_disconnect)
```

## License

This project is licensed under the MIT License.
