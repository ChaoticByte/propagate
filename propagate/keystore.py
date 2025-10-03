
from Crypto.PublicKey.ECC import EccKey
from Crypto.Signature import eddsa


class Keystore:

    def __init__(self):
        self._keys = {} # author_id: EccKey

    def add_key(self, author_id: str, key: EccKey):
        if not type(author_id) == str:
            raise TypeError("author_id must be string")
        if not isinstance(key, EccKey):
            raise TypeError("key must be an object of EccKey")
        if not key.curve == "Ed25519":
            raise ValueError(f"key must be a Ed25519 curve key, not {key.curve}")
        self._keys[author_id] = key

    def sign(self, author_id: str, data: bytes) -> bytes:
        s = eddsa.new(self._keys[author_id], "rfc8032")
        return s.sign(data)

    def verify(self, author_id: str, data: bytes, signature: bytes) -> bool:
        v = eddsa.new(self._keys[author_id], "rfc8032")
        try:
            v.verify(data, signature)
            return True
        # EdDSASigScheme.verify raises a ValueError when the signature is not authentic
        except ValueError:
            return False
