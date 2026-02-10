#!/usr/bin/env python3
"""
Test de comparaison des algorithmes Kociemba (Optimal vs Fast)
par catégories de taille de shuffle.

Catégories:
- Facile: moins de 5 coups
- Moyen: entre 5 et 20 coups  
- Difficile: plus de 20 coups
- Très difficile: plus de 30 coups
"""

import random
import time
import argparse

# Import des deux solvers
from solver_kociemba import solve as solve_optimal
from solver_kociemba import CubieCube, MOVE_CUBE
from solver_kociemba_fast import solve_fast

# Mouvements possibles
MOVES = ["U", "U'", "U2", "D", "D'", "D2", 
         "R", "R'", "R2", "L", "L'", "L2",
         "F", "F'", "F2", "B", "B'", "B2"]

def generate_shuffle(num_moves):
    """Génère un shuffle aléatoire de num_moves coups."""
    shuffle = []
    last_face = None
    
    for _ in range(num_moves):
        # Éviter de répéter la même face
        available = [m for m in MOVES if m[0] != last_face]
        move = random.choice(available)
        shuffle.append(move)
        last_face = move[0]
    
    return " ".join(shuffle)

MOVE_INDEX = {"U": 0, "R": 1, "F": 2, "D": 3, "L": 4, "B": 5}

def _apply_move(cube, move):
    """Applique un mouvement (ex: U, U2, U') au CubieCube."""
    if not move:
        return
    face = move[0]
    axis = MOVE_INDEX.get(face)
    if axis is None:
        return
    suffix = move[1:] if len(move) > 1 else ""
    if suffix == "2":
        turns = 2
    elif suffix == "'":
        turns = 3
    else:
        turns = 1
    for _ in range(turns):
        cube.multiply(MOVE_CUBE[axis])

def get_cubestring(shuffle):
    """Applique le shuffle et retourne le cubestring."""
    cc = CubieCube()
    if shuffle:
        for mv in shuffle.split():
            _apply_move(cc, mv)
    fc = cc.to_facecube()
    return fc.to_string()

def test_single(cubestring, timeout_optimal=30.0, timeout_fast=3.0):
    """
    Teste les deux algorithmes sur un même cubestring.
    
    Returns:
        dict avec les résultats
    """
    results = {}
    
    # Test OPTIMAL
    t_start = time.time()
    try:
        sol_optimal = solve_optimal(cubestring, max_depth=25, timeout=timeout_optimal)
        elapsed_optimal = time.time() - t_start
        if sol_optimal and not sol_optimal.startswith("Error"):
            moves_optimal = len(sol_optimal.split()) if sol_optimal.strip() else 0
            results['optimal'] = {
                'solution': sol_optimal,
                'moves': moves_optimal,
                'time': elapsed_optimal,
                'success': True
            }
        else:
            results['optimal'] = {
                'solution': sol_optimal,
                'moves': -1,
                'time': elapsed_optimal,
                'success': False
            }
    except Exception as e:
        results['optimal'] = {
            'solution': str(e),
            'moves': -1,
            'time': time.time() - t_start,
            'success': False
        }
    
    # Test FAST
    t_start = time.time()
    try:
        sol_fast = solve_fast(cubestring, max_depth=50, timeout=timeout_fast, timeout_per_depth=0.1)
        elapsed_fast = time.time() - t_start
        if sol_fast and not sol_fast.startswith("Error"):
            moves_fast = len(sol_fast.split()) if sol_fast.strip() else 0
            results['fast'] = {
                'solution': sol_fast,
                'moves': moves_fast,
                'time': elapsed_fast,
                'success': True
            }
        else:
            results['fast'] = {
                'solution': sol_fast,
                'moves': -1,
                'time': elapsed_fast,
                'success': False
            }
    except Exception as e:
        results['fast'] = {
            'solution': str(e),
            'moves': -1,
            'time': time.time() - t_start,
            'success': False
        }
    
    return results

def run_category_tests(category_name, shuffle_sizes, num_tests, timeout_optimal, timeout_fast):
    """
    Exécute les tests pour une catégorie de shuffles.
    
    Args:
        category_name: Nom de la catégorie
        shuffle_sizes: Liste ou range des tailles de shuffle possibles
        num_tests: Nombre de tests à effectuer
        timeout_optimal: Timeout pour l'algo optimal
        timeout_fast: Timeout pour l'algo fast
    
    Returns:
        dict avec les statistiques
    """
    print(f"\n{'='*70}")
    print(f"CATÉGORIE: {category_name}")
    print(f"{'='*70}")
    
    stats = {
        'optimal': {'times': [], 'moves': [], 'success': 0, 'fail': 0},
        'fast': {'times': [], 'moves': [], 'success': 0, 'fail': 0}
    }
    
    for i in range(num_tests):
        # Choisir une taille aléatoire dans la plage
        if isinstance(shuffle_sizes, range):
            size = random.choice(list(shuffle_sizes))
        else:
            size = shuffle_sizes
        
        shuffle = generate_shuffle(size)
        cubestring = get_cubestring(shuffle)
        
        print(f"\n[Test {i+1}/{num_tests}] Shuffle ({size} coups): {shuffle[:50]}{'...' if len(shuffle) > 50 else ''}")
        
        results = test_single(cubestring, timeout_optimal, timeout_fast)
        
        # Affichage des résultats
        for algo in ['optimal', 'fast']:
            r = results[algo]
            if r['success']:
                stats[algo]['times'].append(r['time'])
                stats[algo]['moves'].append(r['moves'])
                stats[algo]['success'] += 1
                status = f"✓ {r['moves']} coups en {r['time']:.3f}s"
            else:
                stats[algo]['fail'] += 1
                status = f"✗ ÉCHEC ({r['solution'][:30]}...)" if len(str(r['solution'])) > 30 else f"✗ ÉCHEC ({r['solution']})"
            
            algo_name = "OPTIMAL" if algo == 'optimal' else "FAST   "
            print(f"  {algo_name}: {status}")
    
    return stats

def print_summary(category_name, stats):
    """Affiche le résumé des statistiques pour une catégorie."""
    print(f"\n{'-'*50}")
    print(f"RÉSUMÉ: {category_name}")
    print(f"{'-'*50}")
    
    for algo in ['optimal', 'fast']:
        algo_name = "OPTIMAL" if algo == 'optimal' else "FAST"
        s = stats[algo]
        
        total = s['success'] + s['fail']
        success_rate = (s['success'] / total * 100) if total > 0 else 0
        
        if s['times']:
            avg_time = sum(s['times']) / len(s['times'])
            min_time = min(s['times'])
            max_time = max(s['times'])
        else:
            avg_time = min_time = max_time = 0
        
        if s['moves']:
            avg_moves = sum(s['moves']) / len(s['moves'])
            min_moves = min(s['moves'])
            max_moves = max(s['moves'])
        else:
            avg_moves = min_moves = max_moves = 0
        
        print(f"\n  {algo_name}:")
        print(f"    Succès: {s['success']}/{total} ({success_rate:.1f}%)")
        print(f"    Temps:  moy={avg_time:.3f}s, min={min_time:.3f}s, max={max_time:.3f}s")
        print(f"    Coups:  moy={avg_moves:.1f}, min={min_moves}, max={max_moves}")

def main():
    parser = argparse.ArgumentParser(description="Compare Optimal vs Fast solver par catégorie de shuffle")
    parser.add_argument("-n", "--num-tests", type=int, default=3, 
                        help="Nombre de tests par catégorie (défaut: 3)")
    parser.add_argument("--timeout-optimal", type=float, default=30.0,
                        help="Timeout pour l'algo optimal en secondes (défaut: 30)")
    parser.add_argument("--timeout-fast", type=float, default=3.0,
                        help="Timeout pour l'algo fast en secondes (défaut: 3)")
    parser.add_argument("-c", "--category", type=str, default="all",
                        choices=["easy", "medium", "hard", "extreme", "all"],
                        help="Catégorie à tester (défaut: all)")
    
    args = parser.parse_args()
    
    print("="*70)
    print("COMPARAISON: OPTIMAL vs FAST - Par catégorie de shuffle")
    print("="*70)
    print(f"Tests par catégorie: {args.num_tests}")
    print(f"Timeout Optimal: {args.timeout_optimal}s")
    print(f"Timeout Fast: {args.timeout_fast}s")
    
    # Définition des catégories
    categories = {
        'easy': {
            'name': 'FACILE (< 5 coups)',
            'sizes': range(1, 5)
        },
        'medium': {
            'name': 'MOYEN (5-20 coups)',
            'sizes': range(5, 21)
        },
        'hard': {
            'name': 'DIFFICILE (20-30 coups)',
            'sizes': range(20, 31)
        },
        'extreme': {
            'name': 'TRÈS DIFFICILE (> 30 coups)',
            'sizes': range(31, 51)
        }
    }
    
    all_stats = {}
    
    # Exécuter les tests pour chaque catégorie sélectionnée
    if args.category == "all":
        cats_to_test = ['easy', 'medium', 'hard', 'extreme']
    else:
        cats_to_test = [args.category]
    
    for cat_key in cats_to_test:
        cat = categories[cat_key]
        stats = run_category_tests(
            cat['name'],
            cat['sizes'],
            args.num_tests,
            args.timeout_optimal,
            args.timeout_fast
        )
        all_stats[cat_key] = {'name': cat['name'], 'stats': stats}
    
    # Afficher les résumés
    print("\n")
    print("="*70)
    print("RÉSUMÉ GLOBAL")
    print("="*70)
    
    for cat_key, data in all_stats.items():
        print_summary(data['name'], data['stats'])
    
    # Tableau comparatif final
    print("\n")
    print("="*70)
    print("TABLEAU COMPARATIF")
    print("="*70)
    print(f"{'Catégorie':<25} | {'Optimal (temps/coups)':<25} | {'Fast (temps/coups)':<25}")
    print("-"*70)
    
    for cat_key, data in all_stats.items():
        name = data['name'][:24]
        s_opt = data['stats']['optimal']
        s_fast = data['stats']['fast']
        
        if s_opt['times']:
            opt_str = f"{sum(s_opt['times'])/len(s_opt['times']):.2f}s / {sum(s_opt['moves'])/len(s_opt['moves']):.1f}"
        else:
            opt_str = "N/A"
        
        if s_fast['times']:
            fast_str = f"{sum(s_fast['times'])/len(s_fast['times']):.2f}s / {sum(s_fast['moves'])/len(s_fast['moves']):.1f}"
        else:
            fast_str = "N/A"
        
        print(f"{name:<25} | {opt_str:<25} | {fast_str:<25}")
    
    print("\nLégende: temps moyen / coups moyens")

if __name__ == "__main__":
    main()
