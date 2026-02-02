import sys
import time
import random
import argparse
from solver_kociemba import CubieCube, MOVE_CUBE, solve
from solver_kociemba_fast import solve_fast
from test_kociemba import apply_moves, MOVE_NAMES

allowed_moves = {"R","R'","R2","L","L'","L2","U","U'","U2",
           "D","D'","D2","F","F'","F2","B","B'","B2"}

def main():
    parser = argparse.ArgumentParser(description="Rubik's Cube Solver")
    parser.add_argument("shuffle", help="Séquence de mélange (ex: \"R F B2 F'\")")
    parser.add_argument("--fast", action="store_true", 
                        help="Mode rapide: première solution trouvée (non-optimale)")
    parser.add_argument("--optimal", action="store_true", 
                        help="Mode optimal: solution la plus courte (défaut)")
    args = parser.parse_args()
    
    shuffle = args.shuffle
    use_fast = args.fast and not args.optimal  # --optimal a priorité
    invalid_moves = [move for move in shuffle.split() if move not in allowed_moves]
    if invalid_moves:
        print(f"Invalid moves found: {', '.join(invalid_moves)}")
        sys.exit(1)

    print(f"Shuffle: {shuffle}")
    print(f"Mode: {'FAST (première solution)' if use_fast else 'OPTIMAL (solution la plus courte)'}")
    cc = apply_moves(shuffle)
    fc = cc.to_facecube()
    cubestring = fc.to_string()
    print(f"Cubestring: {cubestring}")
    
    # Résoudre
    start = time.time()
    try:
        if use_fast:
            solution = solve_fast(cubestring, max_depth=50, timeout=3)
        else:
            solution = solve(cubestring, max_depth=30, timeout=15)
        elapsed = time.time() - start
        
        if solution.startswith("Error"):
            print(f"❌ ERREUR: {solution}")
            return {"success": False, "error": solution, "time": elapsed}
        
        sol_moves = len(solution.split()) if solution else 0
        print(f"✅ Solution: {solution}")
        print(f"   Longueur: {sol_moves} mouvements")
        print(f"   Temps: {elapsed:.3f}s")
        
        # Vérifier la solution
        verify_cc = apply_moves(shuffle)
        # Appliquer la solution au cube scramblé
        for move in solution.split():
            if not move:
                continue
            face = move[0]
            face_idx = MOVE_NAMES.index(face)
            count = 1 if len(move) == 1 else (3 if move[1] == "'" else 2)
            for _ in range(count):
                verify_cc.multiply(MOVE_CUBE[face_idx])
        
        # Vérifier si résolu
        verify_fc = verify_cc.to_facecube()
        verify_str = verify_fc.to_string()
        solved_str = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
        
        if verify_str == solved_str:
            print(f"   ✓ Solution vérifiée correcte!")
        else:
            print(f"   ⚠ Solution non vérifiée (résultat: {verify_str})")
        
        return {"success": True, "solution": solution, "moves": sol_moves, "time": elapsed}
        
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ EXCEPTION: {e}")
        return {"success": False, "error": str(e), "time": elapsed}

if __name__ == "__main__":
    main()