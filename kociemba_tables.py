"""
Tables de pruning et de mouvements pour l'algorithme Kociemba.
Module partagé entre solver_kociemba.py et solver_kociemba_fast.py.
"""

import os
import time
import pickle


def get_pruning(table, index):
    if (index & 1) == 0:
        return table[index >> 1] & 0x0f
    return (table[index >> 1] >> 4) & 0x0f


def set_pruning(table, index, value):
    idx = index >> 1
    if (index & 1) == 0:
        table[idx] = (table[idx] & 0xf0) | (value & 0x0f)
    else:
        table[idx] = (table[idx] & 0x0f) | ((value & 0x0f) << 4)


class KociembaTablesConfig:
    def __init__(
        self,
        *,
        N_MOVE,
        N_TWIST,
        N_FLIP,
        N_FRtoBR,
        N_URFtoDLF,
        N_URtoUL,
        N_UBtoDF,
        N_URtoDF,
        N_SLICE1,
        N_SLICE2,
        N_PARITY,
        BR,
    ):
        self.N_MOVE = N_MOVE
        self.N_TWIST = N_TWIST
        self.N_FLIP = N_FLIP
        self.N_FRtoBR = N_FRtoBR
        self.N_URFtoDLF = N_URFtoDLF
        self.N_URtoUL = N_URtoUL
        self.N_UBtoDF = N_UBtoDF
        self.N_URtoDF = N_URtoDF
        self.N_SLICE1 = N_SLICE1
        self.N_SLICE2 = N_SLICE2
        self.N_PARITY = N_PARITY
        self.BR = BR


class Tables:
    def __init__(
        self,
        cube_class,
        move_cube,
        parity_move,
        config: KociembaTablesConfig,
        cache_file=None,
        cache_version="1.0",
        generate_if_missing=True,
        verbose=True,
    ):
        self._cube_class = cube_class
        self._move_cube = move_cube
        self._parity_move = parity_move
        self._cfg = config
        self.CACHE_VERSION = cache_version
        self._verbose = verbose

        if cache_file is None:
            cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kociemba_tables.pkl")
        self.CACHE_FILE = cache_file

        self.twist_move = None
        self.flip_move = None
        self.FRtoBR_move = None
        self.URFtoDLF_move = None
        self.URtoUL_move = None
        self.UBtoDF_move = None
        self.URtoDF_move = None
        self.merge_URtoUL_UBtoDF = None
        self.slice_flip_prun = None
        self.slice_twist_prun = None
        self.slice_URFtoDLF_parity_prun = None
        self.slice_URtoDF_parity_prun = None

        if not self._load_from_cache():
            if not generate_if_missing:
                raise RuntimeError("Tables non trouvées.")
            self._generate_all()
            self._save_to_cache()

    def _log(self, msg):
        if self._verbose:
            print(msg)

    def _load_from_cache(self) -> bool:
        if not os.path.exists(self.CACHE_FILE):
            return False
        try:
            self._log(f"Chargement des tables depuis {os.path.basename(self.CACHE_FILE)}...")
            t_start = time.time()

            with open(self.CACHE_FILE, 'rb') as f:
                data = pickle.load(f)

            if data.get('version') != self.CACHE_VERSION:
                self._log("  Version du cache obsolète, régénération nécessaire...")
                return False

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
            self._log(f"Tables chargées en {elapsed:.2f} secondes")
            return True
        except Exception as e:
            self._log(f"  Erreur lors du chargement du cache: {e}")
            self._log("  Régénération des tables...")
            return False

    def _save_to_cache(self):
        try:
            self._log(f"Sauvegarde des tables dans {os.path.basename(self.CACHE_FILE)}...")

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

            size_mb = os.path.getsize(self.CACHE_FILE) / (1024 * 1024)
            self._log(f"Tables sauvegardées ({size_mb:.1f} MB)")
        except Exception as e:
            self._log(f"  Avertissement: impossible de sauvegarder le cache: {e}")

    def _generate_all(self):
        self._log("Génération des tables de mouvement et pruning...")
        self._log("(Première exécution uniquement, ~2-5 minutes)")
        t_start = time.time()

        self._log("  [1/12] twist_move...")
        self.twist_move = self._gen_twist_move()

        self._log("  [2/12] flip_move...")
        self.flip_move = self._gen_flip_move()

        self._log("  [3/12] FRtoBR_move...")
        self.FRtoBR_move = self._gen_FRtoBR_move()

        self._log("  [4/12] URFtoDLF_move...")
        self.URFtoDLF_move = self._gen_URFtoDLF_move()

        self._log("  [5/12] URtoUL_move...")
        self.URtoUL_move = self._gen_URtoUL_move()

        self._log("  [6/12] UBtoDF_move...")
        self.UBtoDF_move = self._gen_UBtoDF_move()

        self._log("  [7/12] URtoDF_move...")
        self.URtoDF_move = self._gen_URtoDF_move()

        self._log("  [8/12] merge_URtoUL_UBtoDF...")
        self.merge_URtoUL_UBtoDF = self._gen_merge_table()

        self._log("  [9/12] slice_flip_prun...")
        self.slice_flip_prun = self._gen_slice_flip_prun()

        self._log("  [10/12] slice_twist_prun...")
        self.slice_twist_prun = self._gen_slice_twist_prun()

        self._log("  [11/12] slice_URFtoDLF_parity_prun...")
        self.slice_URFtoDLF_parity_prun = self._gen_slice_URFtoDLF_parity_prun()

        self._log("  [12/12] slice_URtoDF_parity_prun...")
        self.slice_URtoDF_parity_prun = self._gen_slice_URtoDF_parity_prun()

        elapsed = time.time() - t_start
        self._log(f"Tables générées en {elapsed:.1f} secondes")

    def _gen_twist_move(self):
        cfg = self._cfg
        table = [[0] * cfg.N_MOVE for _ in range(cfg.N_TWIST)]
        a = self._cube_class()
        for i in range(cfg.N_TWIST):
            a.set_twist(i)
            for j in range(6):
                for k in range(3):
                    a.corner_multiply(self._move_cube[j])
                    table[i][3 * j + k] = a.get_twist()
                a.corner_multiply(self._move_cube[j])
        return table

    def _gen_flip_move(self):
        cfg = self._cfg
        table = [[0] * cfg.N_MOVE for _ in range(cfg.N_FLIP)]
        a = self._cube_class()
        for i in range(cfg.N_FLIP):
            a.set_flip(i)
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(self._move_cube[j])
                    table[i][3 * j + k] = a.get_flip()
                a.edge_multiply(self._move_cube[j])
        return table

    def _gen_FRtoBR_move(self):
        cfg = self._cfg
        table = [[0] * cfg.N_MOVE for _ in range(cfg.N_FRtoBR)]
        a = self._cube_class()
        for i in range(cfg.N_FRtoBR):
            a.set_FRtoBR(i)
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(self._move_cube[j])
                    table[i][3 * j + k] = a.get_FRtoBR()
                a.edge_multiply(self._move_cube[j])
        return table

    def _gen_URFtoDLF_move(self):
        cfg = self._cfg
        table = [[0] * cfg.N_MOVE for _ in range(cfg.N_URFtoDLF)]
        a = self._cube_class()
        for i in range(cfg.N_URFtoDLF):
            a.set_URFtoDLF(i)
            for j in range(6):
                for k in range(3):
                    a.corner_multiply(self._move_cube[j])
                    table[i][3 * j + k] = a.get_URFtoDLF()
                a.corner_multiply(self._move_cube[j])
        return table

    def _gen_URtoUL_move(self):
        cfg = self._cfg
        table = [[0] * cfg.N_MOVE for _ in range(cfg.N_URtoUL)]
        a = self._cube_class()
        for i in range(cfg.N_URtoUL):
            a.set_URtoUL(i)
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(self._move_cube[j])
                    table[i][3 * j + k] = a.get_URtoUL()
                a.edge_multiply(self._move_cube[j])
        return table

    def _gen_UBtoDF_move(self):
        cfg = self._cfg
        table = [[0] * cfg.N_MOVE for _ in range(cfg.N_UBtoDF)]
        a = self._cube_class()
        for i in range(cfg.N_UBtoDF):
            a.set_UBtoDF(i)
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(self._move_cube[j])
                    table[i][3 * j + k] = a.get_UBtoDF()
                a.edge_multiply(self._move_cube[j])
        return table

    def _gen_URtoDF_move(self):
        cfg = self._cfg
        table = [[0] * cfg.N_MOVE for _ in range(cfg.N_URtoDF)]
        a = self._cube_class()
        for i in range(cfg.N_URtoDF):
            a.set_URtoDF(i)
            for j in range(6):
                for k in range(3):
                    a.edge_multiply(self._move_cube[j])
                    table[i][3 * j + k] = a.get_URtoDF()
                a.edge_multiply(self._move_cube[j])
        return table

    def _gen_merge_table(self):
        cfg = self._cfg
        table = [[0] * 336 for _ in range(336)]
        for uRtoUL in range(336):
            for uBtoDF in range(336):
                a = self._cube_class()
                b = self._cube_class()
                a.set_URtoUL(uRtoUL)
                b.set_UBtoDF(uBtoDF)

                for i in range(8):
                    if a.ep[i] != cfg.BR:
                        if b.ep[i] != cfg.BR:
                            table[uRtoUL][uBtoDF] = -1
                            break
                        b.ep[i] = a.ep[i]
                else:
                    table[uRtoUL][uBtoDF] = b.get_URtoDF()
        return table

    def _gen_slice_flip_prun(self):
        cfg = self._cfg
        size = cfg.N_SLICE1 * cfg.N_FLIP
        table = bytearray([0xff] * ((size >> 1) + 1))
        set_pruning(table, 0, 0)

        current = [0]
        depth = 0

        while current:
            next_level = []
            for idx in current:
                flip_idx = idx // cfg.N_SLICE1
                slice_idx = idx % cfg.N_SLICE1
                for mv in range(18):
                    new_slice = self.FRtoBR_move[slice_idx * 24][mv] // 24
                    new_flip = self.flip_move[flip_idx][mv]
                    new_idx = cfg.N_SLICE1 * new_flip + new_slice
                    if get_pruning(table, new_idx) == 0x0f:
                        set_pruning(table, new_idx, depth + 1)
                        next_level.append(new_idx)
            current = next_level
            depth += 1
        return table

    def _gen_slice_twist_prun(self):
        cfg = self._cfg
        size = cfg.N_SLICE1 * cfg.N_TWIST
        table = bytearray([0xff] * ((size >> 1) + 1))
        set_pruning(table, 0, 0)

        current = [0]
        depth = 0

        while current:
            next_level = []
            for idx in current:
                twist_idx = idx // cfg.N_SLICE1
                slice_idx = idx % cfg.N_SLICE1
                for mv in range(18):
                    new_slice = self.FRtoBR_move[slice_idx * 24][mv] // 24
                    new_twist = self.twist_move[twist_idx][mv]
                    new_idx = cfg.N_SLICE1 * new_twist + new_slice
                    if get_pruning(table, new_idx) == 0x0f:
                        set_pruning(table, new_idx, depth + 1)
                        next_level.append(new_idx)
            current = next_level
            depth += 1
        return table

    def _gen_slice_URFtoDLF_parity_prun(self):
        cfg = self._cfg
        size = cfg.N_SLICE2 * cfg.N_URFtoDLF * cfg.N_PARITY
        table = bytearray([0xff] * ((size >> 1) + 1))
        set_pruning(table, 0, 0)

        phase2_moves = (0, 1, 2, 4, 7, 9, 10, 11, 13, 16)

        current = [0]
        depth = 0

        while current:
            next_level = []
            for idx in current:
                parity = idx % 2
                URFtoDLF = (idx >> 1) // cfg.N_SLICE2
                slice_idx = (idx >> 1) % cfg.N_SLICE2

                for mv in phase2_moves:
                    new_slice = self.FRtoBR_move[slice_idx][mv] % 24
                    new_URFtoDLF = self.URFtoDLF_move[URFtoDLF][mv]
                    new_parity = self._parity_move[parity][mv]
                    new_idx = (cfg.N_SLICE2 * new_URFtoDLF + new_slice) * 2 + new_parity
                    if new_idx < size and get_pruning(table, new_idx) == 0x0f:
                        set_pruning(table, new_idx, depth + 1)
                        next_level.append(new_idx)

            current = next_level
            depth += 1
        return table

    def _gen_slice_URtoDF_parity_prun(self):
        cfg = self._cfg
        size = cfg.N_SLICE2 * cfg.N_URtoDF * cfg.N_PARITY
        table = bytearray([0xff] * ((size >> 1) + 1))
        set_pruning(table, 0, 0)

        phase2_moves = (0, 1, 2, 4, 7, 9, 10, 11, 13, 16)

        current = [0]
        depth = 0

        while current:
            next_level = []
            for idx in current:
                parity = idx % 2
                URtoDF = (idx >> 1) // cfg.N_SLICE2
                slice_idx = (idx >> 1) % cfg.N_SLICE2

                for mv in phase2_moves:
                    new_slice = self.FRtoBR_move[slice_idx][mv] % 24
                    new_URtoDF = self.URtoDF_move[URtoDF][mv]
                    new_parity = self._parity_move[parity][mv]
                    new_idx = (cfg.N_SLICE2 * new_URtoDF + new_slice) * 2 + new_parity
                    if new_idx < size and get_pruning(table, new_idx) == 0x0f:
                        set_pruning(table, new_idx, depth + 1)
                        next_level.append(new_idx)

            current = next_level
            depth += 1
        return table
