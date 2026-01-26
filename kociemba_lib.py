"""
Wrapper pour le solveur Kociemba (bibliothèque externe)
=======================================================

Utilise la bibliothèque kociemba qui a des tables de pruning précalculées
pour des solutions très rapides (~0.1s) et quasi-optimales (~20 coups).
"""

import kociemba
import numpy as np

# =============================================================================
# REPRÉSENTATION DU CUBE
# =============================================================================

class Cube:
    """Représentation du cube compatible avec le format kociemba"""
    
    def __init__(self):
        # Chaque face est une matrice 3x3 avec labels position
        self.face_up = np.array([["U0", "U1", "U2"], ["U3", "U4", "U5"], ["U6", "U7", "U8"]])
        self.face_down = np.array([["D0", "D1", "D2"], ["D3", "D4", "D5"], ["D6", "D7", "D8"]])
        self.face_front = np.array([["F0", "F1", "F2"], ["F3", "F4", "F5"], ["F6", "F7", "F8"]])
        self.face_back = np.array([["B0", "B1", "B2"], ["B3", "B4", "B5"], ["B6", "B7", "B8"]])
        self.face_left = np.array([["L0", "L1", "L2"], ["L3", "L4", "L5"], ["L6", "L7", "L8"]])
        self.face_right = np.array([["R0", "R1", "R2"], ["R3", "R4", "R5"], ["R6", "R7", "R8"]])
        
        self.faces = {
            "U": self.U, "D": self.D, "F": self.F,
            "B": self.B, "L": self.L, "R": self.R
        }
    
    def copy(self, other):
        """Copie l'état d'un autre cube"""
        self.face_up = other.face_up.copy()
        self.face_down = other.face_down.copy()
        self.face_front = other.face_front.copy()
        self.face_back = other.face_back.copy()
        self.face_left = other.face_left.copy()
        self.face_right = other.face_right.copy()
    
    def clone(self):
        """Retourne une copie du cube"""
        c = Cube()
        c.copy(self)
        return c
    
    def sides(self):
        return {"U": self.face_up, "D": self.face_down, "F": self.face_front,
                "B": self.face_back, "L": self.face_left, "R": self.face_right}
    
    def is_solved(self):
        """Vérifie si le cube est résolu"""
        for face_name, face in self.sides().items():
            for i in range(9):
                if face.item(i)[0] != face_name:
                    return False
        return True
    
    def to_kociemba_string(self):
        """
        Convertit le cube en string format Kociemba.
        Ordre: U R F D L B (chaque face lue de gauche à droite, haut en bas)
        """
        result = ""
        # Ordre Kociemba: U R F D L B
        for face in [self.face_up, self.face_right, self.face_front, 
                     self.face_down, self.face_left, self.face_back]:
            for i in range(9):
                result += face.item(i)[0]
        return result
    
    # Rotations des faces
    def U(self, reverse=False):
        if reverse:
            self.face_up = np.rot90(self.face_up)
            tmp = self.face_front[0].copy()
            self.face_front[0] = self.face_left[0].copy()
            self.face_left[0] = self.face_back[0].copy()
            self.face_back[0] = self.face_right[0].copy()
            self.face_right[0] = tmp
        else:
            self.face_up = np.rot90(self.face_up, -1)
            tmp = self.face_front[0].copy()
            self.face_front[0] = self.face_right[0].copy()
            self.face_right[0] = self.face_back[0].copy()
            self.face_back[0] = self.face_left[0].copy()
            self.face_left[0] = tmp

    def D(self, reverse=False):
        if reverse:
            self.face_down = np.rot90(self.face_down)
            tmp = self.face_front[2].copy()
            self.face_front[2] = self.face_right[2].copy()
            self.face_right[2] = self.face_back[2].copy()
            self.face_back[2] = self.face_left[2].copy()
            self.face_left[2] = tmp
        else:
            self.face_down = np.rot90(self.face_down, -1)
            tmp = self.face_front[2].copy()
            self.face_front[2] = self.face_left[2].copy()
            self.face_left[2] = self.face_back[2].copy()
            self.face_back[2] = self.face_right[2].copy()
            self.face_right[2] = tmp

    def F(self, reverse=False):
        if reverse:
            self.face_front = np.rot90(self.face_front)
            tmp = self.face_up[2].copy()
            self.face_up[2] = self.face_right[:, 0].copy()
            self.face_right[:, 0] = np.flip(self.face_down[0])
            self.face_down[0] = self.face_left[:, 2].copy()
            self.face_left[:, 2] = np.flip(tmp)
        else:
            self.face_front = np.rot90(self.face_front, -1)
            tmp = self.face_up[2].copy()
            self.face_up[2] = np.flip(self.face_left[:, 2])
            self.face_left[:, 2] = self.face_down[0].copy()
            self.face_down[0] = np.flip(self.face_right[:, 0])
            self.face_right[:, 0] = tmp

    def B(self, reverse=False):
        if reverse:
            self.face_back = np.rot90(self.face_back)
            tmp = self.face_up[0].copy()
            self.face_up[0] = np.flip(self.face_left[:, 0])
            self.face_left[:, 0] = self.face_down[2].copy()
            self.face_down[2] = np.flip(self.face_right[:, 2])
            self.face_right[:, 2] = tmp
        else:
            self.face_back = np.rot90(self.face_back, -1)
            tmp = self.face_up[0].copy()
            self.face_up[0] = self.face_right[:, 2].copy()
            self.face_right[:, 2] = np.flip(self.face_down[2])
            self.face_down[2] = self.face_left[:, 0].copy()
            self.face_left[:, 0] = np.flip(tmp)

    def L(self, reverse=False):
        if reverse:
            self.face_left = np.rot90(self.face_left)
            tmp = self.face_up[:, 0].copy()
            self.face_up[:, 0] = self.face_front[:, 0].copy()
            self.face_front[:, 0] = self.face_down[:, 0].copy()
            self.face_down[:, 0] = np.flip(self.face_back[:, 2])
            self.face_back[:, 2] = np.flip(tmp)
        else:
            self.face_left = np.rot90(self.face_left, -1)
            tmp = self.face_up[:, 0].copy()
            self.face_up[:, 0] = np.flip(self.face_back[:, 2])
            self.face_back[:, 2] = np.flip(self.face_down[:, 0])
            self.face_down[:, 0] = self.face_front[:, 0].copy()
            self.face_front[:, 0] = tmp

    def R(self, reverse=False):
        if reverse:
            self.face_right = np.rot90(self.face_right)
            tmp = self.face_up[:, 2].copy()
            self.face_up[:, 2] = np.flip(self.face_back[:, 0])
            self.face_back[:, 0] = np.flip(self.face_down[:, 2])
            self.face_down[:, 2] = self.face_front[:, 2].copy()
            self.face_front[:, 2] = tmp
        else:
            self.face_right = np.rot90(self.face_right, -1)
            tmp = self.face_up[:, 2].copy()
            self.face_up[:, 2] = self.face_front[:, 2].copy()
            self.face_front[:, 2] = self.face_down[:, 2].copy()
            self.face_down[:, 2] = np.flip(self.face_back[:, 0])
            self.face_back[:, 0] = np.flip(tmp)


# =============================================================================
# UTILITAIRES
# =============================================================================

def apply_move(cube, move):
    """Applique un mouvement au cube"""
    if len(move) == 1:
        cube.faces[move]()
    elif move[1] == "'":
        cube.faces[move[0]](True)
    elif move[1] == "2":
        cube.faces[move[0]]()
        cube.faces[move[0]]()


def apply_sequence(cube, sequence):
    """Applique une séquence de mouvements"""
    if not sequence:
        return cube
    moves = sequence.replace("'", "'").replace("'", "'").split()
    for move in moves:
        apply_move(cube, move)
    return cube


# =============================================================================
# SOLVEUR KOCIEMBA
# =============================================================================

def solver(cube):
    """
    Résout le cube avec la bibliothèque Kociemba.
    
    Retourne la solution sous forme de string.
    """
    if cube.is_solved():
        return ""
    
    # Convertir en format Kociemba
    cube_string = cube.to_kociemba_string()
    
    try:
        # Résoudre avec Kociemba
        solution = kociemba.solve(cube_string)
        
        # Appliquer la solution au cube
        apply_sequence(cube, solution)
        
        return solution
    except Exception as e:
        # En cas d'erreur (cube invalide), retourner vide
        print(f"Erreur Kociemba: {e}")
        return ""


def solver_optimized(cube):
    """Alias pour solver (Kociemba est déjà optimisé)"""
    return solver(cube)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    import time
    
    # Test simple
    cube = Cube()
    scramble = "R U R' U'"
    apply_sequence(cube, scramble)
    
    print(f"Scramble: {scramble}")
    print(f"Cube résolu avant: {cube.is_solved()}")
    print(f"String Kociemba: {cube.to_kociemba_string()}")
    
    start = time.time()
    solution = solver(cube)
    elapsed = time.time() - start
    
    print(f"Solution: {solution}")
    print(f"Coups: {len(solution.split()) if solution else 0}")
    print(f"Temps: {elapsed:.3f}s")
    print(f"Cube résolu après: {cube.is_solved()}")
    
    print("\n--- Test T-perm ---")
    cube2 = Cube()
    scramble2 = "R U R' F' R U R' U' R' F R2 U' R'"
    apply_sequence(cube2, scramble2)
    
    start = time.time()
    solution2 = solver(cube2)
    elapsed = time.time() - start
    
    print(f"Scramble: {scramble2}")
    print(f"Solution: {solution2}")
    print(f"Coups: {len(solution2.split()) if solution2 else 0}")
    print(f"Temps: {elapsed:.3f}s")
    print(f"Résolu: {cube2.is_solved()}")
