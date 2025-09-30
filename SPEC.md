# propagate Networking Specification

**Protocol version:** `v1-pre1`

This document describes how packets are sent through the network of nodes, how packets are structured, etc.


## Overview

### Underlying network protocol

All connections are using unencrypted **websockets** as the underlying network procol.
Implementations **may** support secure websockets, but this is outside of the scope of this specification.


### How a packet travels through the network

(TODO)


### Packet Flow

```
 Network A
.~~~~~~~~~~~~~~~~~~~~~.
(                     )
(   Client ——> Node —————.
(               |     )  |
'~~~~~~~~~~~~~~~|~~~~~'  |
                |        |
 Network B      |        |
.~~~~~~~~~~~~~~~|~~~~~~~~|~~~~~~~~~~~~~~~~.
(               v        v                )
(   Client <—— Node <=> Node ——> Client   )
(               |        |                )
'~~~~~~~~~~~~~~~|~~~~~~~~|~~~~~~~~~~~~~~~~'
                |        |
                |        '————.
 Network C      |             |
.~~~~~~~~~~~~~~~|~~~~~.       :———> other Networks
(               v     )       |
(   Client <—— Node ——————————'
(   Client <————|     )
(   Client <————|     )
(      ... <————'     )
(                     )
'~~~~~~~~~~~~~~~~~~~~~'
```


## Packets

> [!IMPORTANT]  
> Not yet implemented in the official implementation.

A complete packet has a **16-byte** long prefix and [MessagePack](https://msgpack.org/)-encoded data:

```
<prefix><data>
```

Hexadecimal representation of the 16-byte prefix:

```
0123456789abcdeffedcba9876543210
```

If the message is not correctly prefixed, it must be discarded.


### Fields in the packet

The msgpack-encoded data has the following fields:

| field            | type   | description               | notes |
| ---------------- | ------ | ------------------------- | ----- |
| `version`        | string | protocol version          | see the beginning of this document for the current protocol version; customized specs should prefix the version with e.g. `example-` |
| `uuid`           | string | hex. message uuid         | must be a valid [RFC4122](https://datatracker.ietf.org/doc/html/rfc4122.html) hexadecimal UUID string |
| `author_id`      | string | author id                 | clients & nodes use this field to determine the correct public key to verify the signature |
| `channel_id`     | string | channel id                | default: `main`, clients may use this to filter messages; also, encryption is done per-channel |
| `body`           | bytes  | message body              | |
| `is_utf8`        | bool   | is the body utf8-encoded? | must be set to `false` when encryption is used; when possible, implementations should convert the message body to a string after parsing, if this is `true` |
| `channel_crypto` | string | channel encryption scheme | may be an empty string; see [Encryption](#encryption) |
| `signature`      | bytes  | data signature            | see [Signatures](#signatures) |


### Signatures

> [!IMPORTANT]  
> If encryption is used, you must sign the ciphertext, not the plaintext!

Pseudo-code for signing and verifying:

```
# sign message
sign(
    hash(
        encode(msg.uuid) + msg.body
    ),
    private_key(msg.author_id)
)
# -> 64byte signature

# verify message
verify(
    hash(
        encode(msg.uuid) + msg.body
    ),
    public_key(msg.author_id)
)
# -> bool/error code/...
```

| pseudo-code     | description          |
| --------------- | -------------------- |
| `encode()`      | UTF8-encoding        |
| `hash()`        | create sha256 digest |
| `sign()`        | ed25519 sign         |
| `verify()`      | ed25519 verify       |
| `private_key()` | load author's ed25519 private key |
| `public_key()`  | load author's ed25519 public key  |


### Encryption

> [!NOTE]  
> Encryption is implemented by the client and optional.

> [!IMPORTANT]  
> Only the message body may be encrypted.

Encryption should be done per-channel.  
The packet has a `channel_crypto` field with the name of the encryption scheme.
Use this to tell other clients the encryption you are using. Other encryption-related (meta-)data must be written to the message body.
