import keyring
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import logging
from typing import Any, Optional
import getpass

log = logging.getLogger(__name__)


class Crypto:

    SERVICE_NAME = "tbh-cli"
    DAR_KEY_NAME = "dar"
    MINIO_SECRET_KEY_NAME = "minio_secret_key"

    def __init__(self) -> None:
        pass

    @property
    def minio_secret_key(self) -> str:
        key = keyring.get_password(
            service_name=self.SERVICE_NAME,
            username=self.MINIO_SECRET_KEY_NAME,
        )
        if not key:
            key = getpass.getpass(prompt="Enter the MINIO secret key: ")
            assert key
            keyring.set_password(
                service_name=self.SERVICE_NAME,
                username=self.MINIO_SECRET_KEY_NAME,
                password=key,
            )
        return key

    def _generate_password(self) -> str:
        # Generate a new key...
        log.warning("Generating DAR credentials in keyring")
        key = get_random_bytes(16)
        password = base64.b64encode(key).decode('ascii')
        keyring.set_password(
            service_name=self.SERVICE_NAME,
            username=self.DAR_KEY_NAME,
            password=password,
        )
        password = keyring.get_password(
            service_name=self.SERVICE_NAME,
            username=self.DAR_KEY_NAME,
        )
        assert password
        return password

    def _create_cipher(self, nonce: Optional[bytes] = None) -> Any:
        password = keyring.get_password(
            service_name=self.SERVICE_NAME,
            username=self.DAR_KEY_NAME,
        )
        if (password is None) and (nonce is None):
            password = self._generate_password()
        if not password:
            raise RuntimeError("Unable to recover password from keyring")
            
        key = base64.b64decode(password.encode('ascii'))
        return AES.new(key, AES.MODE_GCM, nonce=nonce)

    def encrypt(self, value: str) -> str:
        cipher = self._create_cipher()
        ciphertext, tag = cipher.encrypt_and_digest(value.encode('utf-8'))
        output = cipher.nonce + tag + ciphertext
        encoded_output = base64.b64encode(output).decode('ascii')
        return encoded_output

    def decrypt(self, value: str) -> str:
        bin_value = base64.b64decode(value.encode('ascii'))
        nonce = bin_value[:16]
        tag = bin_value[16:32]
        ciphertext = bin_value[32:]
        cipher = self._create_cipher(nonce=nonce)
        data = cipher.decrypt_and_verify(ciphertext, tag)
        return data.decode('utf-8')


