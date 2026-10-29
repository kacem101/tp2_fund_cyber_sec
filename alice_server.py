import asyncio
import json
import base64
import os
from websockets.asyncio.client import connect
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SECRET_MESSAGE = "Top Secret: Rendezvous coordinates are 36.7538° N, 3.0588° E."

async def run():
    uri = "ws://localhost:8765"
    async with connect(uri) as websocket:
        # 1. Receive Bob's public key
        raw_data = await websocket.recv()
        data = json.loads(raw_data)
        
        bob_public_key = serialization.load_pem_public_key(data["key"].encode("utf-8"))
        print("[Alice] Received Bob's RSA Public Key.")

        # 2. Generate ephemeral AES-256 session key (32 bytes) and nonce (12 bytes)
        session_key = AESGCM.generate_key(bit_length=256)
        nonce = os.urandom(12)

        # 3. Encrypt the secret message with AES-GCM
        aesgcm = AESGCM(session_key)
        ciphertext = aesgcm.encrypt(nonce, SECRET_MESSAGE.encode("utf-8"), None)
        print("[Alice] Message symmetrically encrypted with AES-256-GCM.")

        # 4. Encrypt the AES session key with Bob's RSA Public Key (RSA-OAEP)
        enc_session_key = bob_public_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        print("[Alice] AES Session Key encrypted with Bob's RSA Public Key.")

        # 5. Pack and send payload via JSON
        payload = {
            "type": "encrypted_payload",
            "enc_key": base64.b64encode(enc_session_key).decode("utf-8"),
            "nonce": base64.b64encode(nonce).decode("utf-8"),
            "ciphertext": base64.b64encode(ciphertext).decode("utf-8")
        }
        await websocket.send(json.dumps(payload))
        print("[Alice] Payload sent to Bob.")

        # 6. Wait for Bob's ACK
        ack = await websocket.recv()
        print(f"[Alice] Response from Bob: {ack}")

if __name__ == "__main__":
    asyncio.run(run())