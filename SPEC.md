# propagate Networking Specification

> [!IMPORTANT]  
> This document is a WORK IN PROGRESS

> [!NOTE]  
> This protocol version is not yet implemented in the official implementation.

**Protocol version:** `v1-pre4`

This document describes how packets are sent through the network of nodes, how packets are structured, etc.


## Overview

### Underlying network protocol

All connections are using unencrypted **websockets** as the underlying network procol.
Implementations **may** support secure websockets, but this is outside of the scope of this specification.


### How a packet travels through the network

```
 Network A
.~~~~~~~~~~~~~~~~~~~~~.
(                     )
(  Client A ——> Node* ———.
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


* Gateway Node for Client A
```

#### Client A

Client A wants to send a message.

First, the client has to set the payload by setting all required fields and encoding the date using MessagePack - see [Packet Payload](#packet-payload), [Signatures](#signatures) and [Encryption](#encryption).

The packet is created by concatenating the prefix, the channel id and the payload (see [Packet](#packet)).

The client connects to one or more gateway node(s) via websocket, or uses an existing connection, and sends the packet.


#### Node(s)

Upon startup, a node connects to all known other nodes. The connection must stay alive or the node must reconnect after it looses the connection.

It also listens for incoming connections on its configured interface and port.

When a node receives a packet, it verifies its signature (field `6`). The public key that is used for verification must be determined by the author id (packet field `2`).

Optional: The node may also check if the author is allowed to send on this channel (field `3`), or the channel itself is allowed.

If the message is okay, it gets relayed to all open connections.

> [!IMPORTANT]  
> The node **must** keep track of the last message UUIDs and drop all messages that re-appear.


#### Client B

Client B connects to its known gateway node(s) & tries to reconnect when it looses a connection.

On an incoming message, it may

- filter out messages that don't have the correct channel id
- verify the signature
- decrypt the body based on the encryption scheme (field `5`)


## Packet

A complete packet has a **16-byte** long prefix, a **4-byte** channel-id and a [MessagePack](https://msgpack.org/)-encoded payload:

```
[prefix][channel-id][payload]
```

(without the brackets)

### Prefix

Hexadecimal representation of the 16-byte prefix:

```
0123456789abcdeffedcba9876543210
```

If the message is not correctly prefixed, it must be discarded.


### Channel ID

The channel id is a 32bit integer, stored in 4 bytes in big-endian byte order.  
The default channel is `0`.

Clients use this to filter messages. Nodes use this for authorization (in combination with the author's public key and the signature). It is also used for determining the per-channel encryption key, if the message body is encrypted.


### Packet Payload

The msgpack-encoded data is a list with the following fields:

| idx | type   | description            | notes |
| --- | ------ | ---------------------- | ----- |
|   0 | string | protocol version       | see the beginning of this document for the current protocol version; customized specs should prefix the version with e.g. `example-` |
|   1 | bytes  | message uuid           | must be a valid [RFC4122](https://datatracker.ietf.org/doc/html/rfc4122.html) UUID (16 bytes, big endian) |
|   2 | string | author id              | clients & nodes use this field to determine the correct public key to verify the signature |
|   3 | bytes  | message body           | |
|   4 | bool   | msg body utf8-encoded? | gives a hint to clients wether the body can be decoded into a string; must be set to `false` when encryption is used |
|   5 | string | encryption scheme      | may be an empty string; see [Encryption](#encryption) |
|   6 | bytes  | signature              | see [Signatures](#signatures) (64 bytes) |


### Signatures

Signatures are used by nodes to verify the message

- for authentication.
- for authorization - the nodes may have a whitelist for allowed authors of the whole network or certain channels.

> [!IMPORTANT]  
> If encryption is used, you must sign the ciphertext, not the plaintext!

Pseudo-code for signing and verifying:

```
# sign message
sign(
    msg.uuid + msg.body,
    private_key(msg.author_id)
)
# -> 64byte signature

# verify message
verify(
    msg.uuid + msg.body,
    public_key(msg.author_id)
)
# -> bool/error code/...
```

| pseudo-code     | description        |
| --------------- | ------------------ |
| `sign()`        | **Ed25519** sign   |
| `verify()`      | **Ed25519** verify |
| `private_key()` | load author's **Ed25519** private key |
| `public_key()`  | load author's **Ed25519** public key  |


### Encryption

> [!NOTE]  
> Encryption is implemented by the client and **optional**.  
If you don't use encryption, set the field to an empty string.

> [!IMPORTANT]  
> Only the message body may be encrypted.

Encryption should be done per-channel.  
The packet payload has field `5` with the name of the encryption scheme.
Use this to tell other clients the encryption you are using (e.g. `salsa20_256`). Other encryption-related (meta-)data like nonces, hmacs, etc. must be written to the message body. Parse it yourself.
