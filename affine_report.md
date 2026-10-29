# Affine Cipher: Implementation Report

## 1. Objective

Implement the Affine cipher for text files, covering encryption, decryption, key validation, and modular inverse computation. Save the ciphertext to `ciphertext_affine.txt` and the recovered plaintext to a separate file. Test valid and invalid keys, and explain why `gcd(a, 26) = 1` is required.

## 2. Background

The Affine cipher is a monoalphabetic substitution cipher. Each letter is mapped to a number `x` (A=0, ..., Z=25) and encrypted with:

```
E(x) = (a·x + b) mod 26
D(y) = a⁻¹ · (y − b) mod 26
```

- `a` is the multiplicative key, `b` is the additive (shift) key.
- `a⁻¹` is the modular inverse of `a` mod 26, i.e. `a · a⁻¹ ≡ 1 (mod 26)`.
- With `a = 1` it reduces to a Caesar cipher.

## 3. Implementation

### 3.1 Design

| Requirement | How it is implemented |
|---|---|
| Encrypt / decrypt a text file | `affine_encrypt()` and `affine_decrypt()`, driven by `argparse` in `main` |
| Validate both key parameters | `validate_key()`: `a` must satisfy `gcd(a, 26) = 1`, `b` must be an integer in `0..25` |
| Modular inverse of `a` | `pow(a, -1, 26)` (Python 3.8+), computed only after validation passes |
| Output files | Ciphertext → `ciphertext_affine.txt`, recovered plaintext → `recovered_plaintext.txt` (both overridable by CLI flags) |
| Preserve formatting | Case is kept, non-letters (digits, spaces, punctuation, newlines) pass through unchanged |

### 3.2 Source code

```python
from math import gcd
import argparse


def validate_key(key: tuple[int, int]) -> None:
    a, b = key
    if not isinstance(a, int) or not isinstance(b, int):
        raise ValueError("Both key parameters must be integers")
    if gcd(a, 26) != 1:
        raise ValueError(f"Invalid a = {a}: gcd({a}, 26) = {gcd(a, 26)}, must be 1")
    if not 0 <= b <= 25:
        raise ValueError(f"Invalid b = {b}: must be in the range 0..25")


def affine_encrypt(string: str, key: tuple[int, int]) -> str:
    validate_key(key)
    a, b = key
    res = []
    for ch in string:
        if ch.isascii() and ch.isupper():
            x = ord(ch) - ord('A')
            res.append(chr((a * x + b) % 26 + ord('A')))
        elif ch.isascii() and ch.islower():
            x = ord(ch) - ord('a')
            res.append(chr((a * x + b) % 26 + ord('a')))
        else:
            res.append(ch)
    return "".join(res)


def affine_decrypt(string: str, key: tuple[int, int]) -> str:
    validate_key(key)
    a, b = key
    a_inv = pow(a, -1, 26)
    res = []
    for ch in string:
        if ch.isascii() and ch.isupper():
            y = ord(ch) - ord('A')
            res.append(chr((a_inv * (y - b)) % 26 + ord('A')))
        elif ch.isascii() and ch.islower():
            y = ord(ch) - ord('a')
            res.append(chr((a_inv * (y - b)) % 26 + ord('a')))
        else:
            res.append(ch)
    return "".join(res)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Affine cipher encryption and decryption")
    parser.add_argument("--input", required=True, help="Input plaintext file")
    parser.add_argument("--ciphertext", default="ciphertext_affine.txt", help="Output file for ciphertext")
    parser.add_argument("--recovered", default="recovered_plaintext.txt", help="Output file for recovered plaintext")
    parser.add_argument("--a", type=int, required=True, help="First affine key value")
    parser.add_argument("--b", type=int, required=True, help="Second affine key value")
    args = parser.parse_args()
    key = (args.a, args.b)

    try:
        validate_key(key)
    except ValueError as e:
        parser.error(str(e))

    with open(args.input, "r", encoding="utf-8") as f:
        plaintext = f.read()

    ciphertext = affine_encrypt(plaintext, key)
    with open(args.ciphertext, "w", encoding="utf-8") as f:
        f.write(ciphertext)

    recovered = affine_decrypt(ciphertext, key)
    with open(args.recovered, "w", encoding="utf-8") as f:
        f.write(recovered)

    print(f"Ciphertext saved to: {args.ciphertext}")
    print(f"Recovered plaintext saved to: {args.recovered}")
    print(f"Recovery successful: {recovered == plaintext}")
```

### 3.3 Usage

```bash
python affine.py --input plain.txt --a 5 --b 8
python affine.py --input plain.txt --a 7 --b 3 --ciphertext out.txt --recovered back.txt
```

## 4. Key validation

**Parameter `a`:** must be coprime with 26 so the cipher is invertible (see section 6). The valid values are the 12 integers below 26 that share no factor with 26 (2 or 13):

```
a ∈ {1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25}
```

**Parameter `b`:** must be an integer in `0..25`. Any integer would technically work since the result is reduced mod 26, but values outside the range are equivalent to one inside it, so rejecting them avoids ambiguous keys.

### Modular inverses mod 26

| a | a⁻¹ | a · a⁻¹ mod 26 |
|---|---|---|
| 1 | 1 | 1 |
| 3 | 9 | 1 |
| 5 | 21 | 1 |
| 7 | 15 | 1 |
| 9 | 3 | 1 |
| 11 | 19 | 1 |
| 15 | 7 | 1 |
| 17 | 23 | 1 |
| 19 | 11 | 1 |
| 21 | 5 | 1 |
| 23 | 17 | 1 |
| 25 | 25 | 1 |

## 5. Test results

**Test input (`plain.txt`):**

```
Hello, World! The quick brown fox jumps over the lazy dog.
Cybersecurity 101: Affine Cipher Test.
```

### 5.1 Valid key pairs

| Key (a, b) | a⁻¹ | Ciphertext (first line) | Recovered == original |
|---|---|---|---|
| (5, 8) | 21 | `Rclla, Oaplx! Zrc kewsg npaov hat beqfu ajcp zrc lidy xam.` | True |
| (7, 3) | 15 | `Afccx, Bxscy! Gaf lnhrv ksxbq mxi onjez xufs gaf cdwp yxt.` | True |
| (17, 20) | 23 | `Jkzzy, Eyxzt! Fjk gwaci lxyeh byv rwqpo ynkx fjk zudm tys.` | True |

Second line of the ciphertext for each key:

| Key | Second line |
|---|---|
| (5, 8) | `Syncpucsepwzy 101: Ihhwvc Swfrcp Zcuz.` |
| (7, 3) | `Rpkfszfrnshgp 101: Dmmhqf Rheafs Gfzg.` |
| (17, 20) | `Cmlkxokcwxafm 101: Ubbahk Capjkx Fkof.` |

Digits, spaces, punctuation and capitalization are preserved in every case.

### 5.2 Invalid values

| Key (a, b) | Reason | Program output |
|---|---|---|
| (2, 5) | gcd(2, 26) = 2 | `Invalid a = 2: gcd(2, 26) = 2, must be 1` |
| (13, 7) | gcd(13, 26) = 13 | `Invalid a = 13: gcd(13, 26) = 13, must be 1` |
| (0, 3) | gcd(0, 26) = 26 | `Invalid a = 0: gcd(0, 26) = 26, must be 1` |
| (5, 26) | b out of range | `Invalid b = 26: must be in the range 0..25` |

In all invalid cases the program exits with an error **before** creating any output file.

## 6. Why gcd(a, 26) = 1 is necessary

Encryption is a function `E: Z₂₆ → Z₂₆`. For decryption to exist, `E` must be **one-to-one (bijective)**, meaning every ciphertext letter corresponds to exactly one plaintext letter.

**Algebraic argument.** To decrypt we solve `a·x ≡ (y − b) (mod 26)` for `x`. This needs `a⁻¹`, which exists **if and only if** `gcd(a, 26) = 1`. If `g = gcd(a, 26) > 1`, then `a·x` is always a multiple of `g` modulo 26, so only `26/g` of the 26 residues can ever be produced and the equation has either no solution or `g` solutions.

**Concrete example, a = 2.** Since `gcd(2, 26) = 2`, the mapping `x → 2x mod 26` gives:

```
x:     0  1  2  3  ...  12  13  14  15  ...  25
2x:    0  2  4  6  ...  24   0   2   4  ...  24
```

- `A` (0) and `N` (13) both map to `A`, `B` (1) and `O` (14) both map to `C`, and so on. Every pair `(x, x + 13)` collides.
- Only the 13 even values are ever produced; odd ciphertext letters never appear.
- Given a ciphertext letter, there are two possible plaintext letters, so the original text **cannot be uniquely recovered**.

**Concrete example, a = 13.** `x → 13x mod 26` produces only `0` or `13`: every letter collapses to just two outputs (A or N), which destroys almost all information.

**Why 26 matters.** `26 = 2 × 13`, so any `a` sharing the factor 2 or 13 with 26 fails. The number of valid values of `a` is Euler's totient `φ(26) = φ(2)·φ(13) = 1 × 12 = 12`, which gives a total keyspace of `12 × 26 = 312` keys. (This is tiny, so the cipher is trivially broken by brute force or frequency analysis; it is for learning only.)

## 7. Conclusion

- The implementation encrypts and decrypts text files correctly and preserves non-alphabetic characters and case.
- Both key parameters are validated, with explicit error messages, before any file is written.
- The modular inverse is computed with `pow(a, -1, 26)` after validation.
- Three valid keys (5,8), (7,3), (17,20) round-trip successfully; invalid `a` values 2, 13 and 0 and invalid `b` value 26 are rejected.
- The condition `gcd(a, 26) = 1` is exactly the condition for `a` to have an inverse mod 26, which makes encryption a bijection and decryption possible.

## 8. Notes on the original code

The submitted script only validated `a`, not `b`, so requirement 2 was not fully met. This version adds `validate_key()` to check both, moves validation into a single function used by encrypt, decrypt and the CLI, and renames `alfine_*` to `affine_*`. Case checks also use `ch.isascii()` so non-ASCII letters (e.g. `é`) are passed through instead of being mapped to wrong characters.
