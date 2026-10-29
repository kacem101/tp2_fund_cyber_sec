# TP2: Classical Cryptography

Module: Fundamentals of Cybersecurity, National School of Cyber Security (NSCS)

Index of the files for each part of the practical work. All links are relative, so they work on GitHub and in a local clone.

## Part I: Caesar Cipher

| Item | File |
|---|---|
| Implementation | [fund.py](fund.py) |
| Input file | [file.txt](file.txt) |
| Encrypted output | [ceasar_output.txt](ceasar_output.txt) |

## Part II: Affine Cipher and Hill Cipher

### Affine cipher

| Item | File |
|---|---|
| Implementation | [alfine.py](alfine.py) |
| Report (tasks 1-6, tests, gcd explanation) | [affine_report.md](affine_report.md) |

### Hill cipher

| Item | File |
|---|---|
| Implementation | [hilll.py](hilll.py) |
| Output | [hill_out.txt](hill_out.txt) |

## Part III: File Encryption and Decryption Using OpenSSL

| Item | File |
|---|---|
| Report (questions 7-18, observations) | [part3_openssl_report.md](part3_openssl_report.md) |
| Input file (original) | [openssl_target.txt](openssl_target.txt) |
| Task 1: encrypted file (AES-256-CBC) | [encrypted.bin](encrypted.bin) |
| Task 2: decrypted file (correct password) | [decrypted.txt](decrypted.txt) |
| Task 2: output with wrong password | [false_decrypted.txt](false_decrypted.txt) |
| Task 4: file with one character changed | [plain_text.txt](plain_text.txt) |

## Part IV: RSA (authentication, integrity, confidentiality)

| Item | File |
|---|---|
| Report (hybrid scheme, signature, verification, handout issues) | [part4_rsa_report.md](part4_rsa_report.md) |
| Working directory (keys, packet, recovered files) | [part4/](part4) |

The packet is `file.aes`, `k.crypt`, `file.sign` and `file.sha`. Private keys (`*.prive`) must never be committed.

## Part V: Various Operations

### Task 4: Hybrid encryption

| Item | File |
|---|---|
| Report (OpenSSL CLI and Python versions, comparison) | [part5_hybrid_report.md](part5_hybrid_report.md) |
| OpenSSL working directory (message, encrypted key, IV) | [part5/](part5) |
| Python sender (Alice) | [part5/alice.py](part5/alice.py) |
| Python receiver (Bob) | [part5/bob.py](part5/bob.py) |

### Tasks 1-3: strong/weak ciphers, Base64 and MD5, CAST5

Not added yet.

## Project files

| File | Purpose |
|---|---|
| [src/tp2_fund_cyber_sec](src/tp2_fund_cyber_sec) | Python package directory |
| [pyproject.toml](pyproject.toml) | Project configuration (uv) |
| [uv.lock](uv.lock) | Locked dependencies |
| [.python-version](.python-version) | Python version |
| [.gitignore](.gitignore) | Git ignore rules |