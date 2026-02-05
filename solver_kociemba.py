"""
Solver Kociemba - Two-Phase Algorithm
=====================================

Implémentation Python pure et autonome de l'algorithme Kociemba pour
résoudre le Rubik's Cube. Aucune dépendance externe requise.

UTILISATION:
    from solver_kociemba import solve
    
    # Format cubestring: 54 caractères URFDLB (9 par face)
    solution = solve("DRLUUBFBRBLURRLBFFUFRFBDUDDRFDDLLDRLDUBFLUBLRFBBDUULF")
    print(solution)  # ex: "R U R' F2 D2 ..."

TABLES DE PRUNING:
    Les tables sont générées automatiquement au premier lancement (~40 secondes)
    puis sauvegardées sur disque pour les prochaines exécutions.
    Fichier cache: kociemba_tables.pkl (dans le même répertoire que ce script)

Algorithme Two-Phase:
    Phase 1: Réduit le cube au sous-groupe G1 = <U,D,R2,L2,F2,B2>
    Phase 2: Résout dans G1 avec uniquement U, D, R2, L2, F2, B2
    
Basé sur les travaux de Herbert Kociemba.
"""

import time
import pickle
import os

# =============================================================================
# CONSTANTES
# =============================================================================

# Couleurs / Faces
U, R, F, D, L, B = 0, 1, 2, 3, 4, 5
COLORS = {'U': U, 'R': R, 'F': F, 'D': D, 'L': L, 'B': B}
COLOR_NAMES = ['U', 'R', 'F', 'D', 'L', 'B']

# Positions des coins
URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB = range(8)

# Positions des arêtes
UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR = range(12)

# Facelets (54 positions)
# Face U: 0-8, R: 9-17, F: 18-26, D: 27-35, L: 36-44, B: 45-53
U1, U2, U3, U4, U5, U6, U7, U8, U9 = range(9)
R1, R2, R3, R4, R5, R6, R7, R8, R9 = range(9, 18)
F1, F2, F3, F4, F5, F6, F7, F8, F9 = range(18, 27)
D1, D2, D3, D4, D5, D6, D7, D8, D9 = range(27, 36)
L1, L2, L3, L4, L5, L6, L7, L8, L9 = range(36, 45)
B1, B2, B3, B4, B5, B6, B7, B8, B9 = range(45, 54)

# Mapping coins -> facelets
CORNER_FACELET = (
    (U9, R1, F3), (U7, F1, L3), (U1, L1, B3), (U3, B1, R3),
    (D3, F9, R7), (D1, L9, F7), (D7, B9, L7), (D9, R9, B7),
)

# Mapping arêtes -> facelets
EDGE_FACELET = (
    (U6, R2), (U8, F2), (U4, L2), (U2, B2), (D6, R8), (D2, F8),
    (D4, L8), (D8, B8), (F6, R4), (F4, L6), (B6, L4), (B4, R6),
)

# Couleurs des coins
CORNER_COLOR = (
    (U, R, F), (U, F, L), (U, L, B), (U, B, R),
    (D, F, R), (D, L, F), (D, B, L), (D, R, B),
)

# Couleurs des arêtes
EDGE_COLOR = (
    (U, R), (U, F), (U, L), (U, B), (D, R), (D, F),
    (D, L), (D, B), (F, R), (F, L), (B, L), (B, R),
)

# Tailles des espaces de coordonnées
N_TWIST = 2187      # 3^7 orientations de coins
N_FLIP = 2048       # 2^11 orientations d'arêtes
N_SLICE1 = 495      # C(12,4) positions des arêtes E-slice en phase 1
N_SLICE2 = 24       # 4! permutations des arêtes E-slice en phase 2
N_PARITY = 2        # 2 parités possibles
N_URFtoDLF = 20160  # 8!/2! permutations de 6 coins
N_FRtoBR = 11880    # 12!/8! permutations de 4 arêtes
N_URtoUL = 1320     # 12!/9! permutations de 3 arêtes
N_UBtoDF = 1320     # 12!/9! permutations de 3 arêtes
N_URtoDF = 20160    # 8!/2! permutations de 6 arêtes
N_MOVE = 18         # 18 mouvements possibles

# Table de parité (précalculée)
PARITY_MOVE = (
    (1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1),
    (0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0),
)

# =============================================================================
# UTILITAIRES
# =============================================================================

def Cnk(n, k):
    """Calcul de combinaison C(n,k)"""
    if n < k:
        return 0
    if k > n // 2:
        k = n - k
    s = 1
    for i in range(k):
        s = s * (n - i) // (i + 1)
    return s


def rotate_left(arr, l, r):
    """Rotation gauche des éléments entre l et r"""
    temp = arr[l]
    for i in range(l, r):
        arr[i] = arr[i + 1]
    arr[r] = temp


def rotate_right(arr, l, r):
    """Rotation droite des éléments entre l et r"""
    temp = arr[r]
    for i in range(r, l, -1):
        arr[i] = arr[i - 1]
    arr[l] = temp


# =============================================================================
# CUBIE CUBE - Représentation par cubies
# =============================================================================

class CubieCube:
    """Représentation du cube par coins et arêtes (permutation + orientation)"""
    
    __slots__ = ('cp', 'co', 'ep', 'eo')
    
    def __init__(self, cp=None, co=None, ep=None, eo=None):
        self.cp = list(cp) if cp else [URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB]
        self.co = list(co) if co else [0, 0, 0, 0, 0, 0, 0, 0]
        self.ep = list(ep) if ep else [UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR]
        self.eo = list(eo) if eo else [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    def corner_multiply(self, b):
        """Multiplie les coins par un autre CubieCube"""
        cp_new = [self.cp[b.cp[i]] for i in range(8)]
        co_new = [(self.co[b.cp[i]] + b.co[i]) % 3 for i in range(8)]
        self.cp = cp_new
        self.co = co_new
    
    def edge_multiply(self, b):
        """Multiplie les arêtes par un autre CubieCube"""
        ep_new = [self.ep[b.ep[i]] for i in range(12)]
        eo_new = [(self.eo[b.ep[i]] + b.eo[i]) % 2 for i in range(12)]
        self.ep = ep_new
        self.eo = eo_new
    
    def multiply(self, b):
        """Multiplie le cube complet"""
        self.corner_multiply(b)
        self.edge_multiply(b)
    
    # --- Coordonnées Phase 1 ---
    
    def get_twist(self):
        """Orientation des coins: 0 <= twist < 2187"""
        ret = 0
        for i in range(7):
            ret = 3 * ret + self.co[i]
        return ret
    
    def set_twist(self, twist):
        """Définit l'orientation des coins"""
        parity = 0
        for i in range(6, -1, -1):
            self.co[i] = twist % 3
            parity += self.co[i]
            twist //= 3
        self.co[7] = (3 - parity % 3) % 3
    
    def get_flip(self):
        """Orientation des arêtes: 0 <= flip < 2048"""
        ret = 0
        for i in range(11):
            ret = 2 * ret + self.eo[i]
        return ret
    
    def set_flip(self, flip):
        """Définit l'orientation des arêtes"""
        parity = 0
        for i in range(10, -1, -1):
            self.eo[i] = flip % 2
            parity += self.eo[i]
            flip //= 2
        self.eo[11] = (2 - parity % 2) % 2
    
    def get_FRtoBR(self):
        """Position des arêtes FR, FL, BL, BR (slice)"""
        a, x = 0, 0
        edge4 = [0, 0, 0, 0]
        for j in range(11, -1, -1):
            if FR <= self.ep[j] <= BR:
                a += Cnk(11 - j, x + 1)
                edge4[3 - x] = self.ep[j]
                x += 1
        b = 0
        for j in range(3, 0, -1):
            k = 0
            while edge4[j] != j + 8:
                rotate_left(edge4, 0, j)
                k += 1
            b = (j + 1) * b + k
        return 24 * a + b
    
    def set_FRtoBR(self, idx):
        """Définit la position des arêtes FR, FL, BL, BR"""
        sliceEdge = [FR, FL, BL, BR]
        otherEdge = [UR, UF, UL, UB, DR, DF, DL, DB]
        b = idx % 24
        a = idx // 24
        
        for i in range(12):
            self.ep[i] = DB
        
        for j in range(1, 4):
            k = b % (j + 1)
            b //= (j + 1)
            while k > 0:
                k -= 1
                rotate_right(sliceEdge, 0, j)
        
        x = 3
        for j in range(12):
            if a - Cnk(11 - j, x + 1) >= 0:
                self.ep[j] = sliceEdge[3 - x]
                a -= Cnk(11 - j, x + 1)
                x -= 1
        
        x = 0
        for j in range(12):
            if self.ep[j] == DB:
                self.ep[j] = otherEdge[x]
                x += 1
    
    # --- Coordonnées Phase 2 ---
    
    def corner_parity(self):
        """Parité de la permutation des coins"""
        s = 0
        for i in range(7, 0, -1):
            for j in range(i - 1, -1, -1):
                if self.cp[j] > self.cp[i]:
                    s += 1
        return s % 2
    
    def get_URFtoDLF(self):
        """Permutation des 6 premiers coins"""
        a, b, x = 0, 0, 0
        corner6 = [0] * 6
        for j in range(8):
            if self.cp[j] <= DLF:
                a += Cnk(j, x + 1)
                corner6[x] = self.cp[j]
                x += 1
        # Calcul de l'index de permutation (base factorielle)
        for j in range(5, 0, -1):  # j = 5, 4, 3, 2, 1
            k = 0
            while corner6[j] != j:
                rotate_left(corner6, 0, j)
                k += 1
            b = (j + 1) * b + k
        return 720 * a + b
    
    def set_URFtoDLF(self, idx):
        """Définit la permutation des 6 premiers coins"""
        corner6 = [URF, UFL, ULB, UBR, DFR, DLF]
        other = [DBL, DRB]
        b = idx % 720
        a = idx // 720
        
        for i in range(8):
            self.cp[i] = DRB
        
        # Générer la permutation depuis l'index b
        for j in range(1, 6):  # j = 1, 2, 3, 4, 5
            k = b % (j + 1)
            b //= (j + 1)
            while k > 0:
                rotate_right(corner6, 0, j)
                k -= 1
        
        x = 5
        for j in range(7, -1, -1):
            if a - Cnk(j, x + 1) >= 0:
                self.cp[j] = corner6[x]
                a -= Cnk(j, x + 1)
                x -= 1
        
        x = 0
        for j in range(8):
            if self.cp[j] == DRB:
                self.cp[j] = other[x]
                x += 1
    
    def get_URtoUL(self):
        """Permutation de UR, UF, UL"""
        a, b, x = 0, 0, 0
        edge3 = [0, 0, 0]
        for j in range(12):
            if self.ep[j] <= UL:
                a += Cnk(j, x + 1)
                edge3[x] = self.ep[j]
                x += 1
        for j in range(2, 0, -1):  # j = 2, 1
            k = 0
            while edge3[j] != j:
                rotate_left(edge3, 0, j)
                k += 1
            b = (j + 1) * b + k
        return 6 * a + b
    
    def set_URtoUL(self, idx):
        """Définit la permutation de UR, UF, UL"""
        edge3 = [UR, UF, UL]
        b = idx % 6
        a = idx // 6
        
        for i in range(12):
            self.ep[i] = BR
        
        # Générer la permutation depuis l'index b
        for j in range(1, 3):  # j = 1, 2
            k = b % (j + 1)
            b //= (j + 1)
            while k > 0:
                rotate_right(edge3, 0, j)
                k -= 1
        
        x = 2
        for j in range(11, -1, -1):
            if a - Cnk(j, x + 1) >= 0:
                self.ep[j] = edge3[x]
                a -= Cnk(j, x + 1)
                x -= 1
    
    def get_UBtoDF(self):
        """Permutation de UB, DR, DF"""
        a, b, x = 0, 0, 0
        edge3 = [0, 0, 0]
        for j in range(12):
            if UB <= self.ep[j] <= DF:
                a += Cnk(j, x + 1)
                edge3[x] = self.ep[j]
                x += 1
        for j in range(2, 0, -1):  # j = 2, 1
            k = 0
            while edge3[j] != j + UB:
                rotate_left(edge3, 0, j)
                k += 1
            b = (j + 1) * b + k
        return 6 * a + b
    
    def set_UBtoDF(self, idx):
        """Définit la permutation de UB, DR, DF"""
        edge3 = [UB, DR, DF]
        b = idx % 6
        a = idx // 6
        
        for i in range(12):
            self.ep[i] = BR
        
        # Générer la permutation depuis l'index b
        for j in range(1, 3):  # j = 1, 2
            k = b % (j + 1)
            b //= (j + 1)
            while k > 0:
                rotate_right(edge3, 0, j)
                k -= 1
        
        x = 2
        for j in range(11, -1, -1):
            if a - Cnk(j, x + 1) >= 0:
                self.ep[j] = edge3[x]
                a -= Cnk(j, x + 1)
                x -= 1
    
    def get_URtoDF(self):
        """Permutation de UR, UF, UL, UB, DR, DF"""
        a, b, x = 0, 0, 0
        edge6 = [0] * 6
        for j in range(12):
            if self.ep[j] <= DF:
                a += Cnk(j, x + 1)
                edge6[x] = self.ep[j]
                x += 1
        for j in range(5, 0, -1):  # j = 5, 4, 3, 2, 1
            k = 0
            while edge6[j] != j:
                rotate_left(edge6, 0, j)
                k += 1
            b = (j + 1) * b + k
        return 720 * a + b
    
    def set_URtoDF(self, idx):
        """Définit la permutation de UR, UF, UL, UB, DR, DF"""
        edge6 = [UR, UF, UL, UB, DR, DF]
        other = [DL, DB, FR, FL, BL, BR]
        b = idx % 720
        a = idx // 720
        
        for i in range(12):
            self.ep[i] = BR
        
        # Générer la permutation depuis l'index b
        for j in range(1, 6):  # j = 1, 2, 3, 4, 5
            k = b % (j + 1)
            b //= (j + 1)
            while k > 0:
                rotate_right(edge6, 0, j)
                k -= 1
        
        x = 5
        for j in range(11, -1, -1):
            if a - Cnk(j, x + 1) >= 0:
                self.ep[j] = edge6[x]
                a -= Cnk(j, x + 1)
                x -= 1
        
        x = 0
        for j in range(12):
            if self.ep[j] == BR:
                self.ep[j] = other[x]
                x += 1
    
    def to_facecube(self):
        """Convertit CubieCube en FaceCube"""
        # Créer les facelets (54)
        f = [U] * 54  # Initialiser avec U (sera remplacé)
        
        # Centres (fixes)
        f[4] = U   # Centre Up
        f[13] = R  # Centre Right
        f[22] = F  # Centre Front
        f[31] = D  # Centre Down
        f[40] = L  # Centre Left
        f[49] = B  # Centre Back
        
        # Coins
        for i in range(8):
            j = self.cp[i]  # Quel coin est en position i
            ori = self.co[i]  # Son orientation
            for n in range(3):
                f[CORNER_FACELET[i][(n + ori) % 3]] = CORNER_COLOR[j][n]
        
        # Arêtes
        for i in range(12):
            j = self.ep[i]  # Quelle arête est en position i
            ori = self.eo[i]  # Son orientation
            for n in range(2):
                f[EDGE_FACELET[i][(n + ori) % 2]] = EDGE_COLOR[j][n]
        
        # Créer FaceCube
        fc = FaceCube.__new__(FaceCube)
        fc.f = f
        return fc
    
    def verify(self):
        """Vérifie la validité du cube. Retourne 0 si OK, code erreur sinon."""
        # Vérifier que chaque coin apparaît exactement une fois
        corner_count = [0] * 8
        for c in self.cp:
            if c < 0 or c > 7:
                return -2
            corner_count[c] += 1
        for count in corner_count:
            if count != 1:
                return -2
        
        # Vérifier que chaque arête apparaît exactement une fois
        edge_count = [0] * 12
        for e in self.ep:
            if e < 0 or e > 11:
                return -1
            edge_count[e] += 1
        for count in edge_count:
            if count != 1:
                return -1
        
        # Vérifier orientation des coins (somme doit être 0 mod 3)
        if sum(self.co) % 3 != 0:
            return -5
        
        # Vérifier orientation des arêtes (somme doit être 0 mod 2)
        if sum(self.eo) % 2 != 0:
            return -3
        
        # Vérifier parité
        edge_parity = 0
        for i in range(11, 0, -1):
            for j in range(i - 1, -1, -1):
                if self.ep[j] > self.ep[i]:
                    edge_parity += 1
        if edge_parity % 2 != self.corner_parity():
            return -6
        
        return 0


# =============================================================================
# DÉFINITION DES 6 MOUVEMENTS DE BASE
# =============================================================================

# U (quart de tour horaire face supérieure)
cpU = (UBR, URF, UFL, ULB, DFR, DLF, DBL, DRB)
coU = (0, 0, 0, 0, 0, 0, 0, 0)
epU = (UB, UR, UF, UL, DR, DF, DL, DB, FR, FL, BL, BR)
eoU = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

# R (quart de tour horaire face droite)
cpR = (DFR, UFL, ULB, URF, DRB, DLF, DBL, UBR)
coR = (2, 0, 0, 1, 1, 0, 0, 2)
epR = (FR, UF, UL, UB, BR, DF, DL, DB, DR, FL, BL, UR)
eoR = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

# F (quart de tour horaire face avant)
cpF = (UFL, DLF, ULB, UBR, URF, DFR, DBL, DRB)
coF = (1, 2, 0, 0, 2, 1, 0, 0)
epF = (UR, FL, UL, UB, DR, FR, DL, DB, UF, DF, BL, BR)
eoF = (0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0)

# D (quart de tour horaire face inférieure)
cpD = (URF, UFL, ULB, UBR, DLF, DBL, DRB, DFR)
coD = (0, 0, 0, 0, 0, 0, 0, 0)
epD = (UR, UF, UL, UB, DF, DL, DB, DR, FR, FL, BL, BR)
eoD = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

# L (quart de tour horaire face gauche)
cpL = (URF, ULB, DBL, UBR, DFR, UFL, DLF, DRB)
coL = (0, 1, 2, 0, 0, 2, 1, 0)
epL = (UR, UF, BL, UB, DR, DF, FL, DB, FR, UL, DL, BR)
eoL = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

# B (quart de tour horaire face arrière)
cpB = (URF, UFL, UBR, DRB, DFR, DLF, ULB, DBL)
coB = (0, 0, 1, 2, 0, 0, 2, 1)
epB = (UR, UF, UL, BR, DR, DF, DL, BL, FR, FL, UB, DB)
eoB = (0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1)

# Liste des 6 mouvements de base
MOVE_CUBE = (
    CubieCube(cpU, coU, epU, eoU),  # U
    CubieCube(cpR, coR, epR, eoR),  # R
    CubieCube(cpF, coF, epF, eoF),  # F
    CubieCube(cpD, coD, epD, eoD),  # D
    CubieCube(cpL, coL, epL, eoL),  # L
    CubieCube(cpB, coB, epB, eoB),  # B
)


# =============================================================================
# FACE CUBE - Conversion depuis cubestring
# =============================================================================

class FaceCube:
    """Représentation du cube par les 54 facelets"""
    
    __slots__ = ('f',)
    
    def __init__(self, cube_string="UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"):
        self.f = [COLORS.get(c, U) for c in cube_string]
    
    def to_string(self):
        """Convertit en cubestring de 54 caractères"""
        color_names = ['U', 'R', 'F', 'D', 'L', 'B']
        return ''.join(color_names[c] for c in self.f)
    
    def to_cubie_cube(self):
        """Convertit en CubieCube"""
        cc = CubieCube()
        
        # Coins
        for i in range(8):
            # Trouver l'orientation (où est la facette U ou D)
            for ori in range(3):
                if self.f[CORNER_FACELET[i][ori]] in (U, D):
                    break
            col1 = self.f[CORNER_FACELET[i][(ori + 1) % 3]]
            col2 = self.f[CORNER_FACELET[i][(ori + 2) % 3]]
            
            for j in range(8):
                if col1 == CORNER_COLOR[j][1] and col2 == CORNER_COLOR[j][2]:
                    cc.cp[i] = j
                    cc.co[i] = ori % 3
                    break
        
        # Arêtes
        for i in range(12):
            for j in range(12):
                if (self.f[EDGE_FACELET[i][0]] == EDGE_COLOR[j][0] and
                    self.f[EDGE_FACELET[i][1]] == EDGE_COLOR[j][1]):
                    cc.ep[i] = j
                    cc.eo[i] = 0
                    break
                if (self.f[EDGE_FACELET[i][0]] == EDGE_COLOR[j][1] and
                    self.f[EDGE_FACELET[i][1]] == EDGE_COLOR[j][0]):
                    cc.ep[i] = j
                    cc.eo[i] = 1
                    break
        
        return cc


# =============================================================================
# TABLES DE PRUNING - Stockage optimisé
# =============================================================================

def get_pruning(table, index):
    """Extrait une valeur de pruning (2 valeurs par octet)"""
    if (index & 1) == 0:
        return table[index >> 1] & 0x0f
    else:
        return (table[index >> 1] >> 4) & 0x0f


def set_pruning(table, index, value):
    """Définit une valeur de pruning"""
    idx = index >> 1
    if (index & 1) == 0:
        table[idx] = (table[idx] & 0xf0) | (value & 0x0f)
    else:
        table[idx] = (table[idx] & 0x0f) | ((value & 0x0f) << 4)


# =============================================================================
# GÉNÉRATEUR DE TABLES
# =============================================================================

class Tables:
    """Toutes les tables nécessaires à l'algorithme"""
    
    _instance = None
    
    # Chemin du fichier cache (dans le même répertoire que ce script)
    CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kociemba_tables.pkl")
    CACHE_VERSION = "1.0"  # Incrémenter si le format des tables change
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Tables de mouvement (listes de listes pour accès rapide)
        self.twist_move = None
        self.flip_move = None
        self.FRtoBR_move = None
        self.URFtoDLF_move = None
        self.URtoUL_move = None
        self.UBtoDF_move = None
        self.URtoDF_move = None
        self.merge_URtoUL_UBtoDF = None
        
        # Tables de pruning (bytearrays)
        self.slice_flip_prun = None
        self.slice_twist_prun = None
        self.slice_URFtoDLF_parity_prun = None
        self.slice_URtoDF_parity_prun = None
        
        # Essayer de charger depuis le cache, sinon générer
        if not self._load_from_cache():
            self._generate_all()
            self._save_to_cache()
    
    def _load_from_cache(self) -> bool:
        """Charge les tables depuis le fichier cache si disponible"""
        if not os.path.exists(self.CACHE_FILE):
            return False
        
        try:
            print(f"Chargement des tables depuis {os.path.basename(self.CACHE_FILE)}...")
            t_start = time.time()
            
            with open(self.CACHE_FILE, 'rb') as f:
                data = pickle.load(f)
            
            # Vérifier la version
            if data.get('version') != self.CACHE_VERSION:
                print("  Version du cache obsolète, régénération nécessaire...")
                return False
            
            # Charger les tables
            self.twist_move = data['twist_move']
            self.flip_move = data['flip_move']
            self.FRtoBR_move = data['FRtoBR_move']
            self.URFtoDLF_move = data['URFtoDLF_move']
            self.URtoUL_move = data['URtoUL_move']
            self.UBtoDF_move = data['UBtoDF_move']
            self.URtoDF_move = data['URtoDF_move']
            self.merge_URtoUL_UBtoDF = data['merge_URtoUL_UBtoDF']
            self.slice_flip_prun = data['slice_flip_prun']
            self.slice_twist_prun = data['slice_twist_prun']
            self.slice_URFtoDLF_parity_prun = data['slice_URFtoDLF_parity_prun']
            self.slice_URtoDF_parity_prun = data['slice_URtoDF_parity_prun']
            
            elapsed = time.time() - t_start
            print(f"Tables chargées en {elapsed:.2f} secondes")
            return True
            
        except Exception as e:
            print(f"  Erreur lors du chargement du cache: {e}")
            print("  Régénération des tables...")
            return False
    
    def _save_to_cache(self):
        """Sauvegarde les tables dans le fichier cache"""
        try:
            print(f"Sauvegarde des tables dans {os.path.basename(self.CACHE_FILE)}...")
            
            data = {
                'version': self.CACHE_VERSION,
                'twist_move': self.twist_move,
                'flip_move': self.flip_move,
                'FRtoBR_move': self.FRtoBR_move,
                'URFtoDLF_move': self.URFtoDLF_move,
                'URtoUL_move': self.URtoUL_move,
                'UBtoDF_move': self.UBtoDF_move,
                'URtoDF_move': self.URtoDF_move,
                'merge_URtoUL_UBtoDF': self.merge_URtoUL_UBtoDF,
                'slice_flip_prun': self.slice_flip_prun,
                'slice_twist_prun': self.slice_twist_prun,
                'slice_URFtoDLF_parity_prun': self.slice_URFtoDLF_parity_prun,
                'slice_URtoDF_parity_prun': self.slice_URtoDF_parity_prun,
            }
            
            with open(self.CACHE_FILE, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Afficher la taille du fichier
            size_mb = os.path.getsize(self.CACHE_FILE) / (1024 * 1024)
            print(f"Tables sauvegardées ({size_mb:.1f} MB)")
            
        except Exception as e:
            print(f"  Avertissement: impossible de sauvegarder le cache: {e}")
    
    def _generate_all(self):
        """Génère toutes les tables"""
        print("Génération des tables de mouvement et pruning...")
        print("(Première exécution uniquement, ~2-5 minutes)")
        t_start = time.time()
        
        # Tables de mouvement
        print("  [1/12] twist_move...")
        self.twist_move = self._gen_twist_move()
        
        print("  [2/12] flip_move...")
        self.flip_move = self._gen_flip_move()
        
        print("  [3/12] FRtoBR_move...")
        self.FRtoBR_move = self._gen_FRtoBR_move()
        
        print("  [4/12] URFtoDLF_move...")
        self.URFtoDLF_move = self._gen_URFtoDLF_move()
        
        print("  [5/12] URtoUL_move...")
        self.URtoUL_move = self._gen_URtoUL_move()
        
        print("  [6/12] UBtoDF_move...")
        self.UBtoDF_move = self._gen_UBtoDF_move()
        
        print("  [7/12] URtoDF_move...")
        self.URtoDF_move = self._gen_URtoDF_move()
        
        print("  [8/12] merge_URtoUL_UBtoDF...")
        self.merge_URtoUL_UBtoDF = self._gen_merge_table()
        
        # Tables de pruning
        print("  [9/12] slice_flip_prun...")
        self.slice_flip_prun = self._gen_slice_flip_prun()
        
        print("  [10/12] slice_twist_prun...")
        self.slice_twist_prun = self._gen_slice_twist_prun()
        
        print("  [11/12] slice_URFtoDLF_parity_prun...")
        self.slice_URFtoDLF_parity_prun = self._gen_slice_URFtoDLF_parity_prun()
        
        print("  [12/12] slice_URtoDF_parity_prun...")
        self.slice_URtoDF_parity_prun = self._gen_slice_URtoDF_parity_prun()
        
        elapsed = time.time() - t_start
        print(f"Tables générées en {elapsed:.1f} secondes")
    
    def _gen_twist_move(self):
        """Table de mouvement pour twist (orientation des coins)"""
        table = [[0] * N_MOVE for _ in range(N_TWIST)]
        a = CubieCube()
        for i in range(N_TWIST):
            a.set_twist(i)
            for j in range(6):
                for k in range(3):
                    a.corner_multiply(MOVE_CUBE[j])
                    table[i][3 * j + k] = a.get_twist()
                a.corner_multiply(MOVE_CUBE[j])
        return table
    
    def _gen_flip_move(self):
        """Table de mouvement pour flip (orientation des arêtes)"""
        table = [[0] * N_MOVE for _ in range(N_FLIP)]
        a = CubieCube()
        for i in range(N_FLIP):
            a.set_flip(i)
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    table[i][3 * j + k] = a.get_flip()
                a.edge_multiply(MOVE_CUBE[j])
        return table
    
    def _gen_FRtoBR_move(self):
        """Table de mouvement pour FRtoBR (arêtes du slice)"""
        table = [[0] * N_MOVE for _ in range(N_FRtoBR)]
        a = CubieCube()
        for i in range(N_FRtoBR):
            a.set_FRtoBR(i)
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    table[i][3 * j + k] = a.get_FRtoBR()
                a.edge_multiply(MOVE_CUBE[j])
        return table
    
    def _gen_URFtoDLF_move(self):
        """Table de mouvement pour URFtoDLF (6 premiers coins)"""
        table = [[0] * N_MOVE for _ in range(N_URFtoDLF)]
        a = CubieCube()
        for i in range(N_URFtoDLF):
            a.set_URFtoDLF(i)
            for j in range(6):
                for k in range(3):
                    a.corner_multiply(MOVE_CUBE[j])
                    table[i][3 * j + k] = a.get_URFtoDLF()
                a.corner_multiply(MOVE_CUBE[j])
        return table
    
    def _gen_URtoUL_move(self):
        """Table de mouvement pour URtoUL"""
        table = [[0] * N_MOVE for _ in range(N_URtoUL)]
        a = CubieCube()
        for i in range(N_URtoUL):
            a.set_URtoUL(i)
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    table[i][3 * j + k] = a.get_URtoUL()
                a.edge_multiply(MOVE_CUBE[j])
        return table
    
    def _gen_UBtoDF_move(self):
        """Table de mouvement pour UBtoDF"""
        table = [[0] * N_MOVE for _ in range(N_UBtoDF)]
        a = CubieCube()
        for i in range(N_UBtoDF):
            a.set_UBtoDF(i)
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    table[i][3 * j + k] = a.get_UBtoDF()
                a.edge_multiply(MOVE_CUBE[j])
        return table
    
    def _gen_URtoDF_move(self):
        """Table de mouvement pour URtoDF"""
        table = [[0] * N_MOVE for _ in range(N_URtoDF)]
        a = CubieCube()
        for i in range(N_URtoDF):
            a.set_URtoDF(i)
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(MOVE_CUBE[j])
                    table[i][3 * j + k] = a.get_URtoDF()
                a.edge_multiply(MOVE_CUBE[j])
        return table
    
    def _gen_merge_table(self):
        """Table de fusion URtoUL + UBtoDF -> URtoDF"""
        table = [[0] * 336 for _ in range(336)]
        for uRtoUL in range(336):
            for uBtoDF in range(336):
                a = CubieCube()
                b = CubieCube()
                a.set_URtoUL(uRtoUL)
                b.set_UBtoDF(uBtoDF)
                
                # Fusionner les arêtes
                for i in range(8):
                    if a.ep[i] != BR:
                        if b.ep[i] != BR:
                            table[uRtoUL][uBtoDF] = -1
                            break
                        b.ep[i] = a.ep[i]
                else:
                    table[uRtoUL][uBtoDF] = b.get_URtoDF()
        return table
    
    def _gen_slice_flip_prun(self):
        """Table de pruning Slice+Flip (Phase 1) - optimisée BFS"""
        size = N_SLICE1 * N_FLIP
        table = bytearray([0xff] * ((size >> 1) + 1))
        set_pruning(table, 0, 0)
        
        # BFS
        current = [0]
        depth = 0
        
        while current:
            next_level = []
            for idx in current:
                flip_idx = idx // N_SLICE1
                slice_idx = idx % N_SLICE1
                for mv in range(18):
                    new_slice = self.FRtoBR_move[slice_idx * 24][mv] // 24
                    new_flip = self.flip_move[flip_idx][mv]
                    new_idx = N_SLICE1 * new_flip + new_slice
                    if get_pruning(table, new_idx) == 0x0f:
                        set_pruning(table, new_idx, depth + 1)
                        next_level.append(new_idx)
            current = next_level
            depth += 1
        return table
    
    def _gen_slice_twist_prun(self):
        """Table de pruning Slice+Twist (Phase 1) - optimisée BFS"""
        size = N_SLICE1 * N_TWIST
        table = bytearray([0xff] * ((size >> 1) + 1))
        set_pruning(table, 0, 0)
        
        # BFS
        current = [0]
        depth = 0
        
        while current:
            next_level = []
            for idx in current:
                twist_idx = idx // N_SLICE1
                slice_idx = idx % N_SLICE1
                for mv in range(18):
                    new_slice = self.FRtoBR_move[slice_idx * 24][mv] // 24
                    new_twist = self.twist_move[twist_idx][mv]
                    new_idx = N_SLICE1 * new_twist + new_slice
                    if get_pruning(table, new_idx) == 0x0f:
                        set_pruning(table, new_idx, depth + 1)
                        next_level.append(new_idx)
            current = next_level
            depth += 1
        return table
    
    def _gen_slice_URFtoDLF_parity_prun(self):
        """Table de pruning Slice+URFtoDLF+Parity (Phase 2) - optimisée BFS"""
        size = N_SLICE2 * N_URFtoDLF * N_PARITY
        table = bytearray([0xff] * ((size >> 1) + 1))
        set_pruning(table, 0, 0)
        
        # Mouvements valides en phase 2: U, U2, U', R2, F2, D, D2, D', L2, B2
        phase2_moves = (0, 1, 2, 4, 7, 9, 10, 11, 13, 16)
        
        # BFS avec file
        current = [0]
        depth = 0
        
        while current:
            next_level = []
            for idx in current:
                parity = idx % 2
                URFtoDLF = (idx >> 1) // N_SLICE2
                slice_idx = (idx >> 1) % N_SLICE2
                
                for mv in phase2_moves:
                    new_slice = self.FRtoBR_move[slice_idx][mv] % 24
                    new_URFtoDLF = self.URFtoDLF_move[URFtoDLF][mv]
                    new_parity = PARITY_MOVE[parity][mv]
                    new_idx = (N_SLICE2 * new_URFtoDLF + new_slice) * 2 + new_parity
                    if new_idx < size and get_pruning(table, new_idx) == 0x0f:
                        set_pruning(table, new_idx, depth + 1)
                        next_level.append(new_idx)
            
            current = next_level
            depth += 1
        return table
    
    def _gen_slice_URtoDF_parity_prun(self):
        """Table de pruning Slice+URtoDF+Parity (Phase 2) - optimisée BFS"""
        size = N_SLICE2 * N_URtoDF * N_PARITY
        table = bytearray([0xff] * ((size >> 1) + 1))
        set_pruning(table, 0, 0)
        
        # Mouvements valides en phase 2
        phase2_moves = (0, 1, 2, 4, 7, 9, 10, 11, 13, 16)
        
        # BFS avec file
        current = [0]
        depth = 0
        
        while current:
            next_level = []
            for idx in current:
                parity = idx % 2
                URtoDF = (idx >> 1) // N_SLICE2
                slice_idx = (idx >> 1) % N_SLICE2
                
                for mv in phase2_moves:
                    new_slice = self.FRtoBR_move[slice_idx][mv] % 24
                    new_URtoDF = self.URtoDF_move[URtoDF][mv]
                    new_parity = PARITY_MOVE[parity][mv]
                    new_idx = (N_SLICE2 * new_URtoDF + new_slice) * 2 + new_parity
                    if new_idx < size and get_pruning(table, new_idx) == 0x0f:
                        set_pruning(table, new_idx, depth + 1)
                        next_level.append(new_idx)
            
            current = next_level
            depth += 1
        return table


# =============================================================================
# ALGORITHME DE RECHERCHE TWO-PHASE
# =============================================================================

class Search:
    """Algorithme Two-Phase de Kociemba"""
    
    AXIS_NAMES = ('U', 'R', 'F', 'D', 'L', 'B')
    POWER_NAMES = (None, ' ', '2 ', "' ")
    
    def __init__(self, tables):
        self.tables = tables
        # Piles pour la recherche
        self.ax = [0] * 31
        self.po = [0] * 31
        self.flip = [0] * 31
        self.twist = [0] * 31
        self.slice_ = [0] * 31
        self.parity = [0] * 31
        self.URFtoDLF = [0] * 31
        self.FRtoBR = [0] * 31
        self.URtoUL = [0] * 31
        self.UBtoDF = [0] * 31
        self.URtoDF = [0] * 31
        self.minDistPhase1 = [0] * 31
        self.minDistPhase2 = [0] * 31
    
    def _solution_string(self, length, sep_pos=-1):
        """Convertit la solution en notation standard"""
        parts = []
        for i in range(length):
            if self.POWER_NAMES[self.po[i]] is not None:
                parts.append(self.AXIS_NAMES[self.ax[i]] + self.POWER_NAMES[self.po[i]])
            else:
                parts.append(self.AXIS_NAMES[self.ax[i]])
            if i == sep_pos - 1:
                parts.append('. ')
        return ''.join(parts).strip()
    
    def solve(self, cube_string, max_depth=21, timeout=10.0, separator=False):
        """
        Résout le cube.
        
        Args:
            cube_string: String 54 caractères (URFDLB)
            max_depth: Profondeur maximale
            timeout: Temps limite en secondes
            separator: Afficher le séparateur phase1/phase2
        
        Returns:
            String de la solution ou message d'erreur
        """
        # Validation de l'entrée
        if len(cube_string) != 54:
            return "Error: cubestring doit faire 54 caractères"
        
        count = [0] * 6
        for c in cube_string:
            if c not in COLORS:
                return f"Error: caractère invalide '{c}'"
            count[COLORS[c]] += 1
        
        for i in range(6):
            if count[i] != 9:
                return f"Error: nombre incorrect de '{COLOR_NAMES[i]}'"
        
        # Conversion en CubieCube
        fc = FaceCube(cube_string)
        cc = fc.to_cubie_cube()
        
        # Vérification de validité
        err = cc.verify()
        if err != 0:
            errors = {
                -1: "Error: arête incorrecte",
                -2: "Error: coin incorrect",
                -3: "Error: flip incorrect",
                -5: "Error: twist incorrect",
                -6: "Error: parité incorrecte",
            }
            return errors.get(err, f"Error: code {err}")
        
        # Initialisation
        self.po[0] = 0
        self.ax[0] = 0
        self.flip[0] = cc.get_flip()
        self.twist[0] = cc.get_twist()
        self.parity[0] = cc.corner_parity()
        self.slice_[0] = cc.get_FRtoBR() // 24
        self.URFtoDLF[0] = cc.get_URFtoDLF()
        self.FRtoBR[0] = cc.get_FRtoBR()
        self.URtoUL[0] = cc.get_URtoUL()
        self.UBtoDF[0] = cc.get_UBtoDF()
        
        # Cube déjà résolu ?
        if (self.flip[0] == 0 and self.twist[0] == 0 and 
            self.slice_[0] == 0 and self.FRtoBR[0] == 0 and
            self.URFtoDLF[0] == 0 and self.parity[0] == 0):
            return ""
        
        self.minDistPhase1[1] = 1
        n = 0
        busy = False
        depth_phase1 = 1
        
        t_start = time.time()
        
        # Boucle principale IDA*
        while True:
            # Phase 1: atteindre le groupe G1
            while True:
                if depth_phase1 - n > self.minDistPhase1[n + 1] and not busy:
                    # Descendre dans l'arbre
                    if self.ax[n] in (0, 3):  # U ou D
                        n += 1
                        self.ax[n] = 1
                    else:
                        n += 1
                        self.ax[n] = 0
                    self.po[n] = 1
                else:
                    # Essayer le prochain mouvement
                    self.po[n] += 1
                    if self.po[n] > 3:
                        # Changer d'axe
                        while True:
                            self.ax[n] += 1
                            if self.ax[n] > 5:
                                # Timeout?
                                if time.time() - t_start > timeout:
                                    return "Error: timeout"
                                
                                if n == 0:
                                    if depth_phase1 >= max_depth:
                                        return "Error: pas de solution dans la limite"
                                    depth_phase1 += 1
                                    self.ax[n] = 0
                                    self.po[n] = 1
                                    busy = False
                                    break
                                else:
                                    n -= 1
                                    busy = True
                                    break
                            else:
                                self.po[n] = 1
                                busy = False
                            
                            # Éviter les mouvements redondants
                            if n == 0 or (self.ax[n - 1] != self.ax[n] and 
                                         self.ax[n - 1] - 3 != self.ax[n]):
                                break
                    else:
                        busy = False
                
                if not busy:
                    break
            
            # Calculer nouvelles coordonnées phase 1
            mv = 3 * self.ax[n] + self.po[n] - 1
            self.flip[n + 1] = self.tables.flip_move[self.flip[n]][mv]
            self.twist[n + 1] = self.tables.twist_move[self.twist[n]][mv]
            self.slice_[n + 1] = self.tables.FRtoBR_move[self.slice_[n] * 24][mv] // 24
            # Note: FRtoBR est mis à jour séparément dans _phase2
            
            self.minDistPhase1[n + 1] = max(
                get_pruning(self.tables.slice_flip_prun,
                           N_SLICE1 * self.flip[n + 1] + self.slice_[n + 1]),
                get_pruning(self.tables.slice_twist_prun,
                           N_SLICE1 * self.twist[n + 1] + self.slice_[n + 1])
            )
            
            # Solution trouvée pour phase 1?
            if self.minDistPhase1[n + 1] == 0 and n >= depth_phase1 - 5:
                self.minDistPhase1[n + 1] = 10
                if n == depth_phase1 - 1:
                    # Lancer phase 2
                    s = self._phase2(depth_phase1, max_depth, t_start, timeout)
                    if s == -2:
                        # Timeout dans phase 2
                        return "Error: timeout"
                    if s >= 0:
                        if (s == depth_phase1 or
                            (self.ax[depth_phase1 - 1] != self.ax[depth_phase1] and
                             self.ax[depth_phase1 - 1] != self.ax[depth_phase1] + 3)):
                            if separator:
                                return self._solution_string(s, depth_phase1)
                            return self._solution_string(s)
    
    def _phase2(self, depth_phase1, max_depth, t_start, timeout):
        """Phase 2: résolution finale dans G1"""
        max_depth_phase2 = min(10, max_depth - depth_phase1)
        
        # Calculer coordonnées à la fin de phase 1
        for i in range(depth_phase1):
            mv = 3 * self.ax[i] + self.po[i] - 1
            self.URFtoDLF[i + 1] = self.tables.URFtoDLF_move[self.URFtoDLF[i]][mv]
            self.FRtoBR[i + 1] = self.tables.FRtoBR_move[self.FRtoBR[i]][mv]
            self.parity[i + 1] = PARITY_MOVE[self.parity[i]][mv]
        
        # Vérifier que FRtoBR est bien < 24 (arêtes slice dans le slice)
        if self.FRtoBR[depth_phase1] >= N_SLICE2:
            # Ce ne devrait pas arriver si phase 1 a réussi
            return -1
        
        # Vérifier si phase 2 possible avec d1
        idx1 = (N_SLICE2 * self.URFtoDLF[depth_phase1] + self.FRtoBR[depth_phase1]) * 2 + self.parity[depth_phase1]
        d1 = get_pruning(self.tables.slice_URFtoDLF_parity_prun, idx1)
        if d1 > max_depth_phase2:
            return -1
        
        # Calculer URtoUL et UBtoDF
        for i in range(depth_phase1):
            mv = 3 * self.ax[i] + self.po[i] - 1
            self.URtoUL[i + 1] = self.tables.URtoUL_move[self.URtoUL[i]][mv]
            self.UBtoDF[i + 1] = self.tables.UBtoDF_move[self.UBtoDF[i]][mv]
        
        # Fusionner URtoUL et UBtoDF
        # Attention : merge_URtoUL_UBtoDF est une table 336x336 (sous-ensemble phase 2).
        # Si les coordonnées URtoUL / UBtoDF sortent de ce sous-ensemble, cette branche
        # n'est pas valide pour la phase 2.
        rows_merge = len(self.tables.merge_URtoUL_UBtoDF)
        cols_merge = len(self.tables.merge_URtoUL_UBtoDF[0]) if rows_merge > 0 else 0
        if (self.URtoUL[depth_phase1] >= rows_merge or
            self.UBtoDF[depth_phase1] >= cols_merge):
            return -1
        self.URtoDF[depth_phase1] = self.tables.merge_URtoUL_UBtoDF[
            self.URtoUL[depth_phase1]][self.UBtoDF[depth_phase1]]
        
        # Vérifier avec d2
        idx2 = (N_SLICE2 * self.URtoDF[depth_phase1] + self.FRtoBR[depth_phase1]) * 2 + self.parity[depth_phase1]
        d2 = get_pruning(self.tables.slice_URtoDF_parity_prun, idx2)
        if d2 > max_depth_phase2:
            return -1
        
        self.minDistPhase2[depth_phase1] = max(d1, d2)
        if self.minDistPhase2[depth_phase1] == 0:
            return depth_phase1
        
        # Initialiser recherche phase 2
        depth_phase2 = 1
        n = depth_phase1
        busy = False
        self.po[depth_phase1] = 0
        self.ax[depth_phase1] = 0
        self.minDistPhase2[n + 1] = 1
        
        # Boucle phase 2
        while True:
            while True:
                if depth_phase1 + depth_phase2 - n > self.minDistPhase2[n + 1] and not busy:
                    if self.ax[n] in (0, 3):  # U ou D -> aller à R2
                        n += 1
                        self.ax[n] = 1
                        self.po[n] = 2  # R2, pas R
                    else:
                        n += 1
                        self.ax[n] = 0
                        self.po[n] = 1
                else:
                    if self.ax[n] in (0, 3):
                        self.po[n] += 1
                    else:
                        self.po[n] += 2  # Seulement R2, F2, L2, B2
                    
                    if self.po[n] > 3:
                        while True:
                            self.ax[n] += 1
                            if self.ax[n] > 5:
                                # Vérifier timeout dans phase 2
                                if time.time() - t_start > timeout:
                                    return -2  # Timeout
                                
                                if n == depth_phase1:
                                    if depth_phase2 >= max_depth_phase2:
                                        return -1
                                    depth_phase2 += 1
                                    self.ax[n] = 0
                                    self.po[n] = 1
                                    busy = False
                                    break
                                else:
                                    n -= 1
                                    busy = True
                                    break
                            else:
                                if self.ax[n] in (0, 3):
                                    self.po[n] = 1
                                else:
                                    self.po[n] = 2
                                busy = False
                            
                            if n == depth_phase1 or (self.ax[n - 1] != self.ax[n] and
                                                      self.ax[n - 1] - 3 != self.ax[n]):
                                break
                    else:
                        busy = False
                
                if not busy:
                    break
            
            # Calculer coordonnées phase 2
            mv = 3 * self.ax[n] + self.po[n] - 1
            self.URFtoDLF[n + 1] = self.tables.URFtoDLF_move[self.URFtoDLF[n]][mv]
            self.FRtoBR[n + 1] = self.tables.FRtoBR_move[self.FRtoBR[n]][mv]
            self.parity[n + 1] = PARITY_MOVE[self.parity[n]][mv]
            self.URtoDF[n + 1] = self.tables.URtoDF_move[self.URtoDF[n]][mv]
            
            idx1 = (N_SLICE2 * self.URFtoDLF[n + 1] + self.FRtoBR[n + 1]) * 2 + self.parity[n + 1]
            idx2 = (N_SLICE2 * self.URtoDF[n + 1] + self.FRtoBR[n + 1]) * 2 + self.parity[n + 1]
            
            self.minDistPhase2[n + 1] = max(
                get_pruning(self.tables.slice_URFtoDLF_parity_prun, idx1),
                get_pruning(self.tables.slice_URtoDF_parity_prun, idx2)
            )
            
            if self.minDistPhase2[n + 1] == 0:
                return depth_phase1 + depth_phase2


# =============================================================================
# INTERFACE PUBLIQUE
# =============================================================================

_tables = None


def _get_tables():
    """Retourne les tables (singleton, lazy loading)"""
    global _tables
    if _tables is None:
        _tables = Tables()
    return _tables


def solve(cube_string, max_depth=21, timeout=10.0, separator=False):
    """
    Résout un Rubik's Cube.
    
    Args:
        cube_string: String de 54 caractères représentant l'état du cube.
                    Format: UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB
                    où chaque face est lue de gauche à droite, de haut en bas.
        max_depth: Profondeur maximale de recherche (défaut: 21)
        timeout: Temps limite en secondes (défaut: 10.0)
        separator: Si True, affiche un '.' entre phase 1 et phase 2
    
    Returns:
        str: La solution en notation standard (ex: "U R2 F' D B2")
             ou un message d'erreur commençant par "Error:"
    
    Exemple:
        >>> solve("UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB")
        ''  # Cube déjà résolu
        >>> solve("DRLUUBFBRBLURRLBFFUFRFBDUDDRFDDLLDRLDUBFLUBLRFBBDUULF")
        "D2 R' D' F2 B D R2 D2 R' F2 D' F2 U' B2 L2 U2 D R2 U"
    """
    tables = _get_tables()
    search = Search(tables)
    return search.solve(cube_string, max_depth, timeout, separator)


def init_tables():
    """
    Initialise les tables de pruning à l'avance.
    Utile pour éviter le délai au premier appel de solve().
    """
    _get_tables()


# =============================================================================
# EXEMPLE D'UTILISATION
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Solver Kociemba - Two-Phase Algorithm")
    print("Implémentation Python pure, sans dépendance externe")
    print("=" * 60)
    print()
    
    # Test 1: Cube résolu
    print("Test 1: Cube résolu")
    cube = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
    result = solve(cube)
    print(f"  Entrée:   {cube}")
    print(f"  Solution: '{result}'")
    print()
    
    # Test 2: Après mouvement R
    print("Test 2: Un seul mouvement (R)")
    cube = "UUFUUFUUFRRRRRRRRRFFDFFDFFDDDBDDBDDBLLLLLLLLLUBBUBBUBB"
    t_start = time.time()
    result = solve(cube)
    elapsed = time.time() - t_start
    print(f"  Entrée:   {cube}")
    print(f"  Solution: {result}")
    print(f"  Temps:    {elapsed:.3f}s")
    print()
    
    # Test 3: Scramble simple
    print("Test 3: Scramble R U R' U'")
    cube = "RURUUFUUFFRRRRRRRRUFFUFFUFFDDDDDDDDDBLLLLLLLLBBBLBBBBB"
    t_start = time.time()
    result = solve(cube, timeout=30.0)
    elapsed = time.time() - t_start
    move_count = len(result.split()) if result and not result.startswith("Error") else 0
    print(f"  Solution: {result}")
    print(f"  Coups:    {move_count}")
    print(f"  Temps:    {elapsed:.3f}s")
    print()
    
    # Test 4: Scramble aléatoire
    print("Test 4: Scramble aléatoire complexe")
    cube = "DRLUUBFBRBLURRLBFFUFRFBDUDDRFDDLLDRLDUBFLUBLRFBBDUULF"
    t_start = time.time()
    result = solve(cube, timeout=30.0)
    elapsed = time.time() - t_start
    move_count = len(result.split()) if result and not result.startswith("Error") else 0
    print(f"  Entrée:   {cube}")
    print(f"  Solution: {result}")
    print(f"  Coups:    {move_count}")
    print(f"  Temps:    {elapsed:.3f}s")
    print()
    
    # Test 5: Solution avec séparateur
    print("Test 5: Même scramble avec séparateur phase1/phase2")
    result = solve(cube, timeout=30.0, separator=True)
    print(f"  Solution: {result}")
    print()
    
    print("=" * 60)
    print("Tests terminés!")
    print("=" * 60)
