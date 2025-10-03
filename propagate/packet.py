
from uuid import UUID, uuid4

from msgpack import unpackb, packb

from .keystore import Keystore


PREFIX = bytes.fromhex("0123456789abcdeffedcba9876543210")
PROTOCOL_VERSION = "v1-pre4"


class IncompatibleProtocolVersion(ValueError):

    def __init__(self, version: str):
        self.version = version

    def __str__(self):
        return f"Protocol version {self.version} incompatible with version {PROTOCOL_VERSION}"


class PacketSerializationError(ValueError):

    def __init__(self, reason: str):
        self.reason = reason

    def __str__(self):
        return self.reason


class PacketDeserializationError(ValueError):

    def __init__(self, reason: str):
        self.reason = reason

    def __str__(self):
        return self.reason


class Packet:

    def __init__(
        self,
        channel_id: int,
        message_uuid: UUID,
        author_id: str,
        message_body: bytes,
        utf8_encoded: bool,
        encryption_scheme: str,
        signature: bytes = None
    ):
        # check input and set attributes

        if not type(channel_id) == int:
            raise TypeError(f"Invalid type {type(channel_id)} for channel_id")
        self.channel_id = channel_id % (2**32)

        if not isinstance(message_uuid, UUID):
            raise TypeError(f"Invalid type {type(message_uuid)} for message_uuid")
        self._message_uuid = message_uuid

        if type(author_id) != str:
            raise TypeError(f"Invalid type {type(author_id)} for author_id")
        if not len(author_id) > 0:
            raise ValueError("author_id can't be an empty string!")
        self.author_id = author_id

        if type(message_body) != bytes:
            raise TypeError(f"Invalid type {type(message_body)} for message_body")
        if not len(message_body) > 0:
            raise ValueError("message_body can't be empty!")
        self._message_body = message_body

        self.utf8_encoded = bool(utf8_encoded)

        if not type(encryption_scheme) == str:
            raise TypeError(f"Invalid type {type(encryption_scheme)} for encryption_scheme")
        if len(encryption_scheme) > 0 and utf8_encoded:
            raise ValueError("encryption_scheme is set, but utf8_encoded is True")
        self.encryption_scheme = encryption_scheme

        if not type(signature) == bytes and not signature is None:
            raise TypeError(f"Invalid type {type(signature)} for signature")
        self.signature = signature

    def get_message_uuid(self) -> UUID:
        return self._message_uuid

    def get_message_body(self) -> bytes:
        return self._message_body

    def set_message_body(self, data: bytes):
        if type(data) != bytes:
            raise TypeError(f"Invalid type {type(data)} for data!")
        self.signature = None
        self._message_uuid = uuid4
        self._message_body = data


    def sign(self, keystore: Keystore):
        self.signature = keystore.sign(self.author_id, self._message_uuid.bytes + self._message_body)

    def verify(self, keystore: Keystore) -> bool:
        return keystore.verify(self.author_id, self._message_uuid.bytes + self._message_body, self.signature)


    def serialize(self) -> bytes:
        if self.signature is None:
            raise PacketSerializationError("Signature missing!")
        if len(self.signature) != 64:
            raise PacketSerializationError("Signature length invalid")
        return PREFIX + self.channel_id.to_bytes(4, "big") + packb([
            PROTOCOL_VERSION,
            self._message_uuid.bytes,
            self.author_id,
            self._message_body,
            self.utf8_encoded,
            self.encryption_scheme,
            self.signature
        ])

    @classmethod
    def deserialize(cls, data: bytes) -> 'Packet':
        if len(data) < 96: # realistically this should be higher
            raise PacketDeserializationError("data isn't long enough")
        pfx = data[:16]
        if pfx != PREFIX:
            raise PacketDeserializationError("Packet doesn't start with correct prefix")
        channel_id = int.from_bytes(data[16:20], "big")
        msgfields = unpackb(data[20:])
        proto_version = msgfields[0]
        if proto_version != PROTOCOL_VERSION:
            raise IncompatibleProtocolVersion(proto_version)
        return cls(
            channel_id=channel_id,
            message_uuid=UUID(bytes=msgfields[1]),
            author_id=msgfields[2],
            message_body=msgfields[3],
            utf8_encoded=msgfields[4],
            encryption_scheme=msgfields[5],
            signature=msgfields[6]
        )


    @classmethod
    def new(
        cls,
        author_id: str,
        message_body: bytes | str,
        channel_id: int = 0,
        encryption_scheme: str = ""
    ) -> 'Packet':
        '''Use this method to create a new Packet with minimal input'''
        if type(message_body) == str:
            message_body = message_body.encode("utf8")
            utf8_encoded = not len(encryption_scheme) > 0
        else:
            utf8_encoded = False
        return cls(
            channel_id=channel_id,
            message_uuid=uuid4(),
            author_id=author_id,
            message_body=message_body,
            utf8_encoded=utf8_encoded,
            encryption_scheme=encryption_scheme
        )
