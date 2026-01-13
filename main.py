import sys

allowed_moves = {"R","R'","R2","L","L'","L2","U","U'","U2",
           "D","D'","D2","F","F'","F2","B","B'","B2"}

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 main.py \"R F B2 F'\"")
        sys.exit(1)
    shuffle = sys.argv[1]
    if [move for move in shuffle.split() if move not in allowed_moves] != []:
        print(f"Invalid move: {move}")
        sys.exit(1)

if __name__ == "__main__":
    main()