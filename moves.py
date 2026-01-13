import numpy as np

connections_map = {
            # Face U (0-8) connections
            0: [9, 38],     # U-L-B
            1: [37],        # U-B
            2: [36, 29],    # U-B-R
            3: [10],        # U-L
            4: [],
            5: [28],        # U-R
            6: [18, 11],    # U-F-L
            7: [19],        # U-F
            8: [27, 20],    # U-R-F
    
            # Face L (9-17) connections
            9:  [38, 0],    # L-B-U
            10: [3],        # L-U
            11: [6, 18],    # L-U-F
            12: [41],       # L-B
            13: [],
            14: [21],       # L-F
            15: [51, 44],   # L-D-B
            16: [48],       # L-D
            17: [24, 45],   # L-F-D

            # Face F (18-26) connections
            18: [11, 6],    # F-L-U
            19: [7],        # F-U
            20: [8, 27],    # F-U-R
            21: [14],       # F-L
            22: [],
            23: [30],       # F-R
            24: [45, 17],   # F-D-L
            25: [46],       # F-D
            26: [33, 47],   # F-R-D

            # Face R (27-35) connections
            27: [20, 8],    # R-F-U
            28: [5],        # R-U
            29: [2, 36],    # R-U-B
            30: [23],       # R-F
            31: [],
            32: [39],       # R-B
            33: [47, 26],   # R-D-F
            34: [50],       # R-D
            35: [42, 53],   # R-B-D

            # Face B (36-44) connections
            36: [29, 2],    # B-R-U
            37: [1],        # B-U
            38: [0, 9],     # B-U-L
            39: [32],       # B-R
            40: [],
            41: [12],       # B-D
            42: [53, 35],   # B-D-R
            43: [52],       # B-D
            44: [15, 51],   # B-L-D

            # Face D (45-53) connections
            45: [17, 24],   # D-L-F
            46: [25],       # D-F
            47: [26, 32],   # D-F-R
            48: [16],        # D-L
            49: [],
            50: [34],       # D-R
            51: [44, 15],   # D-B-R
            52: [43],        # D-B
            53: [35, 42],   # D-R-B
        }

class Piece:
    def __init__(self, index, color, connections=None, piece_type=None, position_3d=None):
        self.index = index
        self.color = color
        self.connections = connections or []  # Liste des index des faces liées
        self.piece_type = piece_type  # "corner", "edge", "center"
        self.original_index = index  # Pour pouvoir reset le cube
        
        # État de la pièce
        self.is_solved = True  # Au début, toutes les pièces sont résolues
        self.move_history = []  # Historique des mouvements affectant cette pièce
        
        # ID unique pour le debugging
        self.unique_id = f"{self.piece_type}_{index}" if piece_type else f"piece_{index}"
        
        # # Position 3D (x, y, z) dans l'espace du cube
        # self.position_3d = position_3d or self._calculate_3d_position(index)
        # self.original_position_3d = self.position_3d.copy()
        
        # # Orientation - angles de rotation en degrés autour de chaque axe
        # self.orientation = {"x": 0, "y": 0, "z": 0}
        # self.original_orientation = self.orientation.copy()
        
    # def _calculate_3d_position(self, index):
    #     """Calcule la position 3D basée sur l'index de la pièce"""
    #     face_idx = index // 9
    #     pos_in_face = index % 9
    #     row = pos_in_face // 3
    #     col = pos_in_face % 3
        
    #     # Coordonnées relatives à chaque face (centre du cube = 0,0,0)
    #     face_positions = {
    #         0: (col-1, 1, 1-row),    # U (Up) - face du haut
    #         1: (1, row-1, 1-col),    # R (Right) - face de droite
    #         2: (col-1, row-1, 1),    # F (Front) - face avant
    #         3: (-1, row-1, col-1),   # L (Left) - face de gauche
    #         4: (1-col, row-1, -1),   # B (Back) - face arrière (inversée horizontalement)
    #         5: (col-1, -1, row-1),   # D (Down) - face du bas
    #     }
        
    #     x, y, z = face_positions[face_idx]
    #     return np.array([x, y, z], dtype=float)
    
    def add_connection(self, connection_index):
        """Ajouter une connexion à cette pièce"""
        if connection_index not in self.connections:
            self.connections.append(connection_index)
    
    def rotate_orientation(self, axis, angle):
        """Modifie l'orientation de la pièce"""
        if axis in self.orientation:
            self.orientation[axis] = (self.orientation[axis] + angle) % 360
            self.check_solved_state()
    
    def move_to_position(self, new_position):
        """Déplace la pièce vers une nouvelle position 3D"""
        self.position_3d = np.array(new_position)
        self.check_solved_state()
    
    def add_move_to_history(self, move_notation):
        """Ajoute un mouvement à l'historique"""
        self.move_history.append(move_notation)
    
    def check_solved_state(self):
        """Vérifie si la pièce est dans son état résolu"""
        position_match = np.allclose(self.position_3d, self.original_position_3d, atol=1e-6)
        orientation_match = all(
            abs(self.orientation[axis] - self.original_orientation[axis]) < 1e-6 
            for axis in self.orientation
        )
        self.is_solved = position_match and orientation_match
    
    def reset_to_original(self):
        """Remet la pièce dans son état original"""
        self.position_3d = self.original_position_3d.copy()
        self.orientation = self.original_orientation.copy()
        self.is_solved = True
        self.move_history.clear()
    
    def get_current_face(self):
        """Retourne la face sur laquelle se trouve actuellement la pièce"""
        # Trouve quelle face est la plus proche de la position actuelle
        x, y, z = self.position_3d
        
        if abs(y - 1) < 0.1:      return "U"  # Up
        elif abs(y + 1) < 0.1:    return "D"  # Down
        elif abs(x - 1) < 0.1:    return "R"  # Right
        elif abs(x + 1) < 0.1:    return "L"  # Left
        elif abs(z - 1) < 0.1:    return "F"  # Front
        elif abs(z + 1) < 0.1:    return "B"  # Back
        else:                     return "Unknown"
    
    def is_corner(self):
        """Vérifie si c'est une pièce de coin (3 connexions)"""
        return len(self.connections) == 3
    
    def is_edge(self):
        """Vérifie si c'est une pièce d'arête (2 connexions)"""
        return len(self.connections) == 2
    
    def is_center(self):
        """Vérifie si c'est une pièce centrale (0 connexions pour les centres)"""
        return len(self.connections) == 0
    
    def get_detailed_info(self):
        """Retourne des informations détaillées sur la pièce"""
        return {
            "id": self.unique_id,
            "index": self.index,
            "color": self.color,
            "position_3d": self.position_3d.tolist(),
            "orientation": self.orientation,
            "current_face": self.get_current_face(),
            "is_solved": self.is_solved,
            # self.orientation[axis] = (self.orientation[axis] + angle) % 360
            "type": self.piece_type,
            "move_count": len(self.move_history),
            "connections": self.connections
        }
    
    def __str__(self):
        solved_status = "✓" if self.is_solved else "✗"
        return f"Piece({self.unique_id}, color={self.color}, solved={solved_status})"
    
    def __repr__(self):
        return self.__str__()

class Cube:
    def __init__(self):
        self.pieces = []
        self.face_names = ["U", "L", "F", "R", "B", "D"]  # Up, Left, Front, Right, Back, Down
        self.colors = ["W", "O", "G", "R", "B", "Y"]  # White, Orange, Green, Red, Blue, Yellow
        self.initialize_cube()
    
    def initialize_cube(self):
        """Initialise le cube avec toutes les pièces et leurs connexions"""
        # Créer 54 pièces (9 par face)
        for face_idx in range(6):
            color = self.colors[face_idx]
            for pos in range(9):
                global_index = face_idx * 9 + pos
                piece = Piece(global_index, color)
                self.pieces.append(piece)
        
        # Définir les connexions entre les faces adjacentes
        self.setup_connections()
    
    def setup_connections(self):
        """Définit toutes les connexions entre les pièces adjacentes"""
        for piece_index, connections in connections_map.items():
            for conn_index in connections:
                self.pieces[piece_index].add_connection(conn_index)
                # Ajouter la connexion bidirectionnelle
                if piece_index not in self.pieces[conn_index].connections:
                    self.pieces[conn_index].add_connection(piece_index)
    
    def get_face(self, face_name):
        """Retourne les 9 pièces d'une face donnée"""
        face_index = self.face_names.index(face_name)
        start_idx = face_index * 9
        return self.pieces[start_idx:start_idx + 9]
    
    def get_adjacent_faces(self, face_name):
        """Retourne les noms des faces adjacentes à une face donnée"""
        adjacent_faces_map = {
            "U": ["L", "F", "R", "B"],
            "R": ["U", "F", "D", "B"],
            "F": ["U", "R", "D", "L"],
            "L": ["U", "B", "D", "F"],
            "B": ["U", "L", "D", "R"],
            "D": ["L", "F", "R", "B"],
        }
        return adjacent_faces_map[face_name]

    def rotate_face_clockwise(self, face_name):
        """Rotation horaire d'une face"""
        face_pieces = self.get_face(face_name)

        # apply rotation to the face itself
        new = [0]*9
        for i in range(3):
            for j in range(3):
                new[3*j + (2 - i)] = face_pieces[3*i + j]

        # save new face after rotation
        start_idx = self.face_names.index(face_name) * 9
        self.pieces[start_idx:start_idx + 9] = new

        # Now rotate the adjacent edges
        looking_for = set([piece.index for piece in face_pieces])
        
        # Define which pieces to rotate for each face
        edge_mapping = {
            "U": [[9, 10, 11], [18, 19, 20], [27, 28, 29], [38, 37, 36]],  # L, F, R, B
            "D": [[17, 16, 15], [24, 25, 26], [33, 34, 35], [44, 43, 42]],  # L, F, R, B
            "F": [[6, 7, 8], [27, 30, 33], [47, 46, 45], [17, 14, 11]],     # U, R, D, L
            "B": [[2, 1, 0], [9, 12, 15], [51, 52, 53], [35, 32, 29]],      # U, L, D, R
            "L": [[0, 3, 6], [18, 21, 24], [45, 48, 51], [44, 41, 38]],     # U, F, D, B
            "R": [[8, 5, 2], [36, 39, 42], [53, 50, 47], [26, 23, 20]],     # U, B, D, F
        }
        
        edges = edge_mapping[face_name]
        
        # Save all colors from the edges
        all_colors = []
        for edge in edges:
            for piece_idx in edge:
                all_colors.append(self.pieces[piece_idx].color)
        
        # Rotate: each edge takes colors from the previous edge (shift by 3)
        num_pieces_per_edge = len(edges[0])
        for i, edge in enumerate(edges):
            prev_edge_idx = (i - 1) % len(edges)
            for j, piece_idx in enumerate(edge):
                color_idx = prev_edge_idx * num_pieces_per_edge + j
                self.pieces[piece_idx].color = all_colors[color_idx]

    def display(self):
        """Affiche le cube sous forme dépliée"""
        for face_idx, face_name in enumerate(self.face_names):
            print(f"Face {face_name}:")
            face_pieces = self.get_face(face_name)
            for i in range(3):
                row = face_pieces[i*3:(i+1)*3]
                print(" ".join([piece.color for piece in row]))
    
    def __str__(self):
        return f"Cube with {len(self.pieces)} pieces"

# Fonctions de mouvement utilisant la classe Cube
#################################### Front ####################################
def front(cube_obj):
    """Rotation F"""
    cube_obj.rotate_face_clockwise("F")
    print("F")

def front_reverse(cube_obj):
    """Rotation F'"""
    for _ in range(3):
        cube_obj.rotate_face_clockwise("F")
    print("F'")

def double_front(cube_obj):
    """Rotation F2"""
    for _ in range(2):
        cube_obj.rotate_face_clockwise("F")
    print("F2")

#################################### Back ####################################
def back(cube_obj):
    """Rotation B"""
    cube_obj.rotate_face_clockwise("B")
    print("B")

def back_reverse(cube_obj):
    """Rotation B'"""
    for _ in range(3):
        cube_obj.rotate_face_clockwise("B")
    print("B'")

def double_back(cube_obj):
    """Rotation B2"""
    for _ in range(2):
        cube_obj.rotate_face_clockwise("B")
    print("B2")

#################################### Up ####################################
def up(cube_obj):
    """Rotation U"""
    for _ in range(3):
        cube_obj.rotate_face_clockwise("U")
    print("U")

def up_reverse(cube_obj):
    """Rotation U'"""
    cube_obj.rotate_face_clockwise("U")
    print("U'")

def double_up(cube_obj):
    """Rotation U2"""
    for _ in range(2):
        cube_obj.rotate_face_clockwise("U")
    print("U2")

#################################### Down ####################################
def down(cube_obj):
    """Rotation D"""
    cube_obj.rotate_face_clockwise("D")
    print("D")

def down_reverse(cube_obj):
    """Rotation D'"""
    for _ in range(3):
        cube_obj.rotate_face_clockwise("D")
    print("D'")

def double_down(cube_obj):
    """Rotation D2"""
    for _ in range(2):
        cube_obj.rotate_face_clockwise("D")
    print("D2")

#################################### Right ##########################R
def right(cube_obj):
    cube_obj.rotate_face_clockwise("R")
    print("R")

def right_reverse(cube_obj):
    """Rotation R'"""
    for _ in range(3):
        cube_obj.rotate_face_clockwise("R")
    print("R'")

def double_right(cube_obj):
    """Rotation R2"""
    for _ in range(2):
        cube_obj.rotate_face_clockwise("R")
    print("R2")

#################################### Left ####################################
def left(cube_obj):
    """Rotation L"""
    cube_obj.rotate_face_clockwise("L")
    print("L")

def left_reverse(cube_obj):
    """Rotation L'"""
    for _ in range(3):
        cube_obj.rotate_face_clockwise("L")
    print("L'")

def double_left(cube_obj):
    """Rotation L2"""
    for _ in range(2):
        cube_obj.rotate_face_clockwise("L")
    print("L2")

if __name__ == "__main__":
    cube = Cube()
    # cube.display()
    up(cube)
    down(cube)
    right(cube)
    left(cube)
    front(cube)
    back(cube)
    cube.display()