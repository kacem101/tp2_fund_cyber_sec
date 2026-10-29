# TP2: Part 5, Task 4. Hybrid Encryption with OpenSSL (and a Python version)

## 1. Objective

Implement hybrid encryption: a fast symmetric cipher (AES) protects the message, and RSA protects the symmetric key so it can be sent safely. Bob owns the RSA key pair; Alice (the sender) only needs Bob's public key. Both roles were simulated in one directory (`part5`) on WSL.

## 2. Hybrid encryption with the OpenSSL command line

### 2.1 Bob's key pair

```bash
# bob_private.pem (2048-bit RSA private key) was generated first
openssl rsa -pubout -in bob_private.pem -out bob_public.pem
```

`bob_private.pem` (1.7 KB, `rw-------`, owner only) stays with Bob; `bob_public.pem` (451 bytes) is shared with Alice.

### 2.2 Alice: encrypt the message

```bash
echo "Confidential transaction data: Transfer 500 units to Vault-B." > message.txt   # 62 bytes
openssl rand 32 > session.key          # 256-bit random AES session key
openssl rand -hex 16 > iv.txt          # 128-bit IV in hex
openssl enc -aes-256-cbc -salt -in message.txt -out message.enc -pass file:session.key -iv $(cat iv.txt)
openssl pkeyutl -encrypt -pubin -inkey bob_public.pem -in session.key -out session.key.enc -pkeyopt rsa_padding_mode:oaep
```

| File | Size | Meaning |
|---|---|---|
| `message.enc` | 80 bytes | 16-byte `Salted__`+salt header + 62 bytes padded to 64 |
| `session.key.enc` | 256 bytes | Session key encrypted with RSA-2048 (OAEP padding) |

OpenSSL printed `WARNING : deprecated key derivation used. Using -iter or -pbkdf2 would be better.` because `-pbkdf2` was not given (see section 4).

Alice sends `message.enc`, `session.key.enc` and `iv.txt` to Bob. Only the RSA-encrypted key protects the secret; the IV is not secret.

### 2.3 Bob: decrypt

```bash
openssl pkeyutl -decrypt -inkey bob_private.pem -in session.key.enc -out recovered_session.key -pkeyopt rsa_padding_mode:oaep
openssl enc -d -aes-256-cbc -in message.enc -out decrypted_message.txt -pass file:recovered_session.key -iv $(cat iv.txt)
cat decrypted_message.txt
```

```
Confidential transaction data: Transfer 500 units to Vault-B.
```

`decrypted_message.txt` is 62 bytes, the same size as `message.txt`, and `recovered_session.key` is 32 bytes like `session.key`.

## 3. Hybrid encryption in Python (Alice/Bob over WebSocket)

The same scheme implemented programmatically with the `cryptography` and `websockets` libraries. Alice and Bob are two scripts talking over `ws://localhost:8765`.

| Step | Who | Operation |
|---|---|---|
| 1 | Bob | Generates an RSA-2048 key pair, sends the public key (PEM) to Alice |
| 2 | Alice | Generates a random 256-bit AES key and a 12-byte nonce |
| 3 | Alice | Encrypts the message with **AES-256-GCM** |
| 4 | Alice | Encrypts the AES key with Bob's public key using **RSA-OAEP (SHA-256)** |
| 5 | Alice | Sends `enc_key`, `nonce`, `ciphertext` (base64 in JSON) |
| 6 | Bob | Recovers the AES key with his private key, decrypts and authenticates the message with AES-GCM |
| 7 | Bob | Sends an acknowledgement |

Console output of a test run (the code was executed and worked as designed):

```
[Bob] Listening on ws://localhost:8765
[Alice] Received Bob's RSA Public Key.
[Alice] Message symmetrically encrypted with AES-256-GCM.
[Alice] AES Session Key encrypted with Bob's RSA Public Key.
[Alice] Payload sent to Bob.
[Bob] Alice connected. Sending RSA Public Key...
[Bob] Recovered AES Session Key via RSA-OAEP.
[Bob] Plaintext Message Received: "Top Secret: Rendezvous coordinates are 36.7538° N, 3.0588° E."
[Alice] Response from Bob: {"type": "ack", "status": "Message received and decrypted successfully"}
```

## 4. Comparison and observations

| Aspect | OpenSSL CLI version | Python version |
|---|---|---|
| Symmetric cipher | AES-256-CBC | AES-256-GCM |
| Integrity of the ciphertext | None (CBC is unauthenticated) | Built in (GCM authentication tag) |
| RSA padding | OAEP (OpenSSL default hash: SHA-1) | OAEP with SHA-256 and MGF1-SHA-256 |
| IV / nonce | 16-byte IV chosen by hand | 12-byte random nonce |
| Key handling | Files on disk | In memory, sent over a socket |

Points worth noting:

1. **Why hybrid?** RSA-2048 can encrypt only about 190 bytes with OAEP-SHA256 (245 with PKCS#1 v1.5) and is slow. AES handles any size quickly, and RSA solves the key-distribution problem.
2. **OAEP, not textbook RSA.** OAEP adds randomness, so encrypting the same session key twice gives different ciphertexts, and it is secure against chosen-ciphertext attacks.
3. **Mismatch when mixing both versions.** `openssl pkeyutl` uses **SHA-1** for OAEP by default, while the Python code uses **SHA-256**. A key encrypted by one side fails to decrypt on the other (`oaep decoding error`, verified). To interoperate, add `-pkeyopt rsa_oaep_md:sha256 -pkeyopt rsa_mgf1_md:sha256` to the OpenSSL commands.
4. **Deprecated key derivation warning.** With `-pass`, OpenSSL derives the key from a password using the legacy method unless `-pbkdf2 -iter N` is given. Add `-pbkdf2 -iter 200000` on both encryption and decryption.
5. **A raw binary key used as a password.** `openssl rand 32` produces random bytes, and `-pass file:` reads only the first *line* of the file, so a `0x0A` byte (about a 12% chance in 32 bytes) would silently truncate the password. A safer choice is a hex key (`openssl rand -hex 32`), or passing the key directly with `-K <hex> -iv <hex>` and no key derivation at all.
6. **CBC gives confidentiality only.** A modified `message.enc` could be accepted or produce garbage without a reliable error. The Python version uses AES-GCM, which rejects any tampering (`InvalidTag`). For the CLI version, add a signature or HMAC, as in Part 4.
7. **No sender authentication.** In both versions anyone holding Bob's public key can send him a message, so Bob cannot tell who sent it. Alice's RSA signature (Part 4) would fix this. Bob's public key is also not authenticated: an attacker in the middle could substitute their own key during the exchange, which is why certificates exist. The Python demo also uses plain `ws://`, not `wss://`.
8. The IV is public and must be unique per key; here it is fine because each session key is used once.

## 5. Conclusion

Both implementations show the hybrid principle: RSA transports a one-time AES key, AES encrypts the data. The OpenSSL run recovered the message exactly (`decrypted_message.txt`, 62 bytes), and the Python run authenticated and decrypted it using AES-GCM. For real use, prefer the authenticated variant (AES-GCM), explicit OAEP-SHA256 parameters, and add a signature so the receiver also knows who sent the message.
