###############################################################################
# Copyright 2019 StarkWare Industries Ltd.                                    #
#                                                                             #
# Licensed under the Apache License, Version 2.0 (the "License").             #
# You may not use this file except in compliance with the License.            #
# You may obtain a copy of the License at                                     #
#                                                                             #
# https://www.starkware.co/open-source-license/                               #
#                                                                             #
# Unless required by applicable law or agreed to in writing,                  #
# software distributed under the License is distributed on an "AS IS" BASIS,  #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.    #
# See the License for the specific language governing permissions             #
# and limitations under the License.                                          #
###############################################################################

import hashlib
import json
import math
import os
from typing import Optional
from ecdsa.rfc6979 import generate_k

from stark_lib.math_utils import *

ECPoint = Tuple[int, int]

PEDERSEN_HASH_POINT_FILENAME = os.path.join(os.path.dirname(__file__), "pedersen_params.json")
PEDERSEN_PARAMS = json.load(open(PEDERSEN_HASH_POINT_FILENAME))

FIELD_PRIME = PEDERSEN_PARAMS["FIELD_PRIME"]
ALPHA = PEDERSEN_PARAMS["ALPHA"]
EC_ORDER = PEDERSEN_PARAMS["EC_ORDER"]
CONSTANT_POINTS = PEDERSEN_PARAMS["CONSTANT_POINTS"]
SHIFT_POINT = CONSTANT_POINTS[0]

N_ELEMENT_BITS_ECDSA = math.floor(math.log(FIELD_PRIME, 2))
N_ELEMENT_BITS_HASH = FIELD_PRIME.bit_length()
EC_GEN = CONSTANT_POINTS[1]

ECSignature = Tuple[int, int]


def pedersen_hash(*elements: int) -> int:
    return pedersen_hash_as_point(*elements)[0]

def pedersen_hash_as_point(*elements: int) -> ECPoint:
    """
    Similar to pedersen_hash but also returns the y coordinate of the resulting EC point.
    This function is used for testing.
    """
    point = SHIFT_POINT
    for i, x in enumerate(elements):
        if type(x) == str: x = int(x, 16)
        point_list = CONSTANT_POINTS[
            2 + i * N_ELEMENT_BITS_HASH : 2 + (i + 1) * N_ELEMENT_BITS_HASH
        ]
        assert len(point_list) == N_ELEMENT_BITS_HASH
        for pt in point_list:
            assert point[0] != pt[0], "Unhashable input."
            if x & 1:
                point = ec_add(point, pt, FIELD_PRIME)
            x >>= 1
        assert x == 0
    return point


def get_hash_from_tx(variables: dict):
    packedMessage = 1

    packedMessage = int(packedMessage << 31) + variables['senderVaultId']
    packedMessage = int(packedMessage << 31) + variables['receiverVaultId']
    packedMessage = int(packedMessage << 63) + int(variables['amount'])
    packedMessage = int(packedMessage << 63) + 0
    packedMessage = int(packedMessage << 31) + variables['nonce']
    packedMessage = int(packedMessage << 22) + variables['expirationTimestamp']

    pedersen1 = pedersen_hash(variables['token'], variables['receiverPublicKey'])
    pedersen2 = pedersen_hash(pedersen1, packedMessage)

    return hex(pedersen2)

def inv_mod_curve_size(x: int) -> int:
    return div_mod(1, x, EC_ORDER)

def generate_k_rfc6979(msg_hash: int, priv_key: int, seed: Optional[int] = None) -> int:
    # Pad the message hash, for consistency with the elliptic.js library.
    if 1 <= msg_hash.bit_length() % 8 <= 4 and msg_hash.bit_length() >= 248:
        # Only if we are one-nibble short:
        msg_hash *= 16

    if seed is None:
        extra_entropy = b""
    else:
        extra_entropy = seed.to_bytes(math.ceil(seed.bit_length() / 8), "big")

    return generate_k(
        EC_ORDER,
        priv_key,
        hashlib.sha256,
        msg_hash.to_bytes(math.ceil(msg_hash.bit_length() / 8), "big"),
        extra_entropy=extra_entropy,
    )


def sign(msg_hash: int, priv_key: int, seed: Optional[int] = None) -> ECSignature:
    if type(msg_hash) == str: msg_hash = int(msg_hash, 16)
    if type(priv_key) == str: priv_key = int(priv_key, 16)
    priv_key %= 3618502788666131213697322783095070105526743751716087489154079457884512865583

    # Note: msg_hash must be smaller than 2**N_ELEMENT_BITS_ECDSA.
    # Message whose hash is >= 2**N_ELEMENT_BITS_ECDSA cannot be signed.
    # This happens with a very small probability.
    # assert 0 <= msg_hash < 2**N_ELEMENT_BITS_ECDSA, "Message not signable."

    # Choose a valid k. In our version of ECDSA not every k value is valid,
    # and there is a negligible probability a drawn k cannot be used for signing.
    # This is why we have this loop.
    while True:
        k = generate_k_rfc6979(msg_hash, priv_key, seed)
        # Update seed for next iteration in case the value of k is bad.
        if seed is None:
            seed = 1
        else:
            seed += 1

        # Cannot fail because 0 < k < EC_ORDER and EC_ORDER is prime.
        x = ec_mult(k, EC_GEN, ALPHA, FIELD_PRIME)[0]

        # DIFF: in classic ECDSA, we take int(x) % n.
        r = int(x)
        if not (1 <= r < 2**N_ELEMENT_BITS_ECDSA):
            # Bad value. This fails with negligible probability.
            continue

        if (msg_hash + r * priv_key) % EC_ORDER == 0:
            # Bad value. This fails with negligible probability.
            continue

        w = div_mod(k, msg_hash + r * priv_key, EC_ORDER)
        if not (1 <= w < 2**N_ELEMENT_BITS_ECDSA):
            # Bad value. This fails with negligible probability.
            continue

        s = inv_mod_curve_size(w)
        return hex(r), hex(s)


def private_key_to_ec_point_on_stark_curve(priv_key: int) -> ECPoint:
    # assert 0 < priv_key < EC_ORDER
    return ec_mult(priv_key, EC_GEN, ALPHA, FIELD_PRIME)

def private_to_stark_key(priv_key: int) -> int:
    if type(priv_key) == str: priv_key = int(priv_key, 16)
    res = private_key_to_ec_point_on_stark_curve(priv_key)
    return {'x': hex(res[0]), 'y': hex(res[1])}
