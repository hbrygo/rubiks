#!/usr/bin/env python3
"""
Wrapper pour le solveur Thistlethwaite.
Usage: python soluce.py "SCRAMBLE"
"""

import sys
import time
from thistlethwaite import Cube, solver

def main():
    if len(sys.argv) != 2:
        print("Usage: python soluce.py \"SCRAMBLE\"")
        print("Exemple: python soluce.py \"R U R' U'\"")
        sys.exit(0)

    scramble = sys.argv[1]
    # Normaliser les apostrophes
    scramble = scramble.replace("'", "'").replace("'", "'").replace("`", "'")
    
    cube = Cube()
    cube.scramble(scramble)
    
    start_time = time.time()
    solution = solver(cube)
    end_time = time.time()
    
    # Compter le nombre de mouvements
    num_moves = len(solution.split()) if solution.strip() else 0
    elapsed_time = end_time - start_time
    
    print(solution)
    print(f"Nombre de coups : {num_moves} / Temps : {elapsed_time:.2f}s", file=sys.stderr)

if __name__ == "__main__":
    main()
