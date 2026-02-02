from main import allowed_moves
import sys
import random

def generate_shuffle(length):
    shuffle = []
    previous_move = ""
    for i in range(length):
        move = random.choice(list(allowed_moves))
        while move[0] == previous_move:
            move = random.choice(list(allowed_moves))
        shuffle.append(move)
        previous_move = move[0]
    return " ".join(shuffle)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 bonus_shuffle.py <shuffle_length>")
        sys.exit(1)

    try:
        shuffle_length = int(sys.argv[1])
    except ValueError:
        print("Invalid shuffle length. Please provide a number.")
        sys.exit(1)

    shuffle = generate_shuffle(shuffle_length)
    print(f"Generated shuffle: {shuffle}")