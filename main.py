import sys

allowed_moves = {"R","R'","R2","L","L'","L2","U","U'","U2",
           "D","D'","D2","F","F'","F2","B","B'","B2"}

cube = [
    "W","W","W","W","W","W","W","W","W",  # U
    "R","R","R","R","R","R","R","R","R",  # R
    "G","G","G","G","G","G","G","G","G",  # F
    "Y","Y","Y","Y","Y","Y","Y","Y","Y",  # D
    "O","O","O","O","O","O","O","O","O",  # L
    "B","B","B","B","B","B","B","B","B",  # B
]

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 main.py \"R F B2 F'\"")
        sys.exit(1)
    shuffle = sys.argv[1]
    invalid_moves = [move for move in shuffle.split() if move not in allowed_moves]
    if invalid_moves:
        print(f"Invalid moves found: {', '.join(invalid_moves)}")
        sys.exit(1)

if __name__ == "__main__":
    main()