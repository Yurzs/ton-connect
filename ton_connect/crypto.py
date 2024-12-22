import base64
import json
from typing import Any

from nacl.encoding import HexEncoder
from nacl.public import Box, PrivateKey, PublicKey
from nacl.utils import random


class SessionCrypto:
    def __init__(self, private_key: PrivateKey | str | bytes | None = None) -> None:
        """Session crypto class."""

        if isinstance(private_key, (str, bytes)):
            private_key = private_key.encode() if isinstance(private_key, str) else private_key
            private_key = PrivateKey(private_key, HexEncoder)

        elif private_key is None:
            private_key = PrivateKey.generate()

        self.private_key: PrivateKey = private_key
        self.public_key: str = self.private_key.public_key.encode().hex()

    @staticmethod
    def generate_nonce() -> bytes:
        return random(Box.NONCE_SIZE)

    def encrypt(self, data: dict[str, Any], pub_key: PublicKey | str | bytes) -> bytes:
        """Encrypt data with public private_key

        :param data: Data to encrypt.
        :param pub_key: Recipient public private_key.
        :return: Encrypted data.
        """

        if isinstance(pub_key, (str, bytes)):
            pub_key = pub_key.encode() if isinstance(pub_key, str) else pub_key.hex().encode()
            pub_key = PublicKey(pub_key, HexEncoder)

        box = Box(self.private_key, pub_key)
        nonce = self.generate_nonce()
        encrypted_data = box.encrypt(json.dumps(data).encode(), nonce)

        return base64.b64encode(nonce + encrypted_data.ciphertext)

    def decrypt(self, data: bytes, pub_key: PublicKey | str | bytes) -> str:
        """Decrypt data with public private_key

        :param data: Data to decrypt.
        :param pub_key: Sender public private_key.
        :return: Decrypted data.
        """

        if isinstance(pub_key, (str, bytes)):
            pub_key = pub_key.encode() if isinstance(pub_key, str) else pub_key.hex().encode()
            pub_key = PublicKey(pub_key, HexEncoder)

        box = Box(self.private_key, pub_key)
        nonce = data[: Box.NONCE_SIZE]
        encrypted_data = data[Box.NONCE_SIZE :]

        return box.decrypt(encrypted_data, nonce).decode()
