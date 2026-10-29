import argparse
import math
import numpy


def to_nums(text: str) -> list[int]:
    return [ord(c) - ord('a') for c in text.lower() if c.isalpha()]


def to_text(nums) -> str:
    return "".join(chr(int(n) + ord('a')) for n in nums)


def inverse_key(matrix: numpy.ndarray) -> numpy.ndarray:
    """Inverse of a 2x2 matrix mod 26."""
    a, b = matrix[0]
    c, d = matrix[1]
    det = int(a * d - b * c) % 26

    if math.gcd(det, 26) != 1:
        raise ValueError(
            f"Key not invertible mod 26 (det = {det}, gcd(det, 26) = {math.gcd(det, 26)})"
        )

    det_inv = pow(det, -1, 26)
    adjugate = numpy.array([[d, -b], [-c, a]])
    return (det_inv * adjugate) % 26


def hill(string: str, matrix: numpy.ndarray) -> str:
    nums = to_nums(string)
    if len(nums) % 2 != 0:
        nums.append(ord('x') - ord('a'))  # pad with 'x'

    vect = numpy.array(nums, dtype=int).reshape(-1, 2)
    res = []
    for vec in vect:
        res.extend(matrix @ vec % 26)
    return to_text(res)


def hill_decrypt(string: str, matrix: numpy.ndarray) -> str:
    return hill(string, inverse_key(matrix))


def main():
    parser = argparse.ArgumentParser(description="Hill cipher (2x2)")
    parser.add_argument("mode", choices=["encrypt", "decrypt"])
    parser.add_argument("text", help="text to process")
    parser.add_argument("-k", "--key", nargs=4, type=int, default=[3, 3, 2, 5],
                        metavar=("A", "B", "C", "D"),
                        help="2x2 key as a b c d (row-major), default: 3 3 2 5")
    args = parser.parse_args()

    key = numpy.array(args.key).reshape(2, 2)

    try:
        if args.mode == "encrypt":
            print(hill(args.text, key))
        else:
            print(hill_decrypt(args.text, key))
    except ValueError as e:
        parser.error(str(e))


if __name__ == "__main__":
    main()