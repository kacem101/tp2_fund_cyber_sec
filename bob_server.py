import asyncio
import json
import base64
from websockets.asyncio.server import serve
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Generate Bob's RSA key pair
bob_private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
bob_public_key = bob_private_key.public_key()

# Serialize Bob's public key to PEM format
bob_pub_pem = bob_public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode("utf-8")

async def handle_alice(websocket):
    print("[Bob] Alice connected. Sending RSA Public Key...")
    await websocket.send(json.dumps({"type": "public_key", "key": bob_pub_pem}))

    async for raw_message in websocket:
        data = json.loads(raw_message)

        if data.get("type") == "encrypted_payload":
            # 1. Unpack base64 fields
            enc_session_key = base64.b64decode(data["enc_key"])
            nonce = base64.b64decode(data["nonce"])
            ciphertext = base64.b64decode(data["ciphertext"])

            # 2. Decrypt the AES session key using Bob's RSA private key
            session_key = bob_private_key.decrypt(
                enc_session_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            print("[Bob] Recovered AES Session Key via RSA-OAEP.")

            # 3. Decrypt the bulk message using AES-GCM
            aesgcm = AESGCM(session_key)
            decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
            decrypted_message = decrypted_bytes.decode("utf-8")

            print(f"[Bob] Plaintext Message Received: \"{decrypted_message}\"")

            # 4. Acknowledge receipt
            await websocket.send(json.dumps({"type": "ack", "status": "Message received and decrypted successfully"}))

async def main():
    async with serve(handle_alice, "localhost", 8765):
        print("[Bob] Listening on ws://localhost:8765")
        await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())