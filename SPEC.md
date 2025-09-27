# argh Networking Specification

This document describes how packets are sent through the network of nodes, how packets are structured, etc.


## Overview

### Underlying network protocol

All connections are using unencrypted (TODO) websockets as the underlying network procol.

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

## Packet Structure

> [!IMPORTANT]  
> Not yet implemented.

A complete packet is a [MessagePack](https://msgpack.org/)-encoded dictionary with the following fields:

| field  | type   | description |
| ------ | ------ | ----------- |
| `uuid` | bytes  | 16-byte big endian uuid |
| `body` | bytes  | The message body |

(TODO)

The client who sends the packet to the first node must already provide a complete packet. Nodes solely verify & relay packets.
