# TP2: Part 4. File Encryption and Decryption Using RSA

Hybrid encryption providing **confidentiality**, **integrity** and **authentication**. Maximus (sender) sends `file.txt` to Lucilla (receiver). Both roles were simulated in the same directory (`REP`) on WSL.

## 1. Principle

RSA is slow and can only encrypt small data, while AES is fast but needs a shared secret. The hybrid scheme combines them:

| Goal | Mechanism | Key used |
|---|---|---|
| Confidentiality of the file | AES-256-CBC with a session key | Shared session key |
| Confidentiality of the session key | RSA encryption | Lucilla's **public** key |
| Integrity | SHA-512 hash of the file | None |
| Authentication (and non-repudiation) | RSA signature of the hash | Maximus's **private** key |

Rule: public keys encrypt and verify, private keys decrypt and sign.

## 2. Task 1: Key generation

```bash
mkdir REP ; chmod 700 REP ; cd REP
openssl genrsa -out maximus.prive 2048
chmod 400 maximus.prive
openssl rsa -in maximus.prive -pubout -out maximus.public

openssl genrsa -out lucilla.prive 2048
chmod 400 lucilla.prive
openssl rsa -in lucilla.prive -pubout -out lucilla.public
```

Result: private keys are 1.7 KB with permissions `r--------` (owner read only), public keys are 451 bytes and shareable. The first attempt failed with `lucilla.pub: No such file or directory` because Lucilla's key pair had not been generated yet.

## 3. Maximus's process (sender)

### 3.1 Encrypt the file with AES

```bash
openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 -in file.txt -out file.aes -pass file:k.session
```

Output: `file.aes` (48 bytes for a 20-byte input: 16-byte `Salted__` + salt header, plus 32 bytes of padded ciphertext).

Differences from the handout command (`openssl enc -in file.txt -out file.aes -e -aes256 -k k.session`):
- Without `-pbkdf2` OpenSSL printed `WARNING: deprecated key derivation used`, meaning a weak legacy derivation was used.
- `-k k.session` takes the password **text** (the literal string `k.session`), not the file's contents. `-pass file:k.session` reads the password from the file.

### 3.2 Encrypt the session key with Lucilla's public key

```bash
openssl pkeyutl -encrypt -pubin -inkey lucilla.public -in k.session -out k.crypt
```

Only Lucilla's private key can recover `k.session`. `rsautl` printed `deprecated in version 3.0. Use 'pkeyutl' instead`, so `pkeyutl` was used.

### 3.3 Hash and sign

```bash
openssl dgst -sha512 -binary -out file.sha file.txt
openssl pkeyutl -sign -inkey maximus.prive -in file.sha -out file.sign -pkeyopt digest:sha512
```

| File | Size | Content |
|---|---|---|
| `file.sha` | 64 bytes | Raw SHA-512 digest of `file.txt` |
| `file.sign` | 256 bytes | RSA signature (2048-bit key) of the digest |

The first attempt used `openssl dgst -sha512 -out file.sha file.txt` without `-binary`. That writes a text line (`SHA2-512(file.txt)= ...`, 149 bytes), and signing failed with `The non-raw input data length 149 is too long - max supported hashed size is 64`. `-binary` writes only the 64 raw bytes, and `-pkeyopt digest:sha512` tells `pkeyutl` which hash the input is.

### 3.4 Packet sent

`file.aes`, `k.crypt`, `file.sign`, `file.sha`

## 4. Lucilla's process (receiver)

### 4.1 First level: verify the signature (authentication and integrity of the hash)

```bash
openssl pkeyutl -verify -pubin -inkey maximus.public -in file.sha -sigfile file.sign -pkeyopt digest:sha512
```

```
Signature Verified Successfully
```

Handout method (recover the hash from the signature and compare):

```bash
openssl pkeyutl -verifyrecover -pubin -inkey maximus.public -in file.sign -out file.empreinte -pkeyopt digest:sha512
cmp file.empreinte file.sha && echo "signature OK"
```

```
signature OK
```

`cmp` printed nothing before `signature OK`, so `file.empreinte` and `file.sha` are identical. If they differed, the packet would be rejected (loss of integrity or wrong sender).

### 4.2 Second level: decrypt

```bash
openssl pkeyutl -decrypt -inkey lucilla.prive -in k.crypt -out k.session.dec
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -in file.aes -out file.dec.txt -pass file:k.session.dec
```

### 4.3 Final integrity check

```bash
cmp file.txt file.dec.txt && echo "file identical"
openssl dgst -sha512 -binary file.dec.txt | cmp - file.sha && echo "hash matches signed hash"
```

```
file identical
hash matches signed hash
```

The second check recomputes the hash of the file Lucilla actually decrypted and compares it with the hash that Maximus signed. This step is essential: the first-level check only proves that `file.sha` is genuine, not that `file.aes` is the file it was computed from. An attacker could replace `file.aes` and the unsigned `file.sha` text while keeping the old signature, and only this final comparison would catch it.

## 5. Which property comes from which step

| Property | Provided by | Why |
|---|---|---|
| Confidentiality | AES encryption of the file + RSA encryption of `k.session` | Without Lucilla's private key the session key, and so the file, cannot be recovered |
| Integrity | SHA-512 hash compared after decryption | Any change to the file changes the digest completely |
| Authentication | RSA signature with Maximus's private key | Only the holder of that key can produce a signature that verifies with `maximus.public` |

## 6. Issues found in the handout

1. `-k k.session` uses the literal text as password; `-pass file:` reads the file.
2. No `-pbkdf2`/`-iter` triggers the deprecated key derivation warning.
3. `rsautl` is deprecated in OpenSSL 3.x; `pkeyutl` replaces it.
4. Inconsistent file names (`maximus.prive`/`maximus.priv`, `lucilla.pub`/`lucilla.public`), which cause `No such file or directory`.
5. The encrypt command uses `-aes256` but decryption uses `-aes`; they must match.
6. The hash must be written with `-binary` before signing.
7. The handout does not recompute the hash after decryption, which leaves the integrity check incomplete.
8. AES-CBC alone is not authenticated; here the signature (plus the final recompute) is what detects tampering. A mode such as AES-GCM would detect it directly.

## 7. Conclusion

The full chain worked: the signature verified, the session key was recovered with Lucilla's private key, and the decrypted file is byte-identical to the original and matches the signed SHA-512 hash. The scheme achieves confidentiality, integrity and authentication, with the limitation that the sender's public key must itself be trusted (here it was copied directly; in practice a certificate would bind it to an identity).
