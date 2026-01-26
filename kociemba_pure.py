"""
Kociemba Two-Phase Algorithm - Implémentation Python Pure
============================================================

Implémentation standalone de l'algorithme Kociemba sans dépendance externe.

UTILISATION:
    from kociemba_pure import solve
    
    # Résoudre un cube mélangé
    # Format: 54 caractères URFDLB (9 par face, dans cet ordre)
    solution = solve("DRLUUBFBRBLURRLBFFUFRFBDUDDRFDDLLDRLDUBFLUBLRFBBDUULF")
    print(solution)  # ex: "R U R' F2 D2 ..."

TABLES DE PRUNING:
    - Si kociemba est installé : utilise ses tables (~instant)
    - Sinon : génère les tables au 1er lancement (~5 min, puis cachées)

Basé sur le travail de Herbert Kociemba et l'implémentation pykociemba.
Algorithme Two-Phase:
    - Phase 1: Amène le cube dans le sous-groupe G1 = <U,D,R2,L2,F2,B2>
    - Phase 2: Résout dans G1 avec uniquement U, D, R2, L2, F2, B2
"""

import os
import pickle
from pathlib import Path

# =============================================================================
# CONSTANTES
# =============================================================================

# Couleurs
U, R, F, D, L, B = 0, 1, 2, 3, 4, 5
COLORS = {'U': U, 'R': R, 'F': F, 'D': D, 'L': L, 'B': B}
COLOR_NAMES = ['U', 'R', 'F', 'D', 'L', 'B']

# Coins (positions)
URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB = range(8)

# Arêtes (positions)
UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR = range(12)

# Facelets (54 positions sur le cube)
# U1-U9: 0-8, R1-R9: 9-17, F1-F9: 18-26, D1-D9: 27-35, L1-L9: 36-44, B1-B9: 45-53
U1, U2, U3, U4, U5, U6, U7, U8, U9 = range(9)
R1, R2, R3, R4, R5, R6, R7, R8, R9 = range(9, 18)
F1, F2, F3, F4, F5, F6, F7, F8, F9 = range(18, 27)
D1, D2, D3, D4, D5, D6, D7, D8, D9 = range(27, 36)
L1, L2, L3, L4, L5, L6, L7, L8, L9 = range(36, 45)
B1, B2, B3, B4, B5, B6, B7, B8, B9 = range(45, 54)

# Mappings coins -> facelets
CORNER_FACELET = [
    [U9, R1, F3], [U7, F1, L3], [U1, L1, B3], [U3, B1, R3],
    [D3, F9, R7], [D1, L9, F7], [D7, B9, L7], [D9, R9, B7],
]

# Mappings arêtes -> facelets
EDGE_FACELET = [
    [U6, R2], [U8, F2], [U4, L2], [U2, B2], [D6, R8], [D2, F8],
    [D4, L8], [D8, B8], [F6, R4], [F4, L6], [B6, L4], [B4, R6],
]

# Couleurs des coins
CORNER_COLOR = [
    [U, R, F], [U, F, L], [U, L, B], [U, B, R],
    [D, F, R], [D, L, F], [D, B, L], [D, R, B],
]

# Couleurs des arêtes
EDGE_COLOR = [
    [U, R], [U, F], [U, L], [U, B], [D, R], [D, F],
    [D, L], [D, B], [F, R], [F, L], [B, L], [B, R],
]

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

# Dossier de cache (cherche d'abord dans kociemba installé, sinon local)
def get_cache_dir():
    """Trouve le dossier de cache (préfère celui de kociemba si installé)"""
    # Essayer d'utiliser les tables de kociemba si installé
    try:
        import kociemba
        kociemba_path = Path(kociemba.__file__).parent / "pykociemba" / "prunetables"
        if kociemba_path.exists():
            return kociemba_path
    except ImportError:
        pass
    
    # Sinon utiliser un dossier local
    local_cache = Path(__file__).parent / "kociemba_cache"
    local_cache.mkdir(exist_ok=True)
    return local_cache

CACHE_DIR = None  # Initialisé à la première utilisation

# =============================================================================
# UTILITAIRES MATHÉMATIQUES
# =============================================================================

def Cnk(n, k):
    """Combinaisons: n choose k"""
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
    """Représentation du cube au niveau des cubies (coins et arêtes)"""
    
    def __init__(self, cp=None, co=None, ep=None, eo=None):
        # Permutation des coins
        self.cp = list(cp) if cp else [URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB]
        # Orientation des coins (0, 1, 2)
        self.co = list(co) if co else [0] * 8
        # Permutation des arêtes
        self.ep = list(ep) if ep else [UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR]
        # Orientation des arêtes (0, 1)
        self.eo = list(eo) if eo else [0] * 12
    
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
    
    # === Coordonnées Phase 1 ===
    
    def get_twist(self):
        """Orientation des coins: 0 <= twist < 2187"""
        ret = 0
        for i in range(7):  # Le 8ème est déterminé
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
        for i in range(11):  # La 12ème est déterminée
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
        """Position des arêtes FR, FL, BL, BR (permutation + combinaison)"""
        a = 0
        x = 0
        edge4 = [None] * 4
        # compute the index a < (12 choose 4) and the permutation array
        for j in range(11, -1, -1):  # BR to UR
            if FR <= self.ep[j] <= BR:
                a += Cnk(11 - j, x + 1)
                edge4[3 - x] = self.ep[j]
                x += 1
        
        b = 0
        for j in range(3, 0, -1):  # compute the index b < 4! for the permutation
            k = 0
            while edge4[j] != j + 8:  # FR=8, FL=9, BL=10, BR=11
                rotate_left(edge4, 0, j)
                k += 1
            b = (j + 1) * b + k
        return 24 * a + b
    
    def set_FRtoBR(self, idx):
        """Définit la position des arêtes FR, FL, BL, BR"""
        sliceEdge = [FR, FL, BL, BR]
        otherEdge = [UR, UF, UL, UB, DR, DF, DL, DB]
        b = idx % 24   # Permutation
        a = idx // 24   # Combination
        
        for i in range(12):
            self.ep[i] = DB     # Use DB to invalidate all edges

        for j in range(1, 4):  # generate permutation from index b
            k = b % (j + 1)
            b //= (j + 1)
            while k > 0:
                k -= 1
                rotate_right(sliceEdge, 0, j)

        x = 3   # generate combination and set slice edges
        for j in range(12):  # UR to BR
            if a - Cnk(11 - j, x + 1) >= 0:
                self.ep[j] = sliceEdge[3 - x]
                a -= Cnk(11 - j, x + 1)
                x -= 1
        
        x = 0   # set the remaining edges UR..DB
        for j in range(12):
            if self.ep[j] == DB:
                self.ep[j] = otherEdge[x]
                x += 1
    
    # === Coordonnées Phase 2 ===
    
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
        a, b = 0, 0
        x = 0
        corner6 = [0] * 6
        for j in range(8):
            if self.cp[j] <= DLF:
                a += Cnk(j, x + 1)
                corner6[x] = self.cp[j]
                x += 1
        for j in range(5):
            k = 0
            while corner6[j] != j:
                rotate_left(corner6, j, 5)
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
        
        for j in range(5, -1, -1):
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
        a, b = 0, 0
        x = 0
        edge3 = [0] * 3
        for j in range(12):
            if self.ep[j] <= UL:
                a += Cnk(j, x + 1)
                edge3[x] = self.ep[j]
                x += 1
        for j in range(2):
            k = 0
            while edge3[j] != j:
                rotate_left(edge3, j, 2)
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
        
        for j in range(2, -1, -1):
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
        a, b = 0, 0
        x = 0
        edge3 = [0] * 3
        for j in range(12):
            if UB <= self.ep[j] <= DF:
                a += Cnk(j, x + 1)
                edge3[x] = self.ep[j]
                x += 1
        for j in range(2):
            k = 0
            while edge3[j] != j + UB:
                rotate_left(edge3, j, 2)
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
        
        for j in range(2, -1, -1):
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
        a, b = 0, 0
        x = 0
        edge6 = [0] * 6
        for j in range(12):
            if self.ep[j] <= DF:
                a += Cnk(j, x + 1)
                edge6[x] = self.ep[j]
                x += 1
        for j in range(5):
            k = 0
            while edge6[j] != j:
                rotate_left(edge6, j, 5)
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
        
        for j in range(5, -1, -1):
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
    
    def verify(self):
        """Vérifie si le cube est valide"""
        # Vérifier permutation des coins
        sum_corners = sum(self.co)
        if sum_corners % 3 != 0:
            return -5  # Twist error
        
        # Vérifier permutation des arêtes
        sum_edges = sum(self.eo)
        if sum_edges % 2 != 0:
            return -3  # Flip error
        
        # Vérifier parité
        edge_parity = 0
        for i in range(11, 0, -1):
            for j in range(i - 1, -1, -1):
                if self.ep[j] > self.ep[i]:
                    edge_parity += 1
        
        if edge_parity % 2 != self.corner_parity():
            return -6  # Parity error
        
        return 0


# === Définition des 6 mouvements de base ===

# U
cpU = [UBR, URF, UFL, ULB, DFR, DLF, DBL, DRB]
coU = [0, 0, 0, 0, 0, 0, 0, 0]
epU = [UB, UR, UF, UL, DR, DF, DL, DB, FR, FL, BL, BR]
eoU = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# R
cpR = [DFR, UFL, ULB, URF, DRB, DLF, DBL, UBR]
coR = [2, 0, 0, 1, 1, 0, 0, 2]
epR = [FR, UF, UL, UB, BR, DF, DL, DB, DR, FL, BL, UR]
eoR = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# F
cpF = [UFL, DLF, ULB, UBR, URF, DFR, DBL, DRB]
coF = [1, 2, 0, 0, 2, 1, 0, 0]
epF = [UR, FL, UL, UB, DR, FR, DL, DB, UF, DF, BL, BR]
eoF = [0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0]

# D
cpD = [URF, UFL, ULB, UBR, DLF, DBL, DRB, DFR]
coD = [0, 0, 0, 0, 0, 0, 0, 0]
epD = [UR, UF, UL, UB, DF, DL, DB, DR, FR, FL, BL, BR]
eoD = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# L
cpL = [URF, ULB, DBL, UBR, DFR, UFL, DLF, DRB]
coL = [0, 1, 2, 0, 0, 2, 1, 0]
epL = [UR, UF, BL, UB, DR, DF, FL, DB, FR, UL, DL, BR]
eoL = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# B
cpB = [URF, UFL, UBR, DRB, DFR, DLF, ULB, DBL]
coB = [0, 0, 1, 2, 0, 0, 2, 1]
epB = [UR, UF, UL, BR, DR, DF, DL, BL, FR, FL, UB, DB]
eoB = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1]

# Liste des 6 mouvements de base (quart de tour)
MOVE_CUBE = [
    CubieCube(cpU, coU, epU, eoU),  # U
    CubieCube(cpR, coR, epR, eoR),  # R
    CubieCube(cpF, coF, epF, eoF),  # F
    CubieCube(cpD, coD, epD, eoD),  # D
    CubieCube(cpL, coL, epL, eoL),  # L
    CubieCube(cpB, coB, epB, eoB),  # B
]


# =============================================================================
# FACE CUBE - Représentation par facelets
# =============================================================================

class FaceCube:
    """Représentation du cube par les 54 facelets"""
    
    def __init__(self, cube_string="UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"):
        self.f = [COLORS[c] for c in cube_string]
    
    def to_cubie_cube(self):
        """Convertit en CubieCube"""
        cc = CubieCube()
        
        # Coins
        for i in range(8):
            for ori in range(3):
                if self.f[CORNER_FACELET[i][ori]] in [U, D]:
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
# TABLES DE PRUNING
# =============================================================================

def get_pruning(table, index):
    """Extrait une valeur de pruning (2 valeurs par byte)"""
    if (index & 1) == 0:
        return table[index // 2] & 0x0f
    else:
        return (table[index // 2] & 0xf0) >> 4


def set_pruning(table, index, value):
    """Définit une valeur de pruning"""
    if (index & 1) == 0:
        table[index // 2] &= 0xf0 | value
    else:
        table[index // 2] &= 0x0f | (value << 4)


class PruneTables:
    """Gestion des tables de pruning"""
    
    def __init__(self):
        global CACHE_DIR
        if CACHE_DIR is None:
            CACHE_DIR = get_cache_dir()
        self.cache_dir = CACHE_DIR
        
        # Tables de mouvement
        self.twist_move = None
        self.flip_move = None
        self.FRtoBR_move = None
        self.URFtoDLF_move = None
        self.URtoUL_move = None
        self.UBtoDF_move = None
        self.URtoDF_move = None
        self.merge_URtoUL_and_UBtoDF = None
        
        # Tables de pruning
        self.slice_flip_prun = None
        self.slice_twist_prun = None
        self.slice_URFtoDLF_parity_prun = None
        self.slice_URtoDF_parity_prun = None
        
        # Parité
        self.parity_move = [
            [1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1],
            [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0]
        ]
        
        self._load_or_generate_all()
    
    def _load_cache(self, name):
        """Charge une table depuis le cache"""
        path = self.cache_dir / f"{name}.pkl"
        if path.exists():
            with open(path, 'rb') as f:
                return pickle.load(f)
        return None
    
    def _save_cache(self, obj, name):
        """Sauvegarde une table dans le cache"""
        # Ne sauvegarde que si on n'utilise pas le cache de kociemba
        if "pykociemba" not in str(self.cache_dir):
            path = self.cache_dir / f"{name}.pkl"
            with open(path, 'wb') as f:
                pickle.dump(obj, f)
    
    def _load_or_generate_all(self):
        """Charge ou génère toutes les tables"""
        print(f"Chargement des tables depuis {self.cache_dir}...")
        
        # Tables de mouvement - noms compatibles kociemba
        self.twist_move = self._load_cache('twistMove')
        if self.twist_move is None:
            print("  Génération twistMove...")
            self.twist_move = self._generate_twist_move()
            self._save_cache(self.twist_move, 'twistMove')
        
        self.flip_move = self._load_cache('flipMove')
        if self.flip_move is None:
            print("  Génération flipMove...")
            self.flip_move = self._generate_flip_move()
            self._save_cache(self.flip_move, 'flipMove')
        
        self.FRtoBR_move = self._load_cache('FRtoBR_Move')
        if self.FRtoBR_move is None:
            print("  Génération FRtoBR_Move...")
            self.FRtoBR_move = self._generate_FRtoBR_move()
            self._save_cache(self.FRtoBR_move, 'FRtoBR_Move')
        
        self.URFtoDLF_move = self._load_cache('URFtoDLF_Move')
        if self.URFtoDLF_move is None:
            print("  Génération URFtoDLF_Move...")
            self.URFtoDLF_move = self._generate_URFtoDLF_move()
            self._save_cache(self.URFtoDLF_move, 'URFtoDLF_Move')
        
        self.URtoUL_move = self._load_cache('URtoUL_Move')
        if self.URtoUL_move is None:
            print("  Génération URtoUL_Move...")
            self.URtoUL_move = self._generate_URtoUL_move()
            self._save_cache(self.URtoUL_move, 'URtoUL_Move')
        
        self.UBtoDF_move = self._load_cache('UBtoDF_Move')
        if self.UBtoDF_move is None:
            print("  Génération UBtoDF_Move...")
            self.UBtoDF_move = self._generate_UBtoDF_move()
            self._save_cache(self.UBtoDF_move, 'UBtoDF_Move')
        
        self.URtoDF_move = self._load_cache('URtoDF_Move')
        if self.URtoDF_move is None:
            print("  Génération URtoDF_Move...")
            self.URtoDF_move = self._generate_URtoDF_move()
            self._save_cache(self.URtoDF_move, 'URtoDF_Move')
        
        self.merge_URtoUL_and_UBtoDF = self._load_cache('MergeURtoULandUBtoDF')
        if self.merge_URtoUL_and_UBtoDF is None:
            print("  Génération MergeURtoULandUBtoDF...")
            self.merge_URtoUL_and_UBtoDF = self._generate_merge_URtoUL_and_UBtoDF()
            self._save_cache(self.merge_URtoUL_and_UBtoDF, 'MergeURtoULandUBtoDF')
        
        # Tables de pruning - noms compatibles kociemba
        self.slice_flip_prun = self._load_cache('Slice_Flip_Prun')
        if self.slice_flip_prun is None:
            print("  Génération Slice_Flip_Prun...")
            self.slice_flip_prun = self._generate_slice_flip_prun()
            self._save_cache(self.slice_flip_prun, 'Slice_Flip_Prun')
        
        self.slice_twist_prun = self._load_cache('Slice_Twist_Prun')
        if self.slice_twist_prun is None:
            print("  Génération Slice_Twist_Prun...")
            self.slice_twist_prun = self._generate_slice_twist_prun()
            self._save_cache(self.slice_twist_prun, 'Slice_Twist_Prun')
        
        self.slice_URFtoDLF_parity_prun = self._load_cache('Slice_URFtoDLF_Parity_Prun')
        if self.slice_URFtoDLF_parity_prun is None:
            print("  Génération Slice_URFtoDLF_Parity_Prun...")
            self.slice_URFtoDLF_parity_prun = self._generate_slice_URFtoDLF_parity_prun()
            self._save_cache(self.slice_URFtoDLF_parity_prun, 'Slice_URFtoDLF_Parity_Prun')
        
        self.slice_URtoDF_parity_prun = self._load_cache('Slice_URtoDF_Parity_Prun')
        if self.slice_URtoDF_parity_prun is None:
            print("  Génération Slice_URtoDF_Parity_Prun...")
            self.slice_URtoDF_parity_prun = self._generate_slice_URtoDF_parity_prun()
            self._save_cache(self.slice_URtoDF_parity_prun, 'Slice_URtoDF_Parity_Prun')
        
        print("Tables chargées!")
    
    def _generate_twist_move(self):
        """Génère la table de mouvement pour twist"""
        table = [[0] * N_MOVE for _ in range(N_TWIST)]
        a = CubieCube()
        for i in range(N_TWIST):
            a.set_twist(i)
            for j in range(6):
                for k in range(3):
                    a.corner_multiply(MOVE_CUBE[j])
                    table[i][3 * j + k] = a.get_twist()
                a.corner_multiply(MOVE_CUBE[j])  # Restaure
        return table
    
    def _generate_flip_move(self):
        """Génère la table de mouvement pour flip"""
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
    
    def _generate_FRtoBR_move(self):
        """Génère la table de mouvement pour FRtoBR"""
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
    
    def _generate_URFtoDLF_move(self):
        """Génère la table de mouvement pour URFtoDLF"""
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
    
    def _generate_URtoUL_move(self):
        """Génère la table de mouvement pour URtoUL"""
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
    
    def _generate_UBtoDF_move(self):
        """Génère la table de mouvement pour UBtoDF"""
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
    
    def _generate_URtoDF_move(self):
        """Génère la table de mouvement pour URtoDF"""
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
    
    def _generate_merge_URtoUL_and_UBtoDF(self):
        """Génère la table de fusion"""
        table = [[0] * 336 for _ in range(336)]
        for uRtoUL in range(336):
            for uBtoDF in range(336):
                a = CubieCube()
                b = CubieCube()
                a.set_URtoUL(uRtoUL)
                b.set_UBtoDF(uBtoDF)
                
                # Fusionner
                ok = True
                for i in range(8):
                    if a.ep[i] != BR:
                        if b.ep[i] != BR:
                            ok = False
                            break
                        b.ep[i] = a.ep[i]
                
                if ok:
                    table[uRtoUL][uBtoDF] = b.get_URtoDF()
                else:
                    table[uRtoUL][uBtoDF] = -1
        return table
    
    def _generate_slice_flip_prun(self):
        """Génère la table de pruning Slice+Flip"""
        table = bytearray([0xff] * (N_SLICE1 * N_FLIP // 2 + 1))
        depth = 0
        set_pruning(table, 0, 0)
        done = 1
        
        while done != N_SLICE1 * N_FLIP:
            for i in range(N_SLICE1 * N_FLIP):
                flip = i // N_SLICE1
                slice_ = i % N_SLICE1
                if get_pruning(table, i) == depth:
                    for j in range(18):
                        new_slice = self.FRtoBR_move[slice_ * 24][j] // 24
                        new_flip = self.flip_move[flip][j]
                        if get_pruning(table, N_SLICE1 * new_flip + new_slice) == 0x0f:
                            set_pruning(table, N_SLICE1 * new_flip + new_slice, (depth + 1) & 0xff)
                            done += 1
            depth += 1
        return table
    
    def _generate_slice_twist_prun(self):
        """Génère la table de pruning Slice+Twist"""
        table = bytearray([0xff] * (N_SLICE1 * N_TWIST // 2 + 1))
        depth = 0
        set_pruning(table, 0, 0)
        done = 1
        
        while done != N_SLICE1 * N_TWIST:
            for i in range(N_SLICE1 * N_TWIST):
                twist = i // N_SLICE1
                slice_ = i % N_SLICE1
                if get_pruning(table, i) == depth:
                    for j in range(18):
                        new_slice = self.FRtoBR_move[slice_ * 24][j] // 24
                        new_twist = self.twist_move[twist][j]
                        if get_pruning(table, N_SLICE1 * new_twist + new_slice) == 0x0f:
                            set_pruning(table, N_SLICE1 * new_twist + new_slice, (depth + 1) & 0xff)
                            done += 1
            depth += 1
        return table
    
    def _generate_slice_URFtoDLF_parity_prun(self):
        """Génère la table de pruning pour phase 2 (coins)"""
        table = bytearray([0xff] * (N_SLICE2 * N_URFtoDLF * N_PARITY // 2 + 1))
        depth = 0
        set_pruning(table, 0, 0)
        done = 1
        
        while done != N_SLICE2 * N_URFtoDLF * N_PARITY:
            for i in range(N_SLICE2 * N_URFtoDLF * N_PARITY):
                parity = i % 2
                URFtoDLF = (i // 2) // N_SLICE2
                slice_ = (i // 2) % N_SLICE2
                if get_pruning(table, i) == depth:
                    for j in range(18):
                        if j in [3, 5, 6, 8, 12, 14, 15, 17]:  # Mouvements phase 2
                            new_slice = self.FRtoBR_move[slice_][j]
                            new_URFtoDLF = self.URFtoDLF_move[URFtoDLF][j]
                            new_parity = self.parity_move[parity][j]
                            idx = (N_SLICE2 * new_URFtoDLF + new_slice) * 2 + new_parity
                            if get_pruning(table, idx) == 0x0f:
                                set_pruning(table, idx, (depth + 1) & 0xff)
                                done += 1
            depth += 1
        return table
    
    def _generate_slice_URtoDF_parity_prun(self):
        """Génère la table de pruning pour phase 2 (arêtes)"""
        table = bytearray([0xff] * (N_SLICE2 * N_URtoDF * N_PARITY // 2 + 1))
        depth = 0
        set_pruning(table, 0, 0)
        done = 1
        
        while done != N_SLICE2 * N_URtoDF * N_PARITY:
            for i in range(N_SLICE2 * N_URtoDF * N_PARITY):
                parity = i % 2
                URtoDF = (i // 2) // N_SLICE2
                slice_ = (i // 2) % N_SLICE2
                if get_pruning(table, i) == depth:
                    for j in range(18):
                        if j in [3, 5, 6, 8, 12, 14, 15, 17]:  # Mouvements phase 2
                            new_slice = self.FRtoBR_move[slice_][j]
                            new_URtoDF = self.URtoDF_move[URtoDF][j]
                            new_parity = self.parity_move[parity][j]
                            idx = (N_SLICE2 * new_URtoDF + new_slice) * 2 + new_parity
                            if get_pruning(table, idx) == 0x0f:
                                set_pruning(table, idx, (depth + 1) & 0xff)
                                done += 1
            depth += 1
        return table


# =============================================================================
# RECHERCHE KOCIEMBA
# =============================================================================

class Search:
    """Algorithme de recherche Two-Phase"""
    
    AX_TO_S = ["U", "R", "F", "D", "L", "B"]
    PO_TO_S = [None, " ", "2 ", "' "]
    
    def __init__(self, tables):
        self.tables = tables
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
    
    def solution_to_string(self, length, depth_phase1=None):
        """Convertit la solution en string"""
        s = ""
        for i in range(length):
            s += self.AX_TO_S[self.ax[i]]
            s += self.PO_TO_S[self.po[i]]
            if depth_phase1 is not None and i == depth_phase1 - 1:
                s += ". "
        return s.strip()
    
    def solve(self, facelets, max_depth=21, timeout=10.0, use_separator=False):
        """Résout le cube"""
        import time
        
        # Vérifier l'entrée
        count = [0] * 6
        try:
            for i in range(54):
                count[COLORS[facelets[i]]] += 1
        except:
            return "Error 1"
        
        for i in range(6):
            if count[i] != 9:
                return "Error 1"
        
        fc = FaceCube(facelets)
        cc = fc.to_cubie_cube()
        s = cc.verify()
        if s != 0:
            return f"Error {abs(s)}"
        
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
        
        self.minDistPhase1[1] = 1
        n = 0
        busy = False
        depth_phase1 = 1
        
        t_start = time.time()
        
        # Boucle principale
        while True:
            while True:
                if depth_phase1 - n > self.minDistPhase1[n + 1] and not busy:
                    if self.ax[n] == 0 or self.ax[n] == 3:
                        n += 1
                        self.ax[n] = 1
                    else:
                        n += 1
                        self.ax[n] = 0
                    self.po[n] = 1
                else:
                    self.po[n] += 1
                    if self.po[n] > 3:
                        while True:
                            self.ax[n] += 1
                            if self.ax[n] > 5:
                                if time.time() - t_start > timeout:
                                    return "Error 8"
                                if n == 0:
                                    if depth_phase1 >= max_depth:
                                        return "Error 7"
                                    else:
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
                            if not (n != 0 and (self.ax[n - 1] == self.ax[n] or 
                                               self.ax[n - 1] - 3 == self.ax[n])):
                                break
                    else:
                        busy = False
                if not busy:
                    break
            
            # Calculer nouvelles coordonnées
            mv = 3 * self.ax[n] + self.po[n] - 1
            self.flip[n + 1] = self.tables.flip_move[self.flip[n]][mv]
            self.twist[n + 1] = self.tables.twist_move[self.twist[n]][mv]
            self.slice_[n + 1] = self.tables.FRtoBR_move[self.slice_[n] * 24][mv] // 24
            
            self.minDistPhase1[n + 1] = max(
                get_pruning(self.tables.slice_flip_prun, 
                           N_SLICE1 * self.flip[n + 1] + self.slice_[n + 1]),
                get_pruning(self.tables.slice_twist_prun,
                           N_SLICE1 * self.twist[n + 1] + self.slice_[n + 1])
            )
            
            if self.minDistPhase1[n + 1] == 0 and n >= depth_phase1 - 5:
                self.minDistPhase1[n + 1] = 10
                if n == depth_phase1 - 1:
                    s = self._total_depth(depth_phase1, max_depth)
                    if s >= 0:
                        if (s == depth_phase1 or 
                            (self.ax[depth_phase1 - 1] != self.ax[depth_phase1] and
                             self.ax[depth_phase1 - 1] != self.ax[depth_phase1] + 3)):
                            if use_separator:
                                return self.solution_to_string(s, depth_phase1)
                            return self.solution_to_string(s)
    
    def _total_depth(self, depth_phase1, max_depth):
        """Phase 2 de l'algorithme"""
        max_depth_phase2 = min(10, max_depth - depth_phase1)
        
        # Calculer les coordonnées à la fin de phase 1
        for i in range(depth_phase1):
            mv = 3 * self.ax[i] + self.po[i] - 1
            self.URFtoDLF[i + 1] = self.tables.URFtoDLF_move[self.URFtoDLF[i]][mv]
            self.FRtoBR[i + 1] = self.tables.FRtoBR_move[self.FRtoBR[i]][mv]
            self.parity[i + 1] = self.tables.parity_move[self.parity[i]][mv]
        
        # Vérifier si phase 2 est possible avec d1
        d1 = get_pruning(
            self.tables.slice_URFtoDLF_parity_prun,
            (N_SLICE2 * self.URFtoDLF[depth_phase1] + self.FRtoBR[depth_phase1]) * 2 + self.parity[depth_phase1]
        )
        if d1 > max_depth_phase2:
            return -1
        
        # Calculer URtoUL et UBtoDF
        for i in range(depth_phase1):
            mv = 3 * self.ax[i] + self.po[i] - 1
            self.URtoUL[i + 1] = self.tables.URtoUL_move[self.URtoUL[i]][mv]
            self.UBtoDF[i + 1] = self.tables.UBtoDF_move[self.UBtoDF[i]][mv]
        
        # Fusionner URtoUL et UBtoDF en URtoDF
        self.URtoDF[depth_phase1] = self.tables.merge_URtoUL_and_UBtoDF[self.URtoUL[depth_phase1]][self.UBtoDF[depth_phase1]]
        
        # Vérifier si phase 2 est possible avec d2
        d2 = get_pruning(
            self.tables.slice_URtoDF_parity_prun,
            (N_SLICE2 * self.URtoDF[depth_phase1] + self.FRtoBR[depth_phase1]) * 2 + self.parity[depth_phase1]
        )
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
        
        # Boucle recherche phase 2
        
        while True:
            while True:
                if depth_phase1 + depth_phase2 - n > self.minDistPhase2[n + 1] and not busy:
                    if self.ax[n] == 0 or self.ax[n] == 3:
                        n += 1
                        self.ax[n] = 1
                        self.po[n] = 2
                    else:
                        n += 1
                        self.ax[n] = 0
                        self.po[n] = 1
                else:
                    if self.ax[n] == 0 or self.ax[n] == 3:
                        self.po[n] += 1
                        need_increment = (self.po[n] > 3)
                    else:
                        self.po[n] += 2
                        need_increment = (self.po[n] > 3)
                    
                    if need_increment:
                        while True:
                            self.ax[n] += 1
                            if self.ax[n] > 5:
                                if n == depth_phase1:
                                    if depth_phase2 >= max_depth_phase2:
                                        return -1
                                    else:
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
                                if self.ax[n] == 0 or self.ax[n] == 3:
                                    self.po[n] = 1
                                else:
                                    self.po[n] = 2
                                busy = False
                            if not (n != depth_phase1 and (self.ax[n - 1] == self.ax[n] or
                                                           self.ax[n - 1] - 3 == self.ax[n])):
                                break
                    else:
                        busy = False
                if not busy:
                    break
            
            # Calculer nouvelles coordonnées phase 2
            mv = 3 * self.ax[n] + self.po[n] - 1
            self.URFtoDLF[n + 1] = self.tables.URFtoDLF_move[self.URFtoDLF[n]][mv]
            self.FRtoBR[n + 1] = self.tables.FRtoBR_move[self.FRtoBR[n]][mv]
            self.parity[n + 1] = self.tables.parity_move[self.parity[n]][mv]
            self.URtoDF[n + 1] = self.tables.URtoDF_move[self.URtoDF[n]][mv]
            
            idx = (N_SLICE2 * self.URFtoDLF[n + 1] + self.FRtoBR[n + 1]) * 2 + self.parity[n + 1]
            self.minDistPhase2[n + 1] = max(
                get_pruning(self.tables.slice_URFtoDLF_parity_prun, idx),
                get_pruning(self.tables.slice_URtoDF_parity_prun,
                           (N_SLICE2 * self.URtoDF[n + 1] + self.FRtoBR[n + 1]) * 2 + self.parity[n + 1])
            )
            
            if self.minDistPhase2[n + 1] == 0:
                return depth_phase1 + depth_phase2


# =============================================================================
# INTERFACE PRINCIPALE
# =============================================================================

# Tables globales (chargées une seule fois)
_tables = None


def get_tables():
    """Retourne les tables de pruning (lazy loading)"""
    global _tables
    if _tables is None:
        _tables = PruneTables()
    return _tables


def solve(cube_string, max_depth=21, timeout=10.0):
    """
    Résout un Rubik's Cube.
    
    Args:
        cube_string: String de 54 caractères représentant le cube
                    Format: UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB
        max_depth: Profondeur maximale de recherche
        timeout: Temps maximum en secondes
    
    Returns:
        Solution sous forme de string (ex: "U R2 F' D")
        ou message d'erreur
    """
    tables = get_tables()
    search = Search(tables)
    return search.solve(cube_string, max_depth, timeout, use_separator=False)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    import time
    
    print("=== Test Kociemba Pure Python ===\n")
    
    # Test 1: Cube résolu
    print("Test 1: Cube résolu")
    result = solve("UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB")
    print(f"  Résultat: '{result}' (attendu: '' ou solution triviale)\n")
    
    # Test 2: Simple scramble R
    print("Test 2: Après mouvement R")
    # Cube après R appliqué
    cube = "UUFUUFUUFRRRRRRRRRFFDFFDFFDDDBDDBDDBLLLLLLLLLUBBUBBUBB"
    start = time.time()
    result = solve(cube)
    elapsed = time.time() - start
    print(f"  Solution: {result}")
    print(f"  Temps: {elapsed:.3f}s\n")
    
    # Test 3: Scramble plus complexe
    print("Test 3: Scramble R U R' U'")
    # Après R U R' U' sur cube résolu
    cube = "UULUUFUUFRRBRRURRUFFDFFDFFDDDDDDDDDBLLLLLLLLLUBBBBRBBF"
    start = time.time()
    result = solve(cube, timeout=30.0)
    elapsed = time.time() - start
    print(f"  Solution: {result}")
    print(f"  Coups: {len(result.split()) if result and not result.startswith('Error') else 0}")
    print(f"  Temps: {elapsed:.3f}s\n")
    
    # Test 4: Scramble random
    print("Test 4: Scramble aléatoire")
    # Un vrai scramble
    cube = "DRLUUBFBRBLURRLBFFUFRFBDUDDRFDDLLDRLDUBFLUBLRFBBDUULF"
    start = time.time()
    result = solve(cube, timeout=30.0)
    elapsed = time.time() - start
    print(f"  Solution: {result}")
    print(f"  Coups: {len(result.split()) if result and not result.startswith('Error') else 0}")
    print(f"  Temps: {elapsed:.3f}s")
