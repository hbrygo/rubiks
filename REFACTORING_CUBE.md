# Refactoring cube.py - Notes pour le développeur

Ce document décrit les modifications possibles pour `cube.py` suite à la création du solveur autonome `solver_kociemba.py`.

---

## 📌 Contexte

Le fichier `solver_kociemba.py` contient maintenant une implémentation complète et fonctionnelle du solveur Kociemba. Il inclut ses propres classes de représentation du cube (`CubieCube`, `FaceCube`) qui sont optimisées pour l'algorithme.

---

## 🗑️ Ce qui peut être SUPPRIMÉ de `cube.py`

### 1. L'import problématique
```python
from connection import connections_map  # ← SUPPRIMER (fichier inexistant)
```

### 2. Méthodes inutilisées dans `Piece`

Les méthodes suivantes ne sont jamais appelées et peuvent être supprimées :

```python
# Méthodes à supprimer de la classe Piece
def check_solved_state(self)     # Jamais utilisée
def reset_to_original(self)      # Jamais utilisée  
def is_corner(self)              # Jamais utilisée
def is_edge(self)                # Jamais utilisée
def is_center(self)              # Jamais utilisée
def get_detailed_info(self)      # Jamais utilisée
```

### 3. Attributs jamais initialisés

```python
self.orientation  # Utilisé dans check_solved_state/reset_to_original mais jamais initialisé
```

---

## ✨ Ce qui peut être RÉCUPÉRÉ de `solver_kociemba.py`

### 1. Constantes utiles

```python
# Positions des coins (utile pour référence)
URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB = range(8)

# Positions des arêtes
UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR = range(12)

# Facelets (54 positions)
U1, U2, U3, U4, U5, U6, U7, U8, U9 = range(9)
R1, R2, R3, R4, R5, R6, R7, R8, R9 = range(9, 18)
# ... etc
```

### 2. Mapping coins/arêtes → facelets

```python
# Très utile pour savoir quels facelets correspondent à quel coin
CORNER_FACELET = (
    (U9, R1, F3), (U7, F1, L3), (U1, L1, B3), (U3, B1, R3),
    (D3, F9, R7), (D1, L9, F7), (D7, B9, L7), (D9, R9, B7),
)

EDGE_FACELET = (
    (U6, R2), (U8, F2), (U4, L2), (U2, B2), (D6, R8), (D2, F8),
    (D4, L8), (D8, B8), (F6, R4), (F4, L6), (B6, L4), (B4, R6),
)
```

### 3. Définition des 6 mouvements de base

Les mouvements sont définis par leur effet sur les coins et arêtes :

```python
# Exemple pour le mouvement R (face droite, sens horaire)
cpR = (DFR, UFL, ULB, URF, DRB, DLF, DBL, UBR)  # Permutation coins
coR = (2, 0, 0, 1, 1, 0, 0, 2)                   # Orientation coins
epR = (FR, UF, UL, UB, BR, DF, DL, DB, DR, FL, BL, UR)  # Permutation arêtes
eoR = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)       # Orientation arêtes
```

---

## 🔄 Méthode de conversion à ajouter

Pour faire le lien entre `cube.py` et `solver_kociemba.py`, ajouter :

```python
def to_cubestring(self) -> str:
    """
    Convertit le cube en format cubestring pour le solveur.
    
    Returns:
        String de 54 caractères au format URFDLB
        Ex: "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
    """
    # Mapping des couleurs internes vers le format solveur
    color_map = {
        'W': 'U',  # White → Up
        'Y': 'D',  # Yellow → Down
        'R': 'R',  # Red → Right
        'O': 'L',  # Orange → Left
        'G': 'F',  # Green → Front
        'B': 'B',  # Blue → Back
    }
    
    # L'ordre des faces dans cube.py: U, L, F, R, B, D
    # L'ordre pour le solveur:        U, R, F, D, L, B
    face_order_conversion = [0, 3, 2, 5, 1, 4]  # Indices pour réordonner
    
    result = []
    for new_idx in face_order_conversion:
        face_pieces = self.get_face(self.face_names[new_idx])
        for piece in face_pieces:
            result.append(color_map[piece.color])
    
    return ''.join(result)
```

---

## 🔧 Proposition de `cube.py` simplifié

```python
class Piece:
    def __init__(self, index, color):
        self.index = index
        self.color = color
        self.original_index = index
    
    def __str__(self):
        return f"Piece({self.index}, {self.color})"
    
    def __repr__(self):
        return self.__str__()


class Cube:
    def __init__(self):
        self.pieces = []
        self.face_names = ["U", "L", "F", "R", "B", "D"]
        self.colors = ["W", "O", "G", "R", "B", "Y"]
        self.initialize_cube()
    
    def initialize_cube(self):
        """Initialise le cube avec toutes les pièces"""
        for face_idx in range(6):
            color = self.colors[face_idx]
            for pos in range(9):
                global_index = face_idx * 9 + pos
                self.pieces.append(Piece(global_index, color))
    
    def get_face(self, face_name):
        """Retourne les 9 pièces d'une face donnée"""
        face_index = self.face_names.index(face_name)
        start_idx = face_index * 9
        return self.pieces[start_idx:start_idx + 9]
    
    def rotate_face_clockwise(self, face_name):
        """Rotation horaire d'une face"""
        # ... (garder l'implémentation actuelle)
    
    def to_cubestring(self):
        """Convertit en format pour solver_kociemba"""
        color_map = {'W': 'U', 'Y': 'D', 'R': 'R', 'O': 'L', 'G': 'F', 'B': 'B'}
        face_order = [0, 3, 2, 5, 1, 4]  # U, R, F, D, L, B
        
        result = []
        for idx in face_order:
            for piece in self.get_face(self.face_names[idx]):
                result.append(color_map[piece.color])
        return ''.join(result)
    
    def display(self):
        """Affiche le cube"""
        # ... (garder l'implémentation actuelle)
```

---

## 📋 Résumé des actions

| Action | Élément | Raison |
|--------|---------|--------|
| ❌ Supprimer | `from connection import connections_map` | Fichier inexistant |
| ❌ Supprimer | `self.connections` dans `Piece` | Plus utilisé |
| ❌ Supprimer | `setup_connections()` | Plus utilisé |
| ❌ Supprimer | `check_solved_state()` | Jamais utilisée |
| ❌ Supprimer | `reset_to_original()` | Jamais utilisée |
| ❌ Supprimer | `is_corner/edge/center()` | Jamais utilisées |
| ❌ Supprimer | `get_detailed_info()` | Jamais utilisée |
| ❌ Supprimer | `get_adjacent_faces()` | Non utilisée par le solveur |
| ✅ Ajouter | `to_cubestring()` | Conversion vers le solveur |
| ⚠️ Vérifier | Ordre des faces | `cube.py` = ULFBRD, solveur = URFDLB |

---

## 🔗 Utilisation avec le solveur

```python
from cube import Cube
from solver_kociemba import solve

# Créer et manipuler le cube
cube = Cube()
cube.rotate_face_clockwise("R")
cube.rotate_face_clockwise("U")

# Résoudre
cubestring = cube.to_cubestring()
solution = solve(cubestring)
print(f"Solution: {solution}")
```
