from math import gcd
import argparse


def alfine_encrypt(string: str, key: tuple[int, int]) -> str:
    a, b = key

    if gcd(a, 26) != 1:
        raise ValueError("The key is invalid")

    res = []

    for ch in string:
        if ch.isupper():
            x = ord(ch) - ord('A')
            res.append(chr((a * x + b) % 26 + ord('A')))

        elif ch.islower():
            x = ord(ch) - ord('a')
            res.append(chr((a * x + b) % 26 + ord('a')))

        else:
            res.append(ch)

    return "".join(res)


def alfine_decrypt(string: str, key: tuple[int, int]) -> str:
    a, b = key

    if gcd(a, 26) != 1:
        raise ValueError("The key is invalid")

    a_inv = pow(a, -1, 26)
    res = []

    for ch in string:
        if ch.isupper():
            y = ord(ch) - ord('A')
            res.append(chr((a_inv * (y - b)) % 26 + ord('A')))

        elif ch.islower():
            y = ord(ch) - ord('a')
            res.append(chr((a_inv * (y - b)) % 26 + ord('a')))

        else:
            res.append(ch)

    return "".join(res)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Affine cipher encryption and decryption")

    parser.add_argument("--input", required=True, help="Input plaintext file")
    parser.add_argument("--ciphertext", default="ciphertext_affine.txt",
                        help="Output file for ciphertext")
    parser.add_argument("--recovered", default="recovered_plaintext.txt",
                        help="Output file for recovered plaintext")
    parser.add_argument("--a", type=int, required=True,
                        help="First affine key value")
    parser.add_argument("--b", type=int, required=True,
                        help="Second affine key value")

    args = parser.parse_args()
    key = (args.a, args.b)

  
    with open(args.input, "r", encoding="utf-8") as file:
        plaintext = file.read()


    ciphertext = alfine_encrypt(plaintext, key)


    with open(args.ciphertext, "w", encoding="utf-8") as file:
        file.write(ciphertext)

    recovered = alfine_decrypt(ciphertext, key)


    with open(args.recovered, "w", encoding="utf-8") as file:
        file.write(recovered)

    print(f"Ciphertext saved to: {args.ciphertext}")
    print(f"Recovered plaintext saved to: {args.recovered}")
    print(f"Recovery successful: {recovered == plaintext}")