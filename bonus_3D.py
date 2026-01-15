import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# ======================================================
# CONFIG
# ======================================================
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

# ======================================================
# DESSIN D'UN CUBIE
# ======================================================
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

# ======================================================
# CUBIE
# ======================================================
class Cubie:
    def __init__(self, x, y, z):
        self.pos = [x, y, z]
        self.rot = [0, 0, 0]

        # Chaque cubie a TOUJOURS 6 faces
        self.faces = {
            'U': 'W' if y == 1 else None,
            'D': 'Y' if y == -1 else None,
            'F': 'G' if z == 1 else None,
            'B': 'B' if z == -1 else None,
            'R': 'R' if x == 1 else None,
            'L': 'O' if x == -1 else None,
        }

    def rotate_faces(self, axis, direction=1):
        # rotate the face normals by ±90° around the given axis and reassign faces
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
            # determine target face by the dominant coordinate
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

# ======================================================
# ROTATION D'UNE FACE
# ======================================================
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

# ======================================================
# MAIN
# ======================================================
def main():
    pygame.init()
    pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
    gluPerspective(45, 800/600, 0.1, 50)
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

    while True:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit()
                return
            if e.type == KEYDOWN and not rotating:
                # avoid reusing a stale `axis` when only Shift is pressed
                axis = layer = None
                # détecter shift pour la version prime (inverse)
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
                # clear pending axis/layer so subsequent modifier presses don't restart the last move
                axis = layer = None

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        for c in cubies:
            c.draw()
        pygame.display.flip()

if __name__ == "__main__":
    main()
