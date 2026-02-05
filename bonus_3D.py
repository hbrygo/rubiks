import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import sys
from main import allowed_moves

CUBE_GAP = 1.1
ROT_STEP = 3

COLOR_MAP = {
    'W': (1, 1, 1),
    'Y': (1, 1, 0),
    'R': (1, 0, 0),
    'O': (1, 0.5, 0),
    'B': (0, 0, 1),
    'G': (0, 1, 0),
    None: (0.25, 0.25, 0.25)
}

WINDOW_HEIGHT = 600
WINDOW_WIDTH = 800

def draw_cube(size=0.45, colors=None):
    vertices = [
        (-size,-size,-size),(size,-size,-size),
        (size,size,-size),(-size,size,-size),
        (-size,-size,size),(size,-size,size),
        (size,size,size),(-size,size,size)
    ]

    faces = {
        'U':[3,2,6,7], 'D':[0,1,5,4],
        'F':[4,5,6,7], 'B':[1,0,3,2],
        'R':[5,1,2,6], 'L':[0,4,7,3]
    }

    glBegin(GL_QUADS)
    for f, idxs in faces.items():
        glColor3fv(COLOR_MAP[colors[f]])
        for i in idxs:
            glVertex3fv(vertices[i])
    glEnd()

    glColor3f(0,0,0)
    glLineWidth(2)
    glBegin(GL_LINES)
    edges = [
        (0,1),(1,2),(2,3),(3,0),
        (4,5),(5,6),(6,7),(7,4),
        (0,4),(1,5),(2,6),(3,7)
    ]
    for e in edges:
        for v in e:
            glVertex3fv(vertices[v])
    glEnd()

class Cubie:
    def __init__(self, x, y, z):
        self.pos = [x, y, z]
        self.rot = [0, 0, 0]

        self.faces = {
            'U': 'W' if y == 1 else None,
            'D': 'Y' if y == -1 else None,
            'F': 'G' if z == 1 else None,
            'B': 'B' if z == -1 else None,
            'R': 'R' if x == 1 else None,
            'L': 'O' if x == -1 else None,
        }

    def rotate_faces(self, axis, direction=1):
        old = self.faces.copy()
        new = {k: None for k in old}
        angle = math.radians(90 * direction)
        s = math.sin(angle)
        c = math.cos(angle)

        def rot(vec):
            x, y, z = vec
            if axis == 'x':
                return (x, y * c - z * s, y * s + z * c)
            if axis == 'y':
                return (x * c + z * s, y, -x * s + z * c)
            if axis == 'z':
                return (x * c - y * s, x * s + y * c, z)

        normals = {
            'U': (0, 1, 0), 'D': (0, -1, 0),
            'F': (0, 0, 1), 'B': (0, 0, -1),
            'R': (1, 0, 0), 'L': (-1, 0, 0),
        }

        for label, vec in normals.items():
            rx, ry, rz = rot(vec)
            if abs(rx) > 0.5:
                tgt = 'R' if rx > 0 else 'L'
            elif abs(ry) > 0.5:
                tgt = 'U' if ry > 0 else 'D'
            else:
                tgt = 'F' if rz > 0 else 'B'
            new[tgt] = old[label]

        self.faces = new

    def draw(self):
        glPushMatrix()
        glTranslatef(*self.pos)
        glRotatef(self.rot[0], 1, 0, 0)
        glRotatef(self.rot[1], 0, 1, 0)
        glRotatef(self.rot[2], 0, 0, 1)
        draw_cube(colors=self.faces)
        glPopMatrix()

def rotate_face(cubies, axis, layer, step, direction=1):
    rad = math.radians(step * direction)
    idx = 'xyz'.index(axis)

    for c in cubies:
        if round(c.pos[idx] / CUBE_GAP) == layer:
            x, y, z = c.pos

            if axis == 'x':
                c.pos[1] = y * math.cos(rad) - z * math.sin(rad)
                c.pos[2] = y * math.sin(rad) + z * math.cos(rad)
                c.rot[0] += step * direction

            elif axis == 'y':
                c.pos[0] = x * math.cos(rad) + z * math.sin(rad)
                c.pos[2] = -x * math.sin(rad) + z * math.cos(rad)
                c.rot[1] += step * direction

            elif axis == 'z':
                c.pos[0] = x * math.cos(rad) - y * math.sin(rad)
                c.pos[1] = x * math.sin(rad) + y * math.cos(rad)
                c.rot[2] += step * direction

def invert_move(move: str) -> str:
    if move.endswith("'"):
        return move[:-1]
    if move.endswith("2"):
        return move
    return move + "'"

class SolutionPlayer:
    """Non-blocking controller for solution sequence with prev/next navigation."""
    def __init__(self, solution: str):
        self.tab = solution.split()
        self.index = 0
        self.pending_move = None

    def next(self):
        if self.index >= len(self.tab):
            return None
        m = self.tab[self.index]
        self.index += 1
        self.pending_move = m
        return m

    def prev(self):
        if self.index == 0:
            return None
        self.index -= 1
        m = self.tab[self.index]
        inv = invert_move(m)
        self.pending_move = inv
        return inv

    def has_pending(self):
        return self.pending_move is not None

    def pop_pending(self):
        m = self.pending_move
        self.pending_move = None
        return m

    def finished(self):
        return self.index >= len(self.tab) and not self.has_pending()

def main(shuffle, solution):
    pygame.init()
    pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF | OPENGL)
    gluPerspective(45, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 50)
    glTranslatef(0, 0, -10)
    glRotatef(30, 1, 0, 0)
    glRotatef(-45, 0, 1, 0)
    glEnable(GL_DEPTH_TEST)

    cubies = [
        Cubie(x, y, z)
        for x in (-1,0,1)
        for y in (-1,0,1)
        for z in (-1,0,1)
    ]
    for c in cubies:
        c.pos = [v * CUBE_GAP for v in c.pos]

    clock = pygame.time.Clock()
    rotating = False
    axis = layer = None
    angle = 0
    direction = 1

    initial_solution = solution.strip()
    solution = ""
    solution_player = None

    while True:
        clock.tick(60)

        # shuffle
        if shuffle.strip() and not rotating:
            moves = shuffle.split()
            base_move = moves.pop(0)
            shuffle = " ".join(moves)
            if base_move.endswith("2"):
                base_move = base_move[:-1]
                shuffle = base_move + " " + shuffle

            if base_move == "R":
                axis, layer, direction = 'x', 1, -1
            elif base_move == "R'":
                axis, layer, direction = 'x', 1, 1
            elif base_move == "L":
                axis, layer, direction = 'x', -1, 1
            elif base_move == "L'":
                axis, layer, direction = 'x', -1, -1
            elif base_move == "U":
                axis, layer, direction = 'y', 1, -1
            elif base_move == "U'":
                axis, layer, direction = 'y', 1, 1
            elif base_move == "D":
                axis, layer, direction = 'y', -1, 1
            elif base_move == "D'":
                axis, layer, direction = 'y', -1, -1
            elif base_move == "F":
                axis, layer, direction = 'z', 1, -1
            elif base_move == "F'":
                axis, layer, direction = 'z', 1, 1
            elif base_move == "B":
                axis, layer, direction = 'z', -1, 1
            elif base_move == "B'":
                axis, layer, direction = 'z', -1, -1

            rotating = True
            angle = 0
            if not shuffle:
                print("Shuffle finished")

        # solution
        if not shuffle.strip() and initial_solution and solution_player is None and not rotating:
            solution_player = SolutionPlayer(initial_solution)

        if solution_player and solution_player.has_pending() and not rotating:
            mv = solution_player.pop_pending()
            times = 1
            if mv.endswith("2"):
                times = 2
                mv = mv[:-1]

            if mv == "R":
                axis, layer, direction = 'x', 1, -1
            elif mv == "R'":
                axis, layer, direction = 'x', 1, 1
            elif mv == "L":
                axis, layer, direction = 'x', -1, 1
            elif mv == "L'":
                axis, layer, direction = 'x', -1, -1
            elif mv == "U":
                axis, layer, direction = 'y', 1, -1
            elif mv == "U'":
                axis, layer, direction = 'y', 1, 1
            elif mv == "D":
                axis, layer, direction = 'y', -1, 1
            elif mv == "D'":
                axis, layer, direction = 'y', -1, -1
            elif mv == "F":
                axis, layer, direction = 'z', 1, -1
            elif mv == "F'":
                axis, layer, direction = 'z', 1, 1
            elif mv == "B":
                axis, layer, direction = 'z', -1, 1
            elif mv == "B'":
                axis, layer, direction = 'z', -1, -1
            else:
                axis = layer = direction = None

            if times == 2:
                solution_player.pending_move = mv

            rotating = True
            angle = 0

        # key press + free play if no solution
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit()
                return

            if e.type == KEYDOWN and solution_player is not None and not rotating:
                if e.key == K_LEFT:
                    solution_player.prev()
                elif e.key == K_RIGHT:
                    solution_player.next()
                elif e.key == K_q or e.key == K_ESCAPE:
                    pygame.quit()
                    return
                continue

            if e.type == KEYDOWN and not rotating and not shuffle.strip() and solution_player is None:
                axis = layer = None
                dir_key = -1 if pygame.key.get_mods() & KMOD_SHIFT else 1
                if e.key == K_r: axis, layer, direction = 'x', 1, -dir_key
                if e.key == K_l: axis, layer, direction = 'x', -1, dir_key
                if e.key == K_u: axis, layer, direction = 'y', 1, -dir_key
                if e.key == K_d: axis, layer, direction = 'y', -1, dir_key
                if e.key == K_f: axis, layer, direction = 'z', 1, -dir_key
                if e.key == K_b: axis, layer, direction = 'z', -1, dir_key
                if axis is not None:
                    rotating = True
                    angle = 0
                if e.key == K_q or e.key == K_ESCAPE:
                    pygame.quit()
                    return

        # apply rotation
        if rotating:
            rotate_face(cubies, axis, layer, ROT_STEP, direction)
            angle += ROT_STEP
            if angle >= 90:
                rotating = False
                for c in cubies:
                    c.pos = [round(v / CUBE_GAP) * CUBE_GAP for v in c.pos]
                    c.rot = [0, 0, 0]
                    if round(c.pos['xyz'.index(axis)] / CUBE_GAP) == layer:
                        c.rotate_faces(axis, direction)
                axis = layer = None

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        for c in cubies:
            c.draw()
        pygame.display.flip()

if __name__ == "__main__":
    if len(sys.argv) > 3:
        print("Error: Too many arguments.")
        print("Usage: python3 bonus_3D.py \"R F B2 F'\"")
        print("Or")
        print("Usage: python3 bonus_3D.py")
        sys.exit(1)
    shuffle = sys.argv[1] if len(sys.argv) >= 2 else ""
    solution = sys.argv[2] if len(sys.argv) >= 3 else ""
    invalid_moves = [move for move in shuffle.split() if move not in allowed_moves]
    if invalid_moves:
        print(f"Invalid moves found: {', '.join(invalid_moves)}")
        sys.exit(1)
    invalid_moves = [move for move in solution.split() if move not in allowed_moves]
    if invalid_moves:
        print(f"Invalid moves found: {', '.join(invalid_moves)}")
        sys.exit(1)
    main(shuffle, solution)
