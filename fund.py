import argparse
import json


def ceasar(string:str,key:int) -> str:
    result =[]
    for ch in string :
        if ch.isupper():
            shifted = chr((ord(ch)-ord('A')+key)%26 + ord('A'))
            result.append(shifted)
        elif ch.islower():
            shifted = chr((ord(ch)-ord('a')+key)%26 + ord('a'))
            result.append(shifted)
        else:
            result.append(ch)
    return "".join(result)
def derypt(string:str)->list[str]:
    res =[]
    for i in range(26):
        res.append(ceasar(string,i))
    return res
LETTER_SCORES = {
    # Uppercase
    'E': 26, 'S': 25, 'A': 24, 'N': 23, 'T': 22,
    'I': 21, 'R': 20, 'U': 19, 'L': 18, 'O': 17,
    'D': 16, 'C': 15, 'P': 14, 'M': 13, 'Q': 12,
    'V': 11, 'G': 10, 'F': 9,  'B': 8,  'H': 7,
    'X': 6,  'Y': 5,  'J': 4,  'Z': 3,  'K': 2,
    'W': 1,
    
    # Lowercase
    'e': 26, 's': 25, 'a': 24, 'n': 23, 't': 22,
    'i': 21, 'r': 20, 'u': 19, 'l': 18, 'o': 17,
    'd': 16, 'c': 15, 'p': 14, 'm': 13, 'q': 12,
    'v': 11, 'g': 10, 'f': 9,  'b': 8,  'h': 7,
    'x': 6,  'y': 5,  'j': 4,  'z': 3,  'k': 2,
    'w': 1
}

def score_text(text: str) -> int:
    return sum(LETTER_SCORES.get(ch, 0) for ch in text)
def sort_text(the_list : list[str]) ->list[tuple[str,int]]:
    res =[]
    for i in the_list:
        res.append((i,score_text(i)))
    res.sort(key=lambda x: x[1], reverse=True)
    return res
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Caesar cipher tool")
    parser.add_argument(
        "--key",
        type=int,
        required=True,
        help="Caesar cipher shift key"
    )
    args = parser.parse_args()

    with open("file.txt", "r", encoding="utf-8") as fl:
        string = fl.read()

    print("\nEncrypted text:")
    print(ceasar(string, args.key))

    print("\nAll possible decryptions:")
    print((derypt(string)))
    
    print("\nAll possible decryptions sorted :")
    print(sort_text(derypt(ceasar( string,args.key))))