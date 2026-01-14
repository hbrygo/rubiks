import numpy as np
from connection import connections_map

class Piece:
    def __init__(self, index, color, connections=None, piece_type=None, position_3d=None):
        self.index = index
        self.color = color
        self.connections = connections or []  # Liste des index des faces liées
        self.piece_type = piece_type  # "corner", "edge", "center"
        self.original_index = index  # Pour pouvoir reset le cube
        
        # ID unique pour le debugging
        self.unique_id = f"{self.piece_type}_{index}" if piece_type else f"piece_{index}"
    
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

    def reset_to_original(self):
        """Remet la pièce dans son état original"""
        self.position_3d = self.original_position_3d.copy()
        self.orientation = self.original_orientation.copy()
    
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
            "type": self.piece_type,
            "connections": self.connections
        }
    
    def __str__(self):
        return f"Piece({self.unique_id}, color={self.color})"
    
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