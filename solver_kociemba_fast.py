"""
Solver Kociemba FAST - First Solution Found
============================================

Version rapide du solver Kociemba qui retourne la PREMIÈRE solution trouvée,
sans garantie d'optimalité. Utile quand la vitesse est plus importante
que la longueur minimale de la solution.

Différence avec solver_kociemba.py:
- IDA* (optimal): profondeur 1 → 2 → 3... première solution = optimale
- DFS (fast): profondeur max directe, première solution trouvée retournée

UTILISATION:
    from solver_kociemba_fast import solve_fast
    
    solution = solve_fast("DRLUUBFBRBLURRLBFFUFRFBDUDDRFDDLLDRLDUBFLUBLRFBBDUULF")
    print(solution)  # Solution rapide mais potentiellement non-optimale
"""

import time

from kociemba_tables import Tables, KociembaTablesConfig, get_pruning

# =============================================================================
# CONSTANTES (identiques à solver_kociemba.py)
# =============================================================================

U, R, F, D, L, B = 0, 1, 2, 3, 4, 5
COLORS = {'U': U, 'R': R, 'F': F, 'D': D, 'L': L, 'B': B}
COLOR_NAMES = ['U', 'R', 'F', 'D', 'L', 'B']

URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB = range(8)
UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR = range(12)

U1, U2, U3, U4, U5, U6, U7, U8, U9 = range(9)
R1, R2, R3, R4, R5, R6, R7, R8, R9 = range(9, 18)
F1, F2, F3, F4, F5, F6, F7, F8, F9 = range(18, 27)
D1, D2, D3, D4, D5, D6, D7, D8, D9 = range(27, 36)
L1, L2, L3, L4, L5, L6, L7, L8, L9 = range(36, 45)
B1, B2, B3, B4, B5, B6, B7, B8, B9 = range(45, 54)

CORNER_FACELET = (
    (U9, R1, F3), (U7, F1, L3), (U1, L1, B3), (U3, B1, R3),
    (D3, F9, R7), (D1, L9, F7), (D7, B9, L7), (D9, R9, B7),
)

EDGE_FACELET = (
    (U6, R2), (U8, F2), (U4, L2), (U2, B2), (D6, R8), (D2, F8),
    (D4, L8), (D8, B8), (F6, R4), (F4, L6), (B6, L4), (B4, R6),
)

CORNER_COLOR = (
    (U, R, F), (U, F, L), (U, L, B), (U, B, R),
    (D, F, R), (D, L, F), (D, B, L), (D, R, B),
)

EDGE_COLOR = (
    (U, R), (U, F), (U, L), (U, B), (D, R), (D, F),
    (D, L), (D, B), (F, R), (F, L), (B, L), (B, R),
)

N_TWIST = 2187
N_FLIP = 2048
N_SLICE1 = 495
N_SLICE2 = 24
N_PARITY = 2
N_URFtoDLF = 20160
N_FRtoBR = 11880
N_URtoUL = 1320
N_UBtoDF = 1320
N_URtoDF = 20160
N_MOVE = 18

PARITY_MOVE = (
    (1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1),
    (0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0),
)

KOCIEMBA_TABLES_CONFIG = KociembaTablesConfig(
    N_MOVE=N_MOVE,
    N_TWIST=N_TWIST,
    N_FLIP=N_FLIP,
    N_FRtoBR=N_FRtoBR,
    N_URFtoDLF=N_URFtoDLF,
    N_URtoUL=N_URtoUL,
    N_UBtoDF=N_UBtoDF,
    N_URtoDF=N_URtoDF,
    N_SLICE1=N_SLICE1,
    N_SLICE2=N_SLICE2,
    N_PARITY=N_PARITY,
    BR=BR,
)

# =============================================================================
# UTILITAIRES
# =============================================================================

def Cnk(n, k):
    if n < k:
        return 0
    if k > n // 2:
        k = n - k
    s = 1
    for i in range(k):
        s = s * (n - i) // (i + 1)
    return s

def rotate_left(arr, l, r):
    temp = arr[l]
    for i in range(l, r):
        arr[i] = arr[i + 1]
    arr[r] = temp

def rotate_right(arr, l, r):
    temp = arr[r]
    for i in range(r, l, -1):
        arr[i] = arr[i - 1]
    arr[l] = temp

# =============================================================================
# CUBIE CUBE
# =============================================================================

class CubieCube:
    __slots__ = ('cp', 'co', 'ep', 'eo')
    
    def __init__(self, cp=None, co=None, ep=None, eo=None):
        self.cp = list(cp) if cp else [URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB]
        self.co = list(co) if co else [0, 0, 0, 0, 0, 0, 0, 0]
        self.ep = list(ep) if ep else [UR, UF, UL, UB, DR, DF, DL, DB, FR, FL, BL, BR]
        self.eo = list(eo) if eo else [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    def corner_multiply(self, b):
        cp_new = [self.cp[b.cp[i]] for i in range(8)]
        co_new = [(self.co[b.cp[i]] + b.co[i]) % 3 for i in range(8)]
        self.cp = cp_new
        self.co = co_new
    
    def edge_multiply(self, b):
        ep_new = [self.ep[b.ep[i]] for i in range(12)]
        eo_new = [(self.eo[b.ep[i]] + b.eo[i]) % 2 for i in range(12)]
        self.ep = ep_new
        self.eo = eo_new
    
    def multiply(self, b):
        self.corner_multiply(b)
        self.edge_multiply(b)
    
    def get_twist(self):
        ret = 0
        for i in range(7):
            ret = 3 * ret + self.co[i]
        return ret
    
    def set_twist(self, twist):
        parity = 0
        for i in range(6, -1, -1):
            self.co[i] = twist % 3
            parity += self.co[i]
            twist //= 3
        self.co[7] = (3 - parity % 3) % 3
    
    def get_flip(self):
        ret = 0
        for i in range(11):
            ret = 2 * ret + self.eo[i]
        return ret
    
    def set_flip(self, flip):
        parity = 0
        for i in range(10, -1, -1):
            self.eo[i] = flip % 2
            parity += self.eo[i]
            flip //= 2
        self.eo[11] = (2 - parity % 2) % 2
    
    def get_FRtoBR(self):
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
    
    def corner_parity(self):
        s = 0
        for i in range(7, 0, -1):
            for j in range(i - 1, -1, -1):
                if self.cp[j] > self.cp[i]:
                    s += 1
        return s % 2
    
    def get_URFtoDLF(self):
        a, b, x = 0, 0, 0
        corner6 = [0] * 6
        for j in range(8):
            if self.cp[j] <= DLF:
                a += Cnk(j, x + 1)
                corner6[x] = self.cp[j]
                x += 1
        for j in range(5, 0, -1):
            k = 0
            while corner6[j] != j:
                rotate_left(corner6, 0, j)
                k += 1
            b = (j + 1) * b + k
        return 720 * a + b
    
    def set_URFtoDLF(self, idx):
        corner6 = [URF, UFL, ULB, UBR, DFR, DLF]
        other = [DBL, DRB]
        b = idx % 720
        a = idx // 720
        for i in range(8):
            self.cp[i] = DRB
        for j in range(1, 6):
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
        a, b, x = 0, 0, 0
        edge3 = [0, 0, 0]
        for j in range(12):
            if self.ep[j] <= UL:
                a += Cnk(j, x + 1)
                edge3[x] = self.ep[j]
                x += 1
        for j in range(2, 0, -1):
            k = 0
            while edge3[j] != j:
                rotate_left(edge3, 0, j)
                k += 1
            b = (j + 1) * b + k
        return 6 * a + b
    
    def set_URtoUL(self, idx):
        edge3 = [UR, UF, UL]
        b = idx % 6
        a = idx // 6
        for i in range(12):
            self.ep[i] = BR
        for j in range(1, 3):
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
        a, b, x = 0, 0, 0
        edge3 = [0, 0, 0]
        for j in range(12):
            if UB <= self.ep[j] <= DF:
                a += Cnk(j, x + 1)
                edge3[x] = self.ep[j]
                x += 1
        for j in range(2, 0, -1):
            k = 0
            while edge3[j] != j + UB:
                rotate_left(edge3, 0, j)
                k += 1
            b = (j + 1) * b + k
        return 6 * a + b
    
    def set_UBtoDF(self, idx):
        edge3 = [UB, DR, DF]
        b = idx % 6
        a = idx // 6
        for i in range(12):
            self.ep[i] = BR
        for j in range(1, 3):
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
        a, b, x = 0, 0, 0
        edge6 = [0] * 6
        for j in range(12):
            if self.ep[j] <= DF:
                a += Cnk(j, x + 1)
                edge6[x] = self.ep[j]
                x += 1
        for j in range(5, 0, -1):
            k = 0
            while edge6[j] != j:
                rotate_left(edge6, 0, j)
                k += 1
            b = (j + 1) * b + k
        return 720 * a + b
    
    def set_URtoDF(self, idx):
        edge6 = [UR, UF, UL, UB, DR, DF]
        other = [DL, DB, FR, FL, BL, BR]
        b = idx % 720
        a = idx // 720
        for i in range(12):
            self.ep[i] = BR
        for j in range(1, 6):
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
        f = [U] * 54
        f[4] = U
        f[13] = R
        f[22] = F
        f[31] = D
        f[40] = L
        f[49] = B
        for i in range(8):
            j = self.cp[i]
            ori = self.co[i]
            for n in range(3):
                f[CORNER_FACELET[i][(n + ori) % 3]] = CORNER_COLOR[j][n]
        for i in range(12):
            j = self.ep[i]
            ori = self.eo[i]
            for n in range(2):
                f[EDGE_FACELET[i][(n + ori) % 2]] = EDGE_COLOR[j][n]
        fc = FaceCube.__new__(FaceCube)
        fc.f = f
        return fc
    
    def verify(self):
        corner_count = [0] * 8
        for c in self.cp:
            if c < 0 or c > 7:
                return -2
            corner_count[c] += 1
        for count in corner_count:
            if count != 1:
                return -2
        edge_count = [0] * 12
        for e in self.ep:
            if e < 0 or e > 11:
                return -1
            edge_count[e] += 1
        for count in edge_count:
            if count != 1:
                return -1
        if sum(self.co) % 3 != 0:
            return -5
        if sum(self.eo) % 2 != 0:
            return -3
        edge_parity = 0
        for i in range(11, 0, -1):
            for j in range(i - 1, -1, -1):
                if self.ep[j] > self.ep[i]:
                    edge_parity += 1
        if edge_parity % 2 != self.corner_parity():
            return -6
        return 0


# =============================================================================
# MOUVEMENTS DE BASE
# =============================================================================

cpU = (UBR, URF, UFL, ULB, DFR, DLF, DBL, DRB)
coU = (0, 0, 0, 0, 0, 0, 0, 0)
epU = (UB, UR, UF, UL, DR, DF, DL, DB, FR, FL, BL, BR)
eoU = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

cpR = (DFR, UFL, ULB, URF, DRB, DLF, DBL, UBR)
coR = (2, 0, 0, 1, 1, 0, 0, 2)
epR = (FR, UF, UL, UB, BR, DF, DL, DB, DR, FL, BL, UR)
eoR = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

cpF = (UFL, DLF, ULB, UBR, URF, DFR, DBL, DRB)
coF = (1, 2, 0, 0, 2, 1, 0, 0)
epF = (UR, FL, UL, UB, DR, FR, DL, DB, UF, DF, BL, BR)
eoF = (0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0)

cpD = (URF, UFL, ULB, UBR, DLF, DBL, DRB, DFR)
coD = (0, 0, 0, 0, 0, 0, 0, 0)
epD = (UR, UF, UL, UB, DF, DL, DB, DR, FR, FL, BL, BR)
eoD = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

cpL = (URF, ULB, DBL, UBR, DFR, UFL, DLF, DRB)
coL = (0, 1, 2, 0, 0, 2, 1, 0)
epL = (UR, UF, BL, UB, DR, DF, FL, DB, FR, UL, DL, BR)
eoL = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

cpB = (URF, UFL, UBR, DRB, DFR, DLF, ULB, DBL)
coB = (0, 0, 1, 2, 0, 0, 2, 1)
epB = (UR, UF, UL, BR, DR, DF, DL, BL, FR, FL, UB, DB)
eoB = (0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1)

MOVE_CUBE = (
    CubieCube(cpU, coU, epU, eoU),
    CubieCube(cpR, coR, epR, eoR),
    CubieCube(cpF, coF, epF, eoF),
    CubieCube(cpD, coD, epD, eoD),
    CubieCube(cpL, coL, epL, eoL),
    CubieCube(cpB, coB, epB, eoB),
)


# =============================================================================
# FACE CUBE
# =============================================================================

class FaceCube:
    __slots__ = ('f',)
    
    def __init__(self, cube_string="UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"):
        self.f = [COLORS.get(c, U) for c in cube_string]
    
    def to_string(self):
        color_names = ['U', 'R', 'F', 'D', 'L', 'B']
        return ''.join(color_names[c] for c in self.f)
    
    def to_cubie_cube(self):
        cc = CubieCube()
        for i in range(8):
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
# ALGORITHME FAST - DFS avec profondeur max directe
# =============================================================================

class SearchFast:
    """
    Algorithme Two-Phase FAST - retourne la première solution trouvée.
    
    Différence clé avec Search (optimal):
    - Commence directement à la profondeur maximale
    - Retourne dès qu'une solution est trouvée (pas d'IDA*)
    """
    
    AXIS_NAMES = ('U', 'R', 'F', 'D', 'L', 'B')
    POWER_NAMES = (None, ' ', '2 ', "' ")
    
    def __init__(self, tables):
        self.tables = tables
        self.ax = [0] * 51
        self.po = [0] * 51
        self.flip = [0] * 51
        self.twist = [0] * 51
        self.slice_ = [0] * 51
        self.parity = [0] * 51
        self.URFtoDLF = [0] * 51
        self.FRtoBR = [0] * 51
        self.URtoUL = [0] * 51
        self.UBtoDF = [0] * 51
        self.URtoDF = [0] * 51
        self.minDistPhase1 = [0] * 51
        self.minDistPhase2 = [0] * 51
    
    def _solution_string(self, length):
        parts = []
        for i in range(length):
            if self.POWER_NAMES[self.po[i]] is not None:
                parts.append(self.AXIS_NAMES[self.ax[i]] + self.POWER_NAMES[self.po[i]])
            else:
                parts.append(self.AXIS_NAMES[self.ax[i]])
        return ''.join(parts).strip()
    
    def solve(self, cube_string, max_depth=50, timeout=10.0, timeout_per_depth=0.3):
        """
        Résout le cube en mode FAST (première solution trouvée).
        
        Args:
            cube_string: String 54 caractères (URFDLB)
            max_depth: Profondeur maximale (défaut: 50)
            timeout: Temps limite global en secondes
            timeout_per_depth: Temps limite par profondeur en secondes (défaut: 0.3s)
        
        Returns:
            String de la solution ou message d'erreur
        """
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
        
        fc = FaceCube(cube_string)
        cc = fc.to_cubie_cube()
        
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
        
        if (self.flip[0] == 0 and self.twist[0] == 0 and 
            self.slice_[0] == 0 and self.FRtoBR[0] == 0 and
            self.URFtoDLF[0] == 0 and self.parity[0] == 0):
            return ""
        
        self.minDistPhase1[1] = 1
        n = 0
        busy = False
                
        # Calculer l'estimation minimale initiale
        init_estimate = max(
            get_pruning(self.tables.slice_flip_prun,
                       N_SLICE1 * self.flip[0] + self.slice_[0]),
            get_pruning(self.tables.slice_twist_prun,
                       N_SLICE1 * self.twist[0] + self.slice_[0])
        )
        
        depth_phase1 = init_estimate
        
        t_start = time.time()
        
        while True:
            t_depth_start = time.time()
            depth_timeout_reached = False
            
            while True:
                if depth_phase1 - n > self.minDistPhase1[n + 1] and not busy:
                    if self.ax[n] in (0, 3):
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
                                    return "Error: timeout"
                                
                                if n == 0:
                                    if time.time() - t_depth_start > timeout_per_depth:
                                        depth_timeout_reached = True
                                    depth_phase1 += 7
                                    if depth_phase1 > max_depth:
                                        return "Error: pas de solution dans la limite"
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
                            
                            if n == 0 or (self.ax[n - 1] != self.ax[n] and 
                                         self.ax[n - 1] - 3 != self.ax[n]):
                                break
                    else:
                        busy = False
                
                if not busy:
                    break

            if depth_timeout_reached:
                continue
            
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
            
            if self.minDistPhase1[n + 1] == 0:
                self.minDistPhase1[n + 1] = 10
                # Lancer phase 2
                s = self._phase2(n + 1, max_depth, t_start, timeout, timeout_per_depth)
                if s == -2:
                    return "Error: timeout"
                if s >= 0:
                    return self._solution_string(s)
    
    def _phase2(self, depth_phase1, max_depth, t_start, timeout, timeout_per_depth):
        """Phase 2: résolution finale dans G1"""
        max_depth_phase2 = min(25, max_depth - depth_phase1)
        
        for i in range(depth_phase1):
            mv = 3 * self.ax[i] + self.po[i] - 1
            self.URFtoDLF[i + 1] = self.tables.URFtoDLF_move[self.URFtoDLF[i]][mv]
            self.FRtoBR[i + 1] = self.tables.FRtoBR_move[self.FRtoBR[i]][mv]
            self.parity[i + 1] = PARITY_MOVE[self.parity[i]][mv]
        
        if self.FRtoBR[depth_phase1] >= N_SLICE2:
            return -1
        
        idx1 = (N_SLICE2 * self.URFtoDLF[depth_phase1] + self.FRtoBR[depth_phase1]) * 2 + self.parity[depth_phase1]
        d1 = get_pruning(self.tables.slice_URFtoDLF_parity_prun, idx1)
        if d1 > max_depth_phase2:
            return -1
        
        for i in range(depth_phase1):
            mv = 3 * self.ax[i] + self.po[i] - 1
            self.URtoUL[i + 1] = self.tables.URtoUL_move[self.URtoUL[i]][mv]
            self.UBtoDF[i + 1] = self.tables.UBtoDF_move[self.UBtoDF[i]][mv]
        
        rows_merge = len(self.tables.merge_URtoUL_UBtoDF)
        cols_merge = len(self.tables.merge_URtoUL_UBtoDF[0]) if rows_merge > 0 else 0
        if (self.URtoUL[depth_phase1] >= rows_merge or
            self.UBtoDF[depth_phase1] >= cols_merge):
            return -1
        self.URtoDF[depth_phase1] = self.tables.merge_URtoUL_UBtoDF[
            self.URtoUL[depth_phase1]][self.UBtoDF[depth_phase1]]
        
        idx2 = (N_SLICE2 * self.URtoDF[depth_phase1] + self.FRtoBR[depth_phase1]) * 2 + self.parity[depth_phase1]
        d2 = get_pruning(self.tables.slice_URtoDF_parity_prun, idx2)
        if d2 > max_depth_phase2:
            return -1
        
        self.minDistPhase2[depth_phase1] = max(d1, d2)
        if self.minDistPhase2[depth_phase1] == 0:
            return depth_phase1
        
        depth_phase2 = 1
        n = depth_phase1
        busy = False
        self.po[depth_phase1] = 0
        self.ax[depth_phase1] = 0
        self.minDistPhase2[n + 1] = 1
        
        # Timeout par profondeur en phase 2

        t_depth_start = time.time()
        depth_timeout_reached = False
        
        while True:
            while True:
                if depth_phase1 + depth_phase2 - n > self.minDistPhase2[n + 1] and not busy:
                    if self.ax[n] in (0, 3):
                        n += 1
                        self.ax[n] = 1
                        self.po[n] = 2
                    else:
                        n += 1
                        self.ax[n] = 0
                        self.po[n] = 1
                else:
                    if self.ax[n] in (0, 3):
                        self.po[n] += 1
                    else:
                        self.po[n] += 2
                    
                    if self.po[n] > 3:
                        while True:
                            self.ax[n] += 1
                            if self.ax[n] > 5:
                                if time.time() - t_start > timeout:
                                    return -2
                                
                                if n == depth_phase1:
                                    if time.time() - t_depth_start > timeout_per_depth:
                                        depth_timeout_reached = True
                                    
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
            
            if depth_timeout_reached:
                t_depth_start = time.time()
                depth_timeout_reached = False
                continue
            
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
    global _tables
    if _tables is None:
        _tables = Tables(
            CubieCube,
            MOVE_CUBE,
            PARITY_MOVE,
            KOCIEMBA_TABLES_CONFIG,
        )
    return _tables

def solve_fast(cube_string, max_depth=50, timeout=10.0, timeout_per_depth=0.3):
    """
    Résout un Rubik's Cube en mode FAST (première solution trouvée).
    
    Args:
        cube_string: String de 54 caractères (URFDLB)
        max_depth: Profondeur maximale (défaut: 50)
        timeout: Temps limite global en secondes (défaut: 10.0)
        timeout_per_depth: Temps limite par profondeur en secondes (défaut: 0.3s)
    
    Returns:
        str: La solution (potentiellement non-optimale)
             ou un message d'erreur commençant par "Error:"
    """
    tables = _get_tables()
    search = SearchFast(tables)
    return search.solve(cube_string, max_depth, timeout, timeout_per_depth)
