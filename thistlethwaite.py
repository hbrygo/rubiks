#!/usr/bin/env python3
"""
Algorithme de Thistlethwaite pour résoudre le Rubik's Cube.
Inspiré du projet fonctionnel.

Usage: python thistlethwaite.py "R U R' U'"
"""

import sys
import numpy as np
import multiprocessing as mp

# =============================================================================
# CLASSE CUBE (représentation matricielle)
# =============================================================================

class Cube:
    def __init__(self):
        self.reset()
        self.faces = {"F": self.FRONT, "R": self.RIGHT, "U": self.UP, 
                      "B": self.BACK, "L": self.LEFT, "D": self.DOWN}

    def reset(self):
        self.face_left = np.array([["L0", "L1", "L2"], ["L3", "L4", "L5"], ["L6", "L7", "L8"]])
        self.face_right = np.array([["R0", "R1", "R2"], ["R3", "R4", "R5"], ["R6", "R7", "R8"]])
        self.face_front = np.array([["F0", "F1", "F2"], ["F3", "F4", "F5"], ["F6", "F7", "F8"]])
        self.face_up = np.array([["U0", "U1", "U2"], ["U3", "U4", "U5"], ["U6", "U7", "U8"]])
        self.face_down = np.array([["D0", "D1", "D2"], ["D3", "D4", "D5"], ["D6", "D7", "D8"]])
        self.face_back = np.array([["B0", "B1", "B2"], ["B3", "B4", "B5"], ["B6", "B7", "B8"]])

    def sides(self):
        return {"F": self.face_front, "R": self.face_right, "U": self.face_up, 
                "B": self.face_back, "L": self.face_left, "D": self.face_down}

    def copy(self, cube):
        self.face_front = cube.face_front.copy()
        self.face_right = cube.face_right.copy()
        self.face_back = cube.face_back.copy()
        self.face_left = cube.face_left.copy()
        self.face_up = cube.face_up.copy()
        self.face_down = cube.face_down.copy()

    def primeInvert(self, faces):
        faces[1], faces[3] = faces[3], faces[1]
        return faces

    def UP(self, prime=False):
        face = self.face_up
        faces = [self.face_back, self.face_left, self.face_front, self.face_right]
        tmp = faces[0].copy()
        faces.append(tmp)
        if not prime:
            face = np.rot90(face, k=-1)
        else:
            faces = self.primeInvert(faces)
            face = np.rot90(face, k=1)
        for i in range(4):
            faces[i][0] = faces[i+1][0]
        self.face_up = face

    def DOWN(self, prime=False):
        face = self.face_down
        faces = [self.face_back, self.face_right, self.face_front, self.face_left]
        tmp = faces[0].copy()
        faces.append(tmp)
        if not prime:
            face = np.rot90(face, k=-1)
        else:
            faces = self.primeInvert(faces)
            face = np.rot90(face, k=1)
        for i in range(4):
            faces[i][2] = faces[i+1][2]
        self.face_down = face

    def RIGHT(self, prime=False):
        face = self.face_right
        faces = [np.rot90(self.face_back, k=2), self.face_up, self.face_front, self.face_down]
        tmp = faces[0].copy()
        faces.append(tmp)
        if not prime:
            face = np.rot90(face, k=-1)
        else:
            faces = self.primeInvert(faces)
            face = np.rot90(face, k=1)
        for i in range(4):
            faces[i][:, 2] = faces[i+1][:, 2]
        self.face_right = face

    def LEFT(self, prime=False):
        face = self.face_left
        faces = [np.rot90(self.face_back, k=2), self.face_down, self.face_front, self.face_up]
        tmp = faces[0].copy()
        faces.append(tmp)
        if not prime:
            face = np.rot90(face, k=-1)
        else:
            faces = self.primeInvert(faces)
            face = np.rot90(face, k=1)
        for i in range(4):
            faces[i][:, 0] = faces[i+1][:, 0]
        self.face_left = face

    def FRONT(self, prime=False):
        face = self.face_front
        faces = [np.rot90(self.face_left, k=2), np.rot90(self.face_down), self.face_right, np.rot90(self.face_up, k=-1)]
        tmp = faces[0].copy()
        faces.append(tmp)
        if not prime:
            face = np.rot90(face, k=-1)
        else:
            faces = self.primeInvert(faces)
            face = np.rot90(face, k=1)
        for i in range(4):
            faces[i][:, 0] = faces[i+1][:, 0]
        self.face_front = face

    def BACK(self, prime=False):
        face = self.face_back
        faces = [np.rot90(self.face_left, k=2), np.rot90(self.face_up, k=-1), self.face_right, np.rot90(self.face_down)]
        tmp = faces[0].copy()
        faces.append(tmp)
        if not prime:
            face = np.rot90(face, k=-1)
        else:
            faces = self.primeInvert(faces)
            face = np.rot90(face, k=1)
        for i in range(4):
            faces[i][:, 2] = faces[i+1][:, 2]
        self.face_back = face

    def scramble(self, pattern):
        pattern = pattern.replace("'", "'").replace("'", "'").replace("`", "'")
        moves = pattern.split()
        for move in moves:
            if len(move) > 2 or move[0] not in self.faces or (len(move) == 2 and move[1] not in "2'"):
                print(f"Mouvement invalide: {move}", file=sys.stderr)
                sys.exit(1)
            if len(move) == 2:
                if move[1] == "'":
                    self.faces[move[0]](True)
                elif move[1] == "2":
                    self.faces[move[0]]()
                    self.faces[move[0]]()
            else:
                self.faces[move[0]]()

    def reducePattern(self, pattern):
        if not pattern or len(pattern.strip().split()) <= 1:
            return pattern.strip()
        p = pattern.strip().split()
        change = 1
        while change > 0 and len(p) > 1:
            change = 0
            reduced = []
            i = 0
            while i < len(p) - 1:
                if p[i][0] == p[i + 1][0]:
                    change = 1
                    if len(p[i]) == 1:
                        p[i] = p[i] + "0"
                    if len(p[i+1]) == 1:
                        p[i + 1] = p[i + 1] + "0"
                    if p[i][1] == "2" and p[i+1][1] == "2":
                        pass
                    elif p[i][1] == "0" and p[i+1][1] == "0":
                        reduced.append(p[i][0] + "2")
                    elif p[i][1] == "'" and p[i+1][1] == "'":
                        reduced.append(p[i][0] + "2")
                    elif (p[i][1] == "2" and p[i+1][1] == "'") or (p[i+1][1] == "2" and p[i][1] == "'"):
                        reduced.append(p[i][0])
                    elif (p[i][1] == "2" and p[i+1][1] == "0") or (p[i+1][1] == "2" and p[i][1] == "0"):
                        reduced.append(p[i][0] + "'")
                    elif (p[i][1] == "'" and p[i+1][1] == "0") or (p[i+1][1] == "'" and p[i][1] == "0"):
                        pass
                    i += 1
                else:
                    reduced.append(p[i])
                i += 1
            if i == len(p) - 1:
                reduced.append(p[i])
            p = reduced
        return " ".join(p).strip()

# =============================================================================
# ARBRE DE RECHERCHE
# =============================================================================

class TreeCube:
    def __init__(self, cube, run, allowed=None, move=""):
        if allowed is None:
            allowed = ["F", "R", "U", "B", "L", "D"]
        self.run = run
        self.childs = []
        self.cube = cube
        self.move = move
        self.depth = 0
        self.all_allowed = allowed.copy()
        self.moves = {
            "F": self.rotate, "R": self.rotate, "U": self.rotate,
            "B": self.rotate, "L": self.rotate, "D": self.rotate,
            "F'": self.prime, "R'": self.prime, "U'": self.prime,
            "B'": self.prime, "L'": self.prime, "D'": self.prime,
            "F2": self.double, "R2": self.double, "U2": self.double,
            "B2": self.double, "L2": self.double, "D2": self.double,
        }
        # Pruning des mouvements redondants
        if self.move != "":
            allowed = [k for k in allowed if k[0] != self.move[0]]
            if self.move[0] == "B":
                allowed = [k for k in allowed if k[0] != "F"]
            elif self.move[0] == "D":
                allowed = [k for k in allowed if k[0] != "U"]
            elif self.move[0] == "L":
                allowed = [k for k in allowed if k[0] != "R"]
        self.allowed = allowed.copy()
        for i in allowed:
            if len(i) == 1:
                if i + "'" not in self.allowed:
                    self.allowed.append(i + "'")
                if i + "2" not in self.allowed:
                    self.allowed.append(i + "2")

    def rotate(self, face, prime=False, double=False):
        cube = Cube()
        cube.copy(self.cube)
        if prime:
            cube.faces[face](True)
        elif double:
            cube.faces[face]()
            cube.faces[face]()
        else:
            cube.faces[face]()
        return cube

    def prime(self, face):
        return self.rotate(face, prime=True)

    def double(self, face):
        return self.rotate(face, double=True)

    def searchChilds(self, func, **kwargs):
        for move in self.allowed:
            cube = self.moves[move](move[0])
            node = TreeCube(cube, self.run, allowed=self.all_allowed, move=move)
            node.depth = self.depth + 1
            self.childs.append(node)
            if func(cube, **kwargs):
                return move
        return None

    def nextDepth(self, depth, func, **kwargs):
        while self.depth <= depth and self.run.is_set():
            if self.depth < depth:
                for child in self.childs:
                    m = child.nextDepth(depth, func, **kwargs)
                    if m is not None:
                        return (self.move + " " + m).strip()
            else:
                m = self.searchChilds(func, **kwargs)
                if m is not None:
                    return (self.move + " " + m).strip()
                return None
            if self.depth == 0:
                depth += 1
            else:
                return None
        return None

    def search(self, func, **kwargs):
        m = self.searchChilds(func, **kwargs)
        if m is not None:
            return (self.move + " " + m).strip()
        return self.nextDepth(1, func, **kwargs)

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

pattern = []

def rotate(cube, s, save=True):
    if s is None or s == "":
        return cube
    moves = s.split()
    for move in moves:
        if len(move) > 2 or move[0] not in cube.faces or (len(move) == 2 and move[1] not in "2'"):
            return cube
        if len(move) == 2:
            if move[1] == "'":
                cube.faces[move[0]](True)
            elif move[1] == "2":
                cube.faces[move[0]]()
                cube.faces[move[0]]()
        else:
            cube.faces[move[0]]()
        if save:
            pattern.append(move)
    return cube

def find(cube, run, i, return_code, allowed, func, kwargs):
    cube1 = Cube()
    cube1.copy(cube)
    if i != "":
        if len(i) > 1 and i[1] == "2":
            cube1.faces[i[0]]()
            cube1.faces[i[0]]()
        elif len(i) > 1 and i[1] == "'":
            cube1.faces[i[0]](True)
        else:
            cube1.faces[i[0]]()
    if func(cube1, **kwargs):
        return_code["start_"+i] = i
        run.clear()
        return
    tree = TreeCube(cube1, run, allowed=allowed, move=i)
    m = tree.search(func, **kwargs)
    if m is not None:
        return_code["start_"+i] = m
    run.clear()

def exploration(cube, allowed, func, multi=False, **kwargs):
    if func(cube, **kwargs):
        return ""
    if not multi:
        start = [""]
    else:
        start = [x for x in allowed]
        s = len(start)
        for i in range(s):
            if len(start[i]) == 1:
                start.append(start[i] + "'")
                start.append(start[i] + "2")
    
    processes = []
    manager = mp.Manager()
    return_code = manager.dict()
    run = manager.Event()
    run.set()
    
    for i in start:
        process = mp.Process(target=find, args=(cube, run, i, return_code, allowed, func, kwargs))
        processes.append(process)
        process.start()
    
    for process in processes:
        process.join()
    
    results = [x.split() for x in return_code.values() if x is not None]
    if results:
        return " ".join(min(results, key=len))
    return ""

# =============================================================================
# PHASE 1: EDGE ORIENTATION
# =============================================================================

def badEdges(sticker, sticker2):
    if sticker[0] == "L" or sticker[0] == "R" or \
       ((sticker[0] == "F" or sticker[0] == "B") and (sticker2[0] == "U" or sticker2[0] == "D")):
        return 1
    return 0

def eoDetection(cube):
    bad_edges = {}
    bad_edges["u1"] = badEdges(cube.face_up.item(1), cube.face_back.item(1))
    bad_edges["u3"] = badEdges(cube.face_up.item(3), cube.face_left.item(1))
    bad_edges["u5"] = badEdges(cube.face_up.item(5), cube.face_right.item(1))
    bad_edges["u7"] = badEdges(cube.face_up.item(7), cube.face_front.item(1))
    bad_edges["d1"] = badEdges(cube.face_down.item(1), cube.face_front.item(7))
    bad_edges["d3"] = badEdges(cube.face_down.item(3), cube.face_left.item(7))
    bad_edges["d5"] = badEdges(cube.face_down.item(5), cube.face_right.item(7))
    bad_edges["d7"] = badEdges(cube.face_down.item(7), cube.face_back.item(7))
    bad_edges["f3"] = badEdges(cube.face_front.item(3), cube.face_left.item(5))
    bad_edges["f5"] = badEdges(cube.face_front.item(5), cube.face_right.item(3))
    bad_edges["b3"] = badEdges(cube.face_back.item(3), cube.face_right.item(5))
    bad_edges["b5"] = badEdges(cube.face_back.item(5), cube.face_left.item(3))
    return bad_edges

def badEdgesOnFB(cube, nb, get=False):
    bad_edges = eoDetection(cube)
    bad = [k for k, v in bad_edges.items() if v == 1]
    f = [k[0] for k in bad].count("f") + bad_edges["u7"] + bad_edges["d1"]
    b = [k[0] for k in bad].count("b") + bad_edges["u1"] + bad_edges["d7"]
    if get:
        return (f, b)
    return f == nb or b == nb

def edgeOrienting(cube, bad_edges):
    bad = [k for k, v in bad_edges.items() if v == 1]
    if len(bad) == 0:
        return cube
    if bad == ['u1', 'u7', 'd1', 'd7'] or bad == ['u3', 'u5', 'd3', 'd5']:
        cube = rotate(cube, "U")
    elif len(bad) > 2:
        m = exploration(cube, ["R", "U", "L", "D", "F2", "B2"], badEdgesOnFB, nb=4)
        cube = rotate(cube, m)
        if badEdgesOnFB(cube, 4, True)[0] == 4:
            cube = rotate(cube, "F")
        else:
            cube = rotate(cube, "B")
    else:
        m = exploration(cube, ["R", "U", "L", "D", "F2", "B2"], badEdgesOnFB, nb=1)
        cube = rotate(cube, m)
        if badEdgesOnFB(cube, 1, True)[0] == 1:
            cube = rotate(cube, "F")
        else:
            cube = rotate(cube, "B")
    return cube

# Second axis EO
def badEdges2(sticker, sticker2):
    if sticker[0] == "B" or sticker[0] == "F" or \
       ((sticker[0] == "L" or sticker[0] == "R") and (sticker2[0] == "U" or sticker2[0] == "D")):
        return 1
    return 0

def eoDetection2(cube):
    bad_edges = {}
    bad_edges["u1"] = badEdges2(cube.face_up.item(1), cube.face_back.item(1))
    bad_edges["u3"] = badEdges2(cube.face_up.item(3), cube.face_left.item(1))
    bad_edges["u5"] = badEdges2(cube.face_up.item(5), cube.face_right.item(1))
    bad_edges["u7"] = badEdges2(cube.face_up.item(7), cube.face_front.item(1))
    bad_edges["d1"] = badEdges2(cube.face_down.item(1), cube.face_front.item(7))
    bad_edges["d3"] = badEdges2(cube.face_down.item(3), cube.face_left.item(7))
    bad_edges["d5"] = badEdges2(cube.face_down.item(5), cube.face_right.item(7))
    bad_edges["d7"] = badEdges2(cube.face_down.item(7), cube.face_back.item(7))
    bad_edges["r3"] = badEdges2(cube.face_right.item(3), cube.face_front.item(5))
    bad_edges["r5"] = badEdges2(cube.face_right.item(5), cube.face_back.item(3))
    bad_edges["l3"] = badEdges2(cube.face_left.item(3), cube.face_back.item(5))
    bad_edges["l5"] = badEdges2(cube.face_left.item(5), cube.face_front.item(3))
    return bad_edges

def badEdgesOnRL(cube, nb, get=False):
    bad_edges = eoDetection2(cube)
    bad = [k for k, v in bad_edges.items() if v == 1]
    r = [k[0] for k in bad].count("r") + bad_edges["u5"] + bad_edges["d5"]
    l = [k[0] for k in bad].count("l") + bad_edges["u3"] + bad_edges["d3"]
    if get:
        return (r, l)
    return r == nb or l == nb

def edgeOrienting2(cube, bad_edges):
    bad = [k for k, v in bad_edges.items() if v == 1]
    if len(bad) == 0:
        return cube
    if bad == ['u1', 'u7', 'd1', 'd7'] or bad == ['u3', 'u5', 'd3', 'd5']:
        cube = rotate(cube, "U")
    if len(bad) > 2:
        m = exploration(cube, ["R2", "U", "L2", "D", "F2", "B2"], badEdgesOnRL, nb=4)
        cube = rotate(cube, m)
        if badEdgesOnRL(cube, 4, True)[0] == 4:
            cube = rotate(cube, "R")
        else:
            cube = rotate(cube, "L")
    else:
        m = exploration(cube, ["R2", "U", "L2", "D", "F2", "B2"], badEdgesOnRL, nb=1)
        cube = rotate(cube, m)
        if badEdgesOnRL(cube, 1, True)[0] == 1:
            cube = rotate(cube, "R")
        else:
            cube = rotate(cube, "L")
    return cube

def isUDColor(cube, items=None):
    if items is None:
        items = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    for i in items:
        if cube.face_up.item(i)[0] != 'U' and cube.face_up.item(i)[0] != 'D':
            return False
    for i in items:
        if cube.face_down.item(i)[0] != 'U' and cube.face_down.item(i)[0] != 'D':
            return False
    return True

# =============================================================================
# PHASE 2: CORNER ORIENTATION
# =============================================================================

def tweakCOAlgo(algo, face_up):
    if face_up == "U":
        return algo
    elif face_up == "D":
        return algo.replace('U', 'temp').replace('B', 'F').replace('D', 'U').replace('F', 'B').replace('temp', 'D')
    elif face_up == "F":
        return algo.replace('U', 'temp').replace('B', 'U').replace('D', 'B').replace('F', 'D').replace('temp', 'F')
    elif face_up == "B":
        return algo.replace('U', 'temp').replace('B', 'D').replace('D', 'F').replace('F', 'U').replace('temp', 'B')
    elif face_up == "R":
        return algo.replace('U', 'temp').replace('L', 'U').replace('D', 'L').replace('R', 'D').replace('temp', 'R')
    elif face_up == "L":
        return algo.replace('U', 'temp').replace('L', 'D').replace('D', 'R').replace('R', 'U').replace('temp', 'L')
    return algo

def tweakDRTrigger(algo, face_front):
    if face_front == "F":
        return algo
    elif face_front == "R":
        return algo.replace('F', 'temp').replace('L', 'F').replace('B', 'L').replace('R', 'B').replace('temp', 'R')
    elif face_front == "B":
        return tweakDRTrigger(tweakDRTrigger(algo, "R"), "R")
    elif face_front == "L":
        return algo.replace('F', 'temp').replace('R', 'F').replace('B', 'R').replace('L', 'B').replace('temp', 'L')
    return algo

def mirrorTweakDRTrigger(algo, mirror):
    m_algo = algo.replace("'", 'temp').replace("L ", "L' ").replace("B ", "B' ").replace("R ", "R' ").replace("F ", "F' ").replace("U ", "U' ").replace("D ", "D' ").replace("temp", "")
    if mirror == "U":
        return m_algo.replace('U', 'tempU').replace('D', 'U').replace('tempU', 'D')
    if mirror == "R":
        return m_algo.replace('R', 'tempR').replace('L', 'R').replace('tempR', 'L')
    return m_algo

def whichTrigger(cube):
    l_face = {"F": "L", "L": "B", "B": "R", "R": "F"}
    r_face = {"F": "R", "R": "B", "B": "L", "L": "F"}
    ud = ["U", "D"]
    
    for f in ["F", "R", "B", "L"]:
        # 4c patterns
        if cube.sides()[f].item(0)[0] in ud and cube.sides()[f].item(2)[0] in ud and cube.sides()[f].item(6)[0] in ud and cube.sides()[l_face[f]].item(0)[0] in ud:
            return tweakDRTrigger(tweakDRTrigger("R U' R' U2 R U' R", "L"), f)
        if cube.sides()[f].item(2)[0] in ud and cube.sides()[l_face[f]].item(2)[0] in ud and cube.sides()[l_face[f]].item(8)[0] in ud and cube.sides()[l_face[l_face[f]]].item(0)[0] in ud:
            return tweakDRTrigger("R' U' F2 U F2 R", f)
        # mirror on right
        if cube.sides()[f].item(0)[0] in ud and cube.sides()[f].item(2)[0] in ud and cube.sides()[f].item(8)[0] in ud and cube.sides()[r_face[f]].item(2)[0] in ud:
            return tweakDRTrigger(mirrorTweakDRTrigger(tweakDRTrigger("R U' R' U2 R U' R", "L"), "R"), f)
        if cube.sides()[f].item(0)[0] in ud and cube.sides()[r_face[f]].item(0)[0] in ud and cube.sides()[l_face[f]].item(6)[0] in ud and cube.sides()[r_face[r_face[f]]].item(2)[0] in ud:
            return tweakDRTrigger(mirrorTweakDRTrigger("R' U' F2 U F2 R", "R"), f)
        # mirror on top
        if cube.sides()[f].item(0)[0] in ud and cube.sides()[f].item(6)[0] in ud and cube.sides()[f].item(8)[0] in ud and cube.sides()[r_face[f]].item(6)[0] in ud:
            return tweakDRTrigger(mirrorTweakDRTrigger(tweakDRTrigger("R U' R' U2 R U' R", "L"), "U"), f)
        if cube.sides()[f].item(8)[0] in ud and cube.sides()[l_face[f]].item(8)[0] in ud and cube.sides()[l_face[f]].item(2)[0] in ud and cube.sides()[l_face[l_face[f]]].item(6)[0] in ud:
            return tweakDRTrigger(mirrorTweakDRTrigger("R' U' F2 U F2 R", "U"), f)
        # 3c patterns
        if cube.sides()[f].item(6)[0] in ud and cube.sides()[l_face[f]].item(6)[0] in ud and cube.sides()[l_face[l_face[f]]].item(2)[0] in ud:
            return tweakDRTrigger(tweakDRTrigger("R U' D R' U D' R", "L"), f)
        # mirror on right
        if cube.sides()[f].item(8)[0] in ud and cube.sides()[r_face[f]].item(8)[0] in ud and cube.sides()[r_face[r_face[f]]].item(0)[0] in ud:
            return tweakDRTrigger(mirrorTweakDRTrigger(tweakDRTrigger("R U' D R' U D' R", "L"), "R"), f)
        # mirror on top
        if cube.sides()[f].item(0)[0] in ud and cube.sides()[l_face[f]].item(0)[0] in ud and cube.sides()[l_face[l_face[f]]].item(8)[0] in ud:
            return tweakDRTrigger(mirrorTweakDRTrigger(tweakDRTrigger("R U' D R' U D' R", "L"), "U"), f)
        # 2c patterns
        if cube.sides()[f].item(2)[0] in ud and cube.sides()[l_face[f]].item(0)[0] in ud:
            return tweakDRTrigger(tweakDRTrigger("R D L2 D' R", "R"), f)
        if cube.sides()[f].item(6)[0] in ud and cube.sides()[f].item(8)[0] in ud:
            return tweakDRTrigger("R U' R2 D R2 U R", f)
        if cube.sides()[f].item(2)[0] in ud and cube.sides()[f].item(8)[0] in ud:
            return tweakDRTrigger("U R' D L2 D' R", f)
        if cube.sides()[f].item(0)[0] in ud and cube.sides()[f].item(6)[0] in ud:
            return tweakDRTrigger(tweakDRTrigger("U L' U R2 U' L", "L"), f)
        # mirror on right
        if cube.sides()[f].item(0)[0] in ud and cube.sides()[r_face[f]].item(2)[0] in ud:
            return tweakDRTrigger(mirrorTweakDRTrigger(tweakDRTrigger("R D L2 D' R", "R"), "R"), f)
        # mirror on top
        if cube.sides()[f].item(8)[0] in ud and cube.sides()[l_face[f]].item(6)[0] in ud:
            return tweakDRTrigger(mirrorTweakDRTrigger(tweakDRTrigger("R D L2 D' R", "R"), "U"), f)
        if cube.sides()[f].item(0)[0] in ud and cube.sides()[f].item(2)[0] in ud:
            return tweakDRTrigger(mirrorTweakDRTrigger("R U' R2 D R2 U R", "U"), f)
    return None

def knownDRTrigger(cube):
    return whichTrigger(cube) is not None

def UDCornersOrientation(cube):
    while not isUDColor(cube):
        m = exploration(cube, ["U", "D", "F2", "B2", "R2", "L2"], knownDRTrigger)
        cube = rotate(cube, m)
        cube = rotate(cube, whichTrigger(cube))
    return cube

# =============================================================================
# PHASE 3: CORNER PLACEMENT
# =============================================================================

def allFacesSolved(cube, items=None, faces=None):
    if items is None:
        items = range(0, 9)
    if faces is None:
        faces = ["F", "R", "B", "L", "U", "D"]
    for f in faces:
        for i in items:
            if cube.sides()[f].item(i)[0] != f:
                return False
    return True

def matchMismatchCount(cube):
    if not allFacesSolved(cube, items=[0, 2, 6, 8], faces=["U", "D"]):
        return (0, 0)
    match = 0
    mismatch = 0
    for f in ["F", "L", "B", "R"]:
        if cube.sides()[f].item(0)[0] == cube.sides()[f].item(2)[0]:
            match += 1
        if cube.sides()[f].item(6)[0] == cube.sides()[f].item(8)[0]:
            match += 1
    for f in ["F", "L", "B", "R"]:
        if cube.sides()[f].item(0)[0] != cube.sides()[f].item(2)[0]:
            mismatch += 1
        if cube.sides()[f].item(6)[0] != cube.sides()[f].item(8)[0]:
            mismatch += 1
    return (match, mismatch)

def misMatch(cube):
    test_cube = Cube()
    lowest = min(matchMismatchCount(cube))
    alg = ""
    for m in ["R' F R' B2 R F' R", "L' F L' B2 L F' L", "B' R B' L2 B R' B", "B' L B' R2 B L' B",
              "L' B L' F2 L B' L", "R' B R' F2 R B' R", "F' L F' R2 F L' F", "F' R F' L2 F R' F"]:
        test_cube.copy(cube)
        test_cube = rotate(test_cube, m, save=False)
        match, mismatch = matchMismatchCount(test_cube)
        if (match, mismatch) != (0, 0) and (match < lowest or mismatch < lowest):
            alg = m
    if alg != "":
        return alg
    return False

def cornerPlacement(cube):
    m = exploration(cube, ["U", "D", "F2", "B2", "R2", "L2"], allFacesSolved, multi=True, items=[0, 2, 6, 8], faces=["U", "D"])
    cube = rotate(cube, m)
    while 8 not in matchMismatchCount(cube):
        m = exploration(cube, ["U", "D", "F2", "B2", "R2", "L2"], misMatch)
        cube = rotate(cube, m)
        cube = rotate(cube, misMatch(cube))
    return cube

# =============================================================================
# PHASE 4: EDGE PLACEMENT
# =============================================================================

def allFacesColor(cube, items=None):
    if items is None:
        items = range(0, 9)
    opposit = {"F": "B", "R": "L", "U": "D", "B": "F", "L": "R", "D": "U"}
    faces = {"F": cube.face_front, "R": cube.face_right, "B": cube.face_back,
             "L": cube.face_left, "U": cube.face_up, "D": cube.face_down}
    for f in ["F", "R", "B", "L", "U", "D"]:
        for i in items:
            color = faces[f].item(i)[0]
            if color != f and color != opposit[f]:
                return False
    return True

def edgePlacement(cube):
    m = exploration(cube, ["U", "D", "F2", "B2", "R2", "L2"], allFacesColor, multi=True, items=[0, 2, 6, 8, 1, 3])
    cube = rotate(cube, m)
    m = exploration(cube, ["U", "D", "F2", "B2", "R2", "L2"], allFacesColor, multi=True, items=[0, 2, 6, 8, 1, 3, 5, 7])
    cube = rotate(cube, m)
    return cube

# =============================================================================
# PHASE 5: FINAL SOLVE
# =============================================================================

def searchFinalEdges(cube):
    opposit = {"F": "B", "R": "L", "U": "D", "B": "F", "L": "R", "D": "U"}
    side_oppo = {1: 1, 3: 5, 5: 3, 7: 7}
    ud_oppo = {1: 7, 3: 3, 5: 5, 7: 1}
    two_stickers = {
        "U1": "B2 R2 B2 R2 B2 R2", "U5": "F2 R2 F2 R2 F2 R2",
        "U7": "F2 L2 F2 L2 F2 L2", "U3": "B2 L2 B2 L2 B2 L2",
        "F1": "U2 R2 U2 R2 U2 R2", "F5": "D2 R2 D2 R2 D2 R2",
        "F7": "D2 L2 D2 L2 D2 L2", "F3": "U2 L2 U2 L2 U2 L2",
        "R1": "U2 B2 U2 B2 U2 B2", "R5": "D2 B2 D2 B2 D2 B2",
        "R7": "D2 F2 D2 F2 D2 F2", "R3": "U2 F2 U2 F2 U2 F2"
    }
    for f in ["F", "R"]:
        for i, j in [(1, 5), (5, 7), (7, 3), (3, 1)]:
            if (cube.sides()[f].item(i)[0] != f and cube.sides()[opposit[f]].item(side_oppo[i])[0] == f) and \
               (cube.sides()[f].item(j)[0] != f and cube.sides()[opposit[f]].item(side_oppo[j])[0] == f):
                return two_stickers[f + str(i)]
    for f in ["U"]:
        for i, j in [(1, 5), (5, 7), (7, 3), (3, 1)]:
            if (cube.sides()[f].item(i)[0] != f and cube.sides()[opposit[f]].item(ud_oppo[i])[0] == f) and \
               (cube.sides()[f].item(j)[0] != f and cube.sides()[opposit[f]].item(ud_oppo[j])[0] == f):
                return two_stickers[f + str(i)]
    return ""

def finalEdges2(cube, done=None, get=False):
    if done is None:
        done = []
    if "F" in done and "R" in done and "U" in done:
        return ["F", "R", "U"]
    if not allFacesSolved(cube, items=[0, 2, 6, 8]):
        return False
    for f in done:
        for i in [1, 3, 5, 7]:
            if cube.sides()[f].item(i)[0] != f:
                return False
    good = []
    for f in ["F", "R", "U"]:
        for i in [1, 3, 5, 7]:
            if cube.sides()[f].item(i)[0] != f:
                break
            if i == 7:
                good.append(f)
    if not get and len(good) <= len(done):
        return False
    return good

def finalSolve(cube):
    m = exploration(cube, ["U2", "D2", "F2", "B2", "R2", "L2"], allFacesSolved, multi=True, items=[0, 2, 6, 8])
    cube = rotate(cube, m)
    while not allFacesSolved(cube):
        while searchFinalEdges(cube) != "":
            cube = rotate(cube, searchFinalEdges(cube))
        m = exploration(cube, ["U2", "D2", "F2", "B2", "R2", "L2"], finalEdges2, multi=True, done=finalEdges2(cube, get=True))
        cube = rotate(cube, m)
    return cube

# =============================================================================
# SOLVEUR PRINCIPAL
# =============================================================================

def solver(cube):
    global pattern
    pattern = []

    # Phase 1: Edge Orientation (premier axe)
    bad_edges = eoDetection(cube)
    while sum(bad_edges.values()) > 0:
        cube = edgeOrienting(cube, bad_edges)
        bad_edges = eoDetection(cube)

    # Phase 1b: Edge Orientation (second axe si nécessaire)
    if not isUDColor(cube, [1, 3, 5, 7]):
        bad_edges = eoDetection2(cube)
        while sum(bad_edges.values()) > 0:
            cube = edgeOrienting2(cube, bad_edges)
            bad_edges = eoDetection2(cube)

    # Phase 2: Corner Orientation
    cube = UDCornersOrientation(cube)

    # Phase 3: Corner Placement
    cube = cornerPlacement(cube)

    # Phase 4: Edge Placement
    cube = edgePlacement(cube)

    # Phase 5: Final Solve
    cube = finalSolve(cube)

    return cube.reducePattern(" ".join(pattern))

# =============================================================================
# MAIN
# =============================================================================

def main():
    if len(sys.argv) != 2:
        print("Usage: python thistlethwaite.py \"SCRAMBLE\"")
        print("Exemple: python thistlethwaite.py \"R U R' U'\"")
        sys.exit(0)

    scramble = sys.argv[1]
    cube = Cube()
    cube.scramble(scramble)
    
    solution = solver(cube)
    print(solution)

if __name__ == "__main__":
    main()
