# TP2: Part III. File Encryption and Decryption Using OpenSSL

## 3.1 Objective

Use OpenSSL to encrypt and decrypt a file with AES-256-CBC, and use SHA-256 digests to compare files and detect modification.

## 3.2 Input file

The input file used was `openssl_target.txt` (122 bytes), in place of `plaintext.txt`. The first attempt with `plaintext.txt` failed with `No such file or directory` because that file did not exist in the working directory. It contains non-confidential sample content only: `Confidential information for the cybersecurity laboratory.` The file is 122 bytes rather than the ~60 bytes the text would suggest because PowerShell's `echo >` wrote it as UTF-16LE (2-byte BOM + 2 bytes per character + CRLF). This does not affect the exercise, but it explains why the byte counts and digests differ from those of a plain UTF-8 file.

---

## Task 1: Encrypt with AES-256-CBC

```powershell
openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 -in .\openssl_target.txt -out encrypted.bin
```

OpenSSL prompted twice for the password (`enter` / `Verifying - enter`), so the password was never written on the command line. The output file `encrypted.bin` is **144 bytes**.

### Questions

**7. What does `-aes-256-cbc` specify?**
It selects the cipher: AES (Advanced Encryption Standard) with a 256-bit key, in CBC (Cipher Block Chaining) mode. AES works on 128-bit (16-byte) blocks. In CBC mode each plaintext block is XORed with the previous ciphertext block before encryption, so identical plaintext blocks produce different ciphertext. The first block uses an IV (initialization vector).

**8. What is the purpose of the salt?**
`-salt` generates a random value that is mixed with the password when the key and IV are derived. The same password therefore gives a different key and IV every time. This prevents identical files from producing identical ciphertext, and it defeats precomputed attacks (rainbow tables) against the password. OpenSSL stores the salt in the file header (`Salted__` + 8 bytes), which is why the decryptor does not need to be told it.

**9. What is the role of `-pbkdf2` and `-iter 200000`?**
A password is not a usable key, so a key derivation function turns it into the 256-bit key and IV. `-pbkdf2` selects PBKDF2, a standard and much stronger derivation than the old OpenSSL default (a single MD5 round). `-iter 200000` runs 200,000 hashing iterations, which costs a legitimate user a fraction of a second but makes each password guess in a brute-force or dictionary attack 200,000 times more expensive. Decryption must use the same `-pbkdf2` and `-iter` values, otherwise a different key is derived.

**10. Why must the password be kept confidential?**
The password is the only secret. AES and PBKDF2 are public, so anyone who knows the password can derive the same key and decrypt the file. A weak or leaked password makes the 256-bit key irrelevant. Putting it on the command line is also unsafe because it can end up in shell history and in the process list.

**11. Why is `encrypted.bin` not expected to be readable as ordinary text?**
Good ciphertext is statistically indistinguishable from random bytes, so it contains arbitrary byte values (not printable characters). It also begins with the binary header `Salted__` followed by the random salt. The observed size also fits the format: 16 bytes of header + 122 bytes of data padded (PKCS#7) up to the next multiple of 16 (128) = **144 bytes**.

### Observations
- Encryption succeeded after supplying the correct file name; the output is 144 bytes.
- Size check: 16 (header) + 128 (122 padded to a 16-byte multiple) = 144, as expected for AES-CBC with salt.

---

## Task 2: Decrypt the file

```powershell
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -in encrypted.bin -out decrypted.txt
```

Using the same password, `decrypted.txt` was produced with a size of **122 bytes**, identical to `openssl_target.txt`.

### Comparison

```powershell
cmp .\openssl_target.txt .\decrypted.txt
```

`cmp` printed **no output**, which means the two files are byte-for-byte identical. (On Windows without `cmp`, `fc /b` is the equivalent.)

### Incorrect-password test

```powershell
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -in encrypted.bin -out false_decrypted.txt
```

(a wrong password was entered)

```
bad decrypt
error:1C800064:Provider routines:ossl_cipher_unpadblock:bad decrypt
```

**Observation:** OpenSSL reported `bad decrypt`. A wrong password derives a wrong key, so the decrypted last block does not end with valid padding, and OpenSSL detects that. Even so, `false_decrypted.txt` was created and contains unreadable binary garbage (`cat` shows random symbols instead of the sentence). Its digest is completely different from the original:

| File | SHA-256 |
|---|---|
| `false_decrypted.txt` (wrong password) | `8ed41c404f70c1b6630dc83d92665171f9c3f4a65d07ad83822c86fad8c0095a` |
| `openssl_target.txt` (original) | `f7d55d4e3e0e0fb453db7821a08e635c41270d06821219479d95eb1008ffa788` |

The output file must therefore never be trusted after a `bad decrypt` error.

**Important caveat:** this error is not a reliable integrity check. CBC provides no authentication, so with a wrong key the final block happens to look like valid padding with probability roughly 1 in 256, and in that case OpenSSL succeeds without any error and writes garbage. A command that completes is therefore not proof that the content is correct. The only real check is comparing the result with the original (`cmp` or a SHA-256 digest).

### Security note
CBC mode is not authenticated encryption: it detects neither tampering with `encrypted.bin` nor a wrong password reliably. Real applications should use an authenticated mode such as AES-GCM (or ChaCha20-Poly1305).

---

## Task 3: Calculate SHA-256 digests

```powershell
openssl dgst -sha256 .\openssl_target.txt
openssl dgst -sha256 .\decrypted.txt
```

**12. Digests**

| File | SHA-256 |
|---|---|
| `openssl_target.txt` (original) | `f7d55d4e3e0e0fb453db7821a08e635c41270d06821219479d95eb1008ffa788` |
| `decrypted.txt` (recovered) | `f7d55d4e3e0e0fb453db7821a08e635c41270d06821219479d95eb1008ffa788` |

**13. Comparison:** the two digests **match exactly**, which agrees with the silent result of `cmp`.

**14. Why matching digests support "identical files", but do not prove who created the file**
SHA-256 is collision-resistant: finding two different inputs with the same digest is computationally infeasible, and changing even one bit of the input changes the digest completely (avalanche effect). So equal digests give very strong evidence that the contents are the same. However, a digest involves no secret and no identity. Anyone can compute the SHA-256 of any file, including an attacker who modifies a file and publishes the new digest next to it. A digest therefore shows *integrity* ("this content is the same") but not *authenticity* or *origin* ("who produced it"). Proving the author requires a MAC (HMAC, shared secret) or a digital signature (private key).

---

## Task 4: Detect a modification

**15. Copy the original.** A second file, `plain_text.txt`, was created with the same sentence as the original.

**16. Modify one character.** In the copy, one letter was changed: `Confidential` became `Cunfidential` (`o` → `u`).

```
openssl_target.txt : Confidential information for the cybersecurity laboratory.
plain_text.txt     : Cunfidential information for the cybersecurity laboratory.
```

**17. Digest of the modified file**

```powershell
openssl dgst -sha256 plain_text.txt
```

| File | SHA-256 |
|---|---|
| `openssl_target.txt` (original) | `f7d55d4e3e0e0fb453db7821a08e635c41270d06821219479d95eb1008ffa788` |
| `plain_text.txt` (one character changed) | `02cbf85a7f2015590277209d5a0c34548f733f635336b677472b65202cda816c` |

**18. Explanation of the difference**
Both files have the same size (122 bytes) and differ by a single character, yet the digests share no visible similarity (`f7d55d4e…` vs `02cbf85a…`). SHA-256 has the avalanche property: a one-bit change in the input flips about half of the output bits unpredictably, so the new digest looks unrelated to the original rather than "slightly different". Since identical files always give identical digests, a different digest proves the file was modified. This is how integrity checking works: keep the original digest, recompute later, and any change, accidental or malicious, shows up as a mismatch. The same effect appears in the wrong-password test, where the garbage output has a completely different digest again.

---

## Conclusion
- AES-256-CBC with salt and PBKDF2 (200,000 iterations) encrypted and decrypted the file correctly; the recovered file matches the original (`cmp` silent, identical SHA-256 digests).
- A wrong password produced `bad decrypt`, but this is only a padding error and not a guarantee, so correctness must be verified by comparing against the original.
- SHA-256 detects any modification and verifies integrity but cannot prove authorship; CBC alone gives confidentiality without authentication, so authenticated modes (AES-GCM) or signatures/MACs are needed in practice.
