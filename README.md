# Rubik's Cube Solver - Kociemba Two-Phase Algorithm

Implémentation Python pure et autonome de l'algorithme Kociemba pour résoudre le Rubik's Cube.

## 🚀 Utilisation Rapide

```python
from solver_kociemba import solve

# Format cubestring: 54 caractères URFDLB (9 par face)
solution = solve("DRLUUBFBRBLURRLBFFUFRFBDUDDRFDDLLDRLDUBFLUBLRFBBDUULF")
print(solution)  # ex: "D2 R' D' F2 B D R2 D2 R' ..."
```

### Ligne de commande

```bash
python3 solver_kociemba.py
```

## 📁 Structure du Projet

```
rubiks/
├── solver_kociemba.py      # Solveur Kociemba (PRINCIPAL)
├── cube.py                  # Représentation du cube (interface)
├── kociemba_tables.pkl      # Cache des tables (généré automatiquement)
├── requirement.txt          # Dépendances (aucune pour le solveur)
└── README.md
```

## ⚡ Performances

| Métrique | Valeur |
|----------|--------|
| **Première exécution** | ~40s (génération des tables) |
| **Exécutions suivantes** | ~0.05s (chargement cache) |
| **Temps de résolution** | < 1s (moyenne) |
| **Longueur des solutions** | ~20 mouvements (HTM) |
| **Dépendances externes** | **Aucune** |

### Métriques

Les solutions utilisent la métrique **Half-Turn Metric (HTM)** :
- Un quart de tour (`U`, `R'`) = 1 mouvement
- Un demi-tour (`U2`, `R2`) = 1 mouvement
- Le score est équivalent à `wc -w` sur la solution

## 🔧 Format du Cubestring

Le cube est représenté par une chaîne de 54 caractères :

```
             | U1 U2 U3 |
             | U4 U5 U6 |
             | U7 U8 U9 |
 ____________|__________|____________
| L1 L2 L3   | F1 F2 F3 | R1 R2 R3   | B1 B2 B3 |
| L4 L5 L6   | F4 F5 F6 | R4 R5 R6   | B4 B5 B6 |
| L7 L8 L9   | F7 F8 F9 | R7 R8 R9   | B7 B8 B9 |
 ____________|__________|____________
             | D1 D2 D3 |
             | D4 D5 D6 |
             | D7 D8 D9 |
```

**Ordre de lecture** : `U R F D L B` (9 facelets par face, de gauche à droite, de haut en bas)

**Cube résolu** : `UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB`

## 📖 API

### `solve(cube_string, max_depth=21, timeout=10.0, separator=False)`

Résout un Rubik's Cube.

**Paramètres :**
- `cube_string` : String de 54 caractères (format URFDLB)
- `max_depth` : Profondeur maximale de recherche (défaut: 21)
- `timeout` : Temps limite en secondes (défaut: 10.0)
- `separator` : Si True, affiche un '.' entre phase 1 et phase 2

**Retourne :**
- La solution en notation standard (ex: `"U R2 F' D B2"`)
- Message d'erreur si échec (ex: `"Error: invalid cube"`)

### `init_tables()`

Pré-charge les tables de pruning. Utile pour éviter le délai au premier appel de `solve()`.

## 🧪 Tests

```bash
# Lancer les tests complets
python3 test_comprehensive.py
```

## 📚 Algorithme Two-Phase

L'algorithme Kociemba fonctionne en deux phases :

1. **Phase 1** : Réduit le cube au sous-groupe G1 = ⟨U, D, R², L², F², B²⟩
   - Oriente tous les coins et arêtes
   - Place les arêtes du "slice" (FR, FL, BL, BR) dans leur couche

2. **Phase 2** : Résout dans G1 avec uniquement U, D, R², L², F², B²
   - Permute les coins
   - Permute les arêtes

## 📦 Installation

```bash
# Aucune dépendance requise pour le solveur !
python3 solver_kociemba.py
```

## 🔗 Références

- [Herbert Kociemba - Cube Explorer](http://kociemba.org/cube.htm)
- [Two-Phase Algorithm](http://kociemba.org/twophase.htm)

