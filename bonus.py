import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
from moves import Cube

# Mapping des couleurs
COLOR_MAP = {
    'W': (1.0, 1.0, 1.0),  # White
    'Y': (1.0, 1.0, 0.0),  # Yellow
    'G': (0.0, 1.0, 0.0),  # Green
    'B': (0.0, 0.0, 1.0),  # Blue
    'R': (1.0, 0.0, 0.0),  # Red
    'O': (1.0, 0.5, 0.0),  # Orange
}

# -----------------------------
# DESSIN D'UN CUBE AVEC COULEURS
# -----------------------------
def draw_cube(size=0.45, colors=None):
    vertices = [
        (-size, -size, -size),  # 0
        ( size, -size, -size),  # 1
        ( size,  size, -size),  # 2
        (-size,  size, -size),  # 3
        (-size, -size,  size),  # 4
        ( size, -size,  size),  # 5
        ( size,  size,  size),  # 6
        (-size,  size,  size),  # 7
    ]

    # Définition des faces (ordre des vertices pour chaque face)
    # Toutes les faces sont ordonnées dans le sens trigonométrique (CCW) vu depuis l'extérieur
    faces = {
        'U': [3, 2, 6, 7],  # Up (y+)
        'D': [0, 1, 5, 4],  # Down (y-)
        'F': [4, 5, 6, 7],  # Front (z+)
        'B': [1, 0, 3, 2],  # Back (z-)
        'R': [5, 1, 2, 6],  # Right (x+)
        'L': [0, 4, 7, 3],  # Left (x-)
    }

    # Couleurs par défaut (gris)
    default_color = (0.3, 0.3, 0.3)

    # Dessiner les faces colorées
    glBegin(GL_QUADS)
    for face_name, face_vertices in faces.items():
        if colors and face_name in colors:
            glColor3fv(colors[face_name])
        else:
            glColor3fv(default_color)
        for vertex_idx in face_vertices:
            glVertex3fv(vertices[vertex_idx])
    glEnd()

    # Dessiner les arêtes en noir
    edges = [
        (0,1),(1,2),(2,3),(3,0),
        (4,5),(5,6),(6,7),(7,4),
        (0,4),(1,5),(2,6),(3,7)
    ]

    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(vertices[vertex])
    glEnd()

# -----------------------------
# CLASSE CUBIE
# -----------------------------
class Cubie:
    def __init__(self, x, y, z, grid_pos, cube_state):
        self.pos = [x, y, z]
        self.rot = [0, 0, 0]
        self.grid_pos = grid_pos  # Position dans la grille (x, y, z) ∈ {-1, 0, 1}
        self.cube_state = cube_state  # Référence au cube logique
        self.colors = {}
        self.update_colors()

    def get_face_index(self, face_name, gx, gy, gz):
        """Calcule l'index de la pièce dans cube.pieces pour une face donnée"""
        if face_name == 'U' and gy == 1:
            # Face U: indices 0-8
            row = 1 - gz  # gz=1→row=2, gz=0→row=1, gz=-1→row=0
            col = 1 + gx
            return 0 + row * 3 + col
        elif face_name == 'D' and gy == -1:
            # Face D: indices 45-53
            row = 1 - gz  # gz=1→row=0, gz=0→row=1, gz=-1→row=2
            col = gx + 1
            return 45 + row * 3 + col
        elif face_name == 'F' and gz == 1:
            # Face F: indices 18-26
            row = 1 - gy
            col = gx + 1
            return 18 + row * 3 + col
        elif face_name == 'B' and gz == -1:
            # Face B: indices 36-44
            row = 1 - gy
            col = 1 - gx
            return 36 + row * 3 + col
        elif face_name == 'R' and gx == 1:
            # Face R: indices 27-35
            row = 1 - gy
            col = 1 - gz
            return 27 + row * 3 + col
        elif face_name == 'L' and gx == -1:
            # Face L: indices 9-17
            row = 1 - gy
            col = gz + 1
            return 9 + row * 3 + col
        return None

    def update_colors(self):
        """Met à jour les couleurs du cubie depuis le cube logique"""
        gx, gy, gz = self.grid_pos
        self.colors = {}

        faces_to_check = [
            ('U', gy == 1),
            ('D', gy == -1),
            ('F', gz == 1),
            ('B', gz == -1),
            ('R', gx == 1),
            ('L', gx == -1),
        ]

        for face_name, condition in faces_to_check:
            if condition:
                idx = self.get_face_index(face_name, gx, gy, gz)
                # Vérifier l'index retourné par get_face_index avant d'accéder au cube logique
                if idx is None:
                    # Cas improbable mais utile pour le debug
                    print(f"[update_colors] Warning: get_face_index returned None for face {face_name} grid={self.grid_pos}")
                    continue
                if not (0 <= idx < len(self.cube_state.pieces)):
                    print(f"[update_colors] Warning: index hors gamme pour face {face_name} grid={self.grid_pos} idx={idx}")
                    continue
                color_letter = self.cube_state.pieces[idx].color
                # Utiliser une couleur par défaut si la lettre n'est pas dans COLOR_MAP
                self.colors[face_name] = COLOR_MAP.get(color_letter, (0.5, 0.5, 0.5))

    def draw(self):
        glPushMatrix()
        glTranslatef(*self.pos)
        glRotatef(self.rot[0], 1, 0, 0)
        glRotatef(self.rot[1], 0, 1, 0)
        glRotatef(self.rot[2], 0, 0, 1)
        draw_cube(colors=self.colors)
        glPopMatrix()

# -----------------------------
# ROTATION D'UNE FACE
# -----------------------------
def rotate_face(cubies, axis, value, angle_step):
    idx = {'x': 0, 'y': 1, 'z': 2}[axis]
    
    for c in cubies:
        if round(c.pos[idx]) == value:
            # Rotation autour du centre de la face
            rad = math.radians(angle_step)
            x, y, z = c.pos
            
            if axis == 'x':
                # Rotation autour de l'axe X
                new_y = y * math.cos(rad) - z * math.sin(rad)
                new_z = y * math.sin(rad) + z * math.cos(rad)
                c.pos[1] = new_y
                c.pos[2] = new_z
            elif axis == 'y':
                # Rotation autour de l'axe Y
                new_x = x * math.cos(rad) + z * math.sin(rad)
                new_z = -x * math.sin(rad) + z * math.cos(rad)
                c.pos[0] = new_x
                c.pos[2] = new_z
            elif axis == 'z':
                # Rotation autour de l'axe Z
                new_x = x * math.cos(rad) - y * math.sin(rad)
                new_y = x * math.sin(rad) + y * math.cos(rad)
                c.pos[0] = new_x
                c.pos[1] = new_y
            
            # Mise à jour de la rotation locale du cubie
            c.rot[idx] += angle_step

# -----------------------------
# MAIN
# -----------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Rubik's Cube - OpenGL")

    gluPerspective(45, 800 / 600, 0.1, 50.0)
    glTranslatef(0.0, 0.0, -10)

    # Vue diagonale : rotation autour de X et Y
    glRotatef(30, 1, 0, 0)  # Inclinaison vers le bas (vue de haut)
    glRotatef(-45, 0, 1, 0)  # Rotation vers la gauche (vue de droite)

    glEnable(GL_DEPTH_TEST)

    # Initialiser le cube logique
    cube_state = Cube()

    # Création des 27 cubies
    cubies = []
    for x in [-1, 0, 1]:
        for y in [-1, 0, 1]:
            for z in [-1, 0, 1]:
                grid_pos = (x, y, z)
                cubies.append(Cubie(x * 1.1, y * 1.1, z * 1.1, grid_pos, cube_state))

    clock = pygame.time.Clock()
    rotating = False
    angle_done = 0
    rotation_direction = 0

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            if event.type == KEYDOWN:
                if event.key == K_r and not rotating:
                    rotating = True
                    angle_done = 0
                    rotation_direction = 1
                if event.key == K_l and not rotating:
                    rotating = True
                    angle_done = 0
                    rotation_direction = 2
                if event.key == K_u and not rotating:
                    rotating = True
                    angle_done = 0
                    rotation_direction = 3
                if event.key == K_d and not rotating:
                    rotating = True
                    angle_done = 0
                    rotation_direction = 4
                if event.key == K_f and not rotating:
                    rotating = True
                    angle_done = 0
                    rotation_direction = 5
                if event.key == K_b and not rotating:
                    rotating = True
                    angle_done = 0
                    rotation_direction = 6

        # Animation de la rotation
        if rotating:
            step = 3  # degrés par frame
            if rotation_direction == 1:
                # R
                rotate_face(cubies, 'x', 1, -step)
            elif rotation_direction == 2:
                # L
                rotate_face(cubies, 'x', -1, step)
            elif rotation_direction == 3:
                # U
                rotate_face(cubies, 'y', 1, -step)
            elif rotation_direction == 4:
                # D
                rotate_face(cubies, 'y', -1, step)
            elif rotation_direction == 5:
                # F
                rotate_face(cubies, 'z', 1, -step)
            elif rotation_direction == 6:
                # B
                rotate_face(cubies, 'z', -1, step)
            
            angle_done += step
            if angle_done >= 90:
                rotating = False
                
                # DEBUG: Afficher l'état AVANT la mise à jour
                print("\n" + "="*60)
                print(f"ROTATION TERMINÉE - Direction: {rotation_direction}")
                print("="*60)
                
                # Afficher la face U AVANT la mise à jour des positions
                print("\n--- FACE U AVANT mise à jour grid_pos ---")
                u_cubies_before = sorted([c for c in cubies if c.grid_pos[1] == 1], 
                                        key=lambda x: (-x.grid_pos[2], x.grid_pos[0]))
                for i, c in enumerate(u_cubies_before):
                    if i % 3 == 0:
                        print()
                    idx = c.get_face_index('U', c.grid_pos[0], c.grid_pos[1], c.grid_pos[2])
                    color = cube_state.pieces[idx].color if idx is not None else '?'
                    print(f"[{color} pos:{c.pos[0]:5.2f},{c.pos[1]:5.2f},{c.pos[2]:5.2f} grid:{c.grid_pos}]", end=" ")
                print()
                
                # D'abord, mettre à jour les grid_pos après la rotation 3D
                for c in cubies:
                    # Arrondir les positions pour éviter les erreurs de float
                    c.pos[0] = round(c.pos[0] / 1.1) * 1.1
                    c.pos[1] = round(c.pos[1] / 1.1) * 1.1
                    c.pos[2] = round(c.pos[2] / 1.1) * 1.1
                    
                    # Mettre à jour grid_pos en fonction de la nouvelle position
                    c.grid_pos = (
                        round(c.pos[0] / 1.1),
                        round(c.pos[1] / 1.1),
                        round(c.pos[2] / 1.1)
                    )
                    
                    # Réinitialiser les rotations locales
                    c.rot = [0, 0, 0]
                
                # Afficher la face U APRÈS la mise à jour des positions
                print("\n--- FACE U APRÈS mise à jour grid_pos (AVANT rotation logique) ---")
                u_cubies_after = sorted([c for c in cubies if c.grid_pos[1] == 1], 
                                       key=lambda x: (-x.grid_pos[2], x.grid_pos[0]))
                for i, c in enumerate(u_cubies_after):
                    if i % 3 == 0:
                        print()
                    idx = c.get_face_index('U', c.grid_pos[0], c.grid_pos[1], c.grid_pos[2])
                    color = cube_state.pieces[idx].color if idx is not None else '?'
                    print(f"[{color} idx:{idx:2d} grid:{c.grid_pos}]", end=" ")
                print()
                
                # Ensuite, appliquer la rotation au cube logique
                print("\n--- État du cube AVANT rotation logique ---")
                print(f"Face U (indices 0-8): {[cube_state.pieces[i].color for i in range(9)]}")
                
                if rotation_direction == 1:
                    cube_state.rotate_face_clockwise("R")
                elif rotation_direction == 2:
                    cube_state.rotate_face_clockwise("L")
                elif rotation_direction == 3:
                    for _ in range(3):
                        cube_state.rotate_face_clockwise("U")
                elif rotation_direction == 4:
                    cube_state.rotate_face_clockwise("D")
                elif rotation_direction == 5:
                    cube_state.rotate_face_clockwise("F")
                elif rotation_direction == 6:
                    cube_state.rotate_face_clockwise("B")
                
                print("\n--- État du cube APRÈS rotation logique ---")
                print(f"Face U (indices 0-8): {[cube_state.pieces[i].color for i in range(9)]}")
                
                # Enfin, mettre à jour les couleurs de tous les cubies depuis le cube logique
                for c in cubies:
                    c.update_colors()
                
                # Afficher la face U APRÈS la mise à jour des couleurs
                print("\n--- FACE U FINALE (après update_colors) ---")
                for i, c in enumerate(u_cubies_after):
                    if i % 3 == 0:
                        print()
                    idx = c.get_face_index('U', c.grid_pos[0], c.grid_pos[1], c.grid_pos[2])
                    color = cube_state.pieces[idx].color if idx is not None else '?'
                    print(f"[{color}]", end=" ")
                print("\n" + "="*60 + "\n")

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        for c in cubies:
            c.draw()

        pygame.display.flip()

    pygame.quit()

# -----------------------------
# POINT D'ENTRÉE
# -----------------------------
if __name__ == "__main__":
    main()