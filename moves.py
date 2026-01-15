from cube import Cube

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

#################################### Right ####################################
def right(cube_obj):
    """Rotation R"""
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