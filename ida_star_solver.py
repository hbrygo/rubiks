"""
IDA* Simplifié pour Rubik's Cube - Version sans Pattern Database
Heuristique: nombre de pièces mal orientées
"""

from cube import Cube
import time
from random import choice


class IDAStar_Simple:
    """Solveur IDA* simple sans Pattern Database"""
    
    def __init__(self, max_depth=20):
        self.max_depth = max_depth
        self.threshold = 0
        self.min_threshold = float('inf')
        self.moves = []
        self.nodes_generated = 0
        self.visited_states = set()
    
    def heuristic(self, cube):
        """
        Heuristique simple: compte les pièces mal orientées
        - Chaque pièce mal placée contribue 1 (estimation grossière)
        - Minimum: 0 (résolu)
        """
        # Compter les stickers mal orientés
        faces = {
            'U': [0, 1, 2, 3, 4, 5, 6, 7, 8],
            'L': [9, 10, 11, 12, 13, 14, 15, 16, 17],
            'F': [18, 19, 20, 21, 22, 23, 24, 25, 26],
            'R': [27, 28, 29, 30, 31, 32, 33, 34, 35],
            'B': [36, 37, 38, 39, 40, 41, 42, 43, 44],
            'D': [45, 46, 47, 48, 49, 50, 51, 52, 53]
        }
        
        bad_count = 0
        expected_colors = {
            'U': 'W', 'L': 'O', 'F': 'G', 'R': 'R', 'B': 'B', 'D': 'Y'
        }
        
        for face, indices in faces.items():
            expected = expected_colors[face]
            for idx in indices:
                if cube.pieces[idx].color != expected:
                    bad_count += 1
        
        # Diviser par 8 car il faut au moins 8 mouvements pour fixer 8 stickers
        return max(1, bad_count // 8)
    
    def run(self, cube):
        """Résout le cube avec IDA*"""
        print("\n" + "=" * 60)
        print("IDA* Simplifié (sans Pattern Database)")
        print("=" * 60)
        
        if self.is_solved(cube):
            print("✓ Cube déjà résolu!")
            return []
        
        # Heuristique initiale
        self.threshold = self.heuristic(cube)
        print(f"Heuristique initiale: {self.threshold}")
        
        iteration = 0
        start_total = time.time()
        prev_threshold = None
        
        while True:
            iteration += 1
            self.min_threshold = float('inf')
            self.nodes_generated = 0
            self.visited_states.clear()
            
            status = self.search(cube, 1)
            
            if status:
                elapsed = time.time() - start_total
                print(f"\n{'=' * 60}")
                print(f"✓ SOLUTION TROUVÉE!")
                print(f"  Mouvements: {len(self.moves)}")
                print(f"  Nœuds: {self.nodes_generated}")
                print(f"  Temps: {elapsed:.2f}s")
                print(f"{'=' * 60}")
                return self.moves
            
            self.moves = []
            old_threshold = self.threshold
            
            if self.min_threshold == float('inf'):
                print(f"✗ Aucune amélioration possible")
                return []
            
            self.threshold = self.min_threshold
            
            if self.threshold == prev_threshold:
                print(f"✗ Seuil bloqué à {self.threshold}")
                return []
            prev_threshold = self.threshold
            
            if self.threshold > self.max_depth:
                print(f"✗ Max depth ({self.max_depth}) atteint")
                return []
            
            if time.time() - start_total > 60:
                print(f"✗ Timeout (60s)")
                return []
            
            print(f"→ Itération {iteration}: seuil {old_threshold}→{self.threshold} ({self.nodes_generated} nœuds)")
        
        return []
    
    def search(self, cube, g_score):
        """Recherche DFS avec IDA*"""
        if self.is_solved(cube):
            return True
        
        if len(self.moves) >= self.threshold:
            return False
        
        self.nodes_generated += 1
        
        # Obtenir signature pour éviter de revisiter
        state_sig = self.get_state_sig(cube)
        if state_sig in self.visited_states and len(self.moves) > 0:
            return False
        self.visited_states.add(state_sig)
        
        # Tous les mouvements
        moves = ['U', 'D', 'L', 'R', 'F', 'B',
                 "U'", "D'", "L'", "R'", "F'", "B'",
                 'U2', 'D2', 'L2', 'R2', 'F2', 'B2']
        
        # Éviter mouvement opposé
        if self.moves:
            last_move = self.moves[-1]
            last_face = last_move[0]
            moves = [m for m in moves if m[0] != last_face]
        
        # Évaluer tous les mouvements
        candidates = []
        for move in moves:
            new_cube = self.copy_cube(cube)
            self.apply_move(new_cube, move)
            
            if self.is_solved(new_cube):
                self.moves.append(move)
                return True
            
            h = self.heuristic(new_cube)
            f = g_score + h
            
            if f > self.threshold:
                if f < self.min_threshold:
                    self.min_threshold = f
            else:
                candidates.append((h, move, new_cube))
        
        # Trier par heuristique et explorer
        candidates.sort()
        for h, move, new_cube in candidates:
            self.moves.append(move)
            if self.search(new_cube, g_score + 1):
                return True
            self.moves.pop()
        
        return False
    
    def is_solved(self, cube):
        """Vérifie si le cube est résolu"""
        expected_colors = {
            'U': 'W', 'L': 'O', 'F': 'G', 'R': 'R', 'B': 'B', 'D': 'Y'
        }
        
        faces = {
            'U': [0, 1, 2, 3, 4, 5, 6, 7, 8],
            'L': [9, 10, 11, 12, 13, 14, 15, 16, 17],
            'F': [18, 19, 20, 21, 22, 23, 24, 25, 26],
            'R': [27, 28, 29, 30, 31, 32, 33, 34, 35],
            'B': [36, 37, 38, 39, 40, 41, 42, 43, 44],
            'D': [45, 46, 47, 48, 49, 50, 51, 52, 53]
        }
        
        for face, indices in faces.items():
            for idx in indices:
                if cube.pieces[idx].color != expected_colors[face]:
                    return False
        return True
    
    def get_state_sig(self, cube):
        """Obtient une signature de l'état du cube"""
        sig = []
        for i in range(54):
            sig.append(cube.pieces[i].color)
        return tuple(sig)
    
    def apply_move(self, cube, move):
        """Applique un mouvement"""
        face = move[0]
        if len(move) == 2:
            if move[1] == "'":
                for _ in range(3):
                    cube.rotate_face_clockwise(face)
            elif move[1] == "2":
                for _ in range(2):
                    cube.rotate_face_clockwise(face)
        else:
            cube.rotate_face_clockwise(face)
    
    @staticmethod
    def copy_cube(cube):
        """Copie un cube"""
        new_cube = Cube()
        for i in range(54):
            new_cube.pieces[i].color = cube.pieces[i].color
        return new_cube


def solve_with_ida_star_simple(cube):
    """Interface pour résoudre un cube"""
    solver = IDAStar_Simple(max_depth=20)
    solution = solver.run(cube)
    return solution


# ===== Test =====
if __name__ == "__main__":
    from random import choice as rand_choice
    
    def scramble_cube(cube, num_moves=20):
        """Mélange le cube"""
        all_moves = ['U', 'D', 'L', 'R', 'F', 'B', 
                     "U'", "D'", "L'", "R'", "F'", "B'",
                     'U2', 'D2', 'L2', 'R2', 'F2', 'B2']
        scramble = []
        for _ in range(num_moves):
            move = rand_choice(all_moves)
            face = move[0]
            if len(move) == 2:
                if move[1] == "'":
                    for _ in range(3):
                        cube.rotate_face_clockwise(face)
                elif move[1] == "2":
                    for _ in range(2):
                        cube.rotate_face_clockwise(face)
            else:
                cube.rotate_face_clockwise(face)
            scramble.append(move)
        return scramble
    
    print("Test IDA* Simplifié")
    print("=" * 60)
    
    # Créer et mélanger un cube
    cube = Cube()
    moves = scramble_cube(cube, num_moves=5)
    print(f"Scramble: {' '.join(moves)}")
    
    # Résoudre
    solution = solve_with_ida_star_simple(cube)
    
    if solution:
        print(f"\nSolution: {' '.join(solution)}")
        
        # Vérifier
        test_cube = Cube()
        for move in moves:
            face = move[0]
            if len(move) == 2:
                if move[1] == "'":
                    for _ in range(3):
                        test_cube.rotate_face_clockwise(face)
                elif move[1] == "2":
                    for _ in range(2):
                        test_cube.rotate_face_clockwise(face)
            else:
                test_cube.rotate_face_clockwise(face)
        
        for move in solution:
            face = move[0]
            if len(move) == 2:
                if move[1] == "'":
                    for _ in range(3):
                        test_cube.rotate_face_clockwise(face)
                elif move[1] == "2":
                    for _ in range(2):
                        test_cube.rotate_face_clockwise(face)
            else:
                test_cube.rotate_face_clockwise(face)
        
        solver = IDAStar_Simple()
        if solver.is_solved(test_cube):
            print("✓ Cube résolu!")
        else:
            print("✗ Cube non résolu")
    else:
        print("✗ Aucune solution trouvée")
