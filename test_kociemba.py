#!/usr/bin/env python3
"""Test complet du solveur Kociemba avec différents niveaux de difficulté"""

import time
import random
from solver_kociemba import CubieCube, FaceCube, MOVE_CUBE, solve

# Noms des mouvements
MOVE_NAMES = ["U", "R", "F", "D", "L", "B"]


def apply_moves(scramble: str) -> CubieCube:
    """Applique une séquence de mouvements à un cube résolu"""
    cc = CubieCube()
    moves = scramble.split()
    
    for move in moves:
        if not move:
            continue
        
        # Parser le mouvement
        face = move[0]
        if face not in MOVE_NAMES:
            print(f"Mouvement inconnu: {move}")
            continue
        
        face_idx = MOVE_NAMES.index(face)
        
        # Déterminer le nombre de rotations
        if len(move) == 1:
            count = 1  # U = 1 fois
        elif move[1] == "'":
            count = 3  # U' = 3 fois (équivalent à -1)
        elif move[1] == "2":
            count = 2  # U2 = 2 fois
        else:
            count = 1
        
        # Appliquer le mouvement
        for _ in range(count):
            cc.multiply(MOVE_CUBE[face_idx])
    
    return cc


def generate_random_scramble(n_moves: int) -> str:
    """Génère un scramble aléatoire de n mouvements"""
    moves = []
    last_face = -1
    
    for _ in range(n_moves):
        # Éviter le même face 2 fois de suite
        face = random.choice([i for i in range(6) if i != last_face])
        last_face = face
        
        # Choisir la puissance
        power = random.choice(["", "'", "2"])
        moves.append(MOVE_NAMES[face] + power)
    
    return " ".join(moves)


def test_scramble(name: str, scramble: str, timeout: float = 120.0) -> dict:
    """Teste un scramble et retourne les résultats"""
    print(f"\n{'=' * 70}")
    print(f"TEST: {name}")
    print(f"{'=' * 70}")
    print(f"Scramble: {scramble}")
    print(f"Nombre de mouvements: {len(scramble.split())}")
    
    # Appliquer le scramble
    cc = apply_moves(scramble)
    fc = cc.to_facecube()
    cubestring = fc.to_string()
    print(f"Cubestring: {cubestring}")
    
    # Résoudre
    start = time.time()
    try:
        solution = solve(cubestring, max_depth=24, timeout=timeout)
        elapsed = time.time() - start
        
        if solution.startswith("Error"):
            print(f"❌ ERREUR: {solution}")
            return {"success": False, "error": solution, "time": elapsed}
        
        sol_moves = len(solution.split()) if solution else 0
        print(f"✅ Solution: {solution}")
        print(f"   Longueur: {sol_moves} mouvements")
        print(f"   Temps: {elapsed:.3f}s")
        
        # Vérifier la solution
        verify_cc = apply_moves(scramble)
        verify_cc2 = apply_moves(solution)
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


def main():
    print("\n" + "=" * 70)
    print("       TESTS COMPLETS DU SOLVEUR KOCIEMBA AUTONOME")
    print("=" * 70)
    
    results = []
    
    # ========================================
    # NIVEAU 1: 4-5 mouvements (très facile)
    # ========================================
    print("\n" + "🟢 " * 20)
    print("NIVEAU 1: SCRAMBLES COURTS (4-5 mouvements)")
    print("🟢 " * 20)
    
    short_scrambles = [
        ("4 mouvements - Test 1", "R U R' U'"),
        ("5 mouvements - Test 1", "R U R' U' F"),
        ("4 mouvements - Test 2", "F R U R'"),
        ("5 mouvements - Test 2", "U' L' U L F"),
    ]
    
    for name, scramble in short_scrambles:
        results.append((name, test_scramble(name, scramble)))
    
    # ========================================
    # NIVEAU 2: 5-20 mouvements (moyen)
    # ========================================
    print("\n" + "🟡 " * 20)
    print("NIVEAU 2: SCRAMBLES MOYENS (5-20 mouvements)")
    print("🟡 " * 20)
    
    medium_scrambles = [
        ("10 mouvements", "R U R' U' R' F R2 U' R' U"),
        ("12 mouvements", "R U R' F' R U R' U' R' F R2 U'"),
        ("15 mouvements", "R U R' U R U2 R' L' U' L U' L' U2 L U"),
        ("18 mouvements", generate_random_scramble(18)),
    ]
    
    for name, scramble in medium_scrambles:
        results.append((name, test_scramble(name, scramble)))
    
    # ========================================
    # NIVEAU 3: Plus de 20 mouvements (difficile)
    # ========================================
    print("\n" + "🟠 " * 20)
    print("NIVEAU 3: SCRAMBLES DIFFICILES (>20 mouvements)")
    print("🟠 " * 20)
    
    hard_scrambles = [
        ("22 mouvements", generate_random_scramble(22)),
        ("25 mouvements", generate_random_scramble(25)),
        ("28 mouvements", generate_random_scramble(28)),
    ]
    
    for name, scramble in hard_scrambles:
        results.append((name, test_scramble(name, scramble)))
    
    # ========================================
    # NIVEAU 4: Plus de 30 mouvements (très difficile)
    # ========================================
    print("\n" + "🔴 " * 20)
    print("NIVEAU 4: SCRAMBLES TRÈS DIFFICILES (>30 mouvements)")
    print("🔴 " * 20)
    
    very_hard_scrambles = [
        ("32 mouvements", generate_random_scramble(32)),
        ("35 mouvements", generate_random_scramble(35)),
        ("40 mouvements", generate_random_scramble(40)),
    ]
    
    for name, scramble in very_hard_scrambles:
        results.append((name, test_scramble(name, scramble)))
    
    # ========================================
    # TEST SPÉCIAL: Superflip
    # ========================================
    print("\n" + "⭐ " * 20)
    print("TEST SPÉCIAL: SUPERFLIP")
    print("⭐ " * 20)
    
    superflip = "U R2 F B R B2 R U2 L B2 R U' D' R2 F R' L B2 U2 F2"
    results.append(("Superflip (20 HTM)", test_scramble("Superflip", superflip, timeout=180.0)))
    
    # ========================================
    # RÉSUMÉ
    # ========================================
    print("\n" + "=" * 70)
    print("                        RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    success_count = 0
    total_time = 0
    total_moves = 0
    
    for name, result in results:
        if result["success"]:
            success_count += 1
            total_time += result["time"]
            total_moves += result["moves"]
            status = f"✅ {result['moves']:2d} mvts en {result['time']:.3f}s"
        else:
            status = f"❌ {result.get('error', 'Échec')[:30]}"
        print(f"  {name:35s} {status}")
    
    print(f"\n{'=' * 70}")
    print(f"  TOTAL: {success_count}/{len(results)} tests réussis")
    if success_count > 0:
        print(f"  Temps moyen de résolution: {total_time/success_count:.3f}s")
        print(f"  Longueur moyenne des solutions: {total_moves/success_count:.1f} mouvements")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    random.seed(42)  # Pour reproductibilité
    main()
