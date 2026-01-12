# cube = [
#     "W","W","W","W","W","W","W","W","W",  # U
#     "R","R","R","R","R","R","R","R","R",  # R
#     "G","G","G","G","G","G","G","G","G",  # F
#     "Y","Y","Y","Y","Y","Y","Y","Y","Y",  # D
#     "O","O","O","O","O","O","O","O","O",  # L
#     "B","B","B","B","B","B","B","B","B",  # B
# ]

# transpose une matrice pour tourner une face puis inverser ligne ou colonne en fonction de la rotation
# theorie des groupes

# rotate front face: F
def front():
    tmp = cube
    tmp[0] = cube[6]
    tmp[1] = cube[3]
    tmp[2] = cube[0]
    tmp[3] = cube[7]
    tmp[4] = cube[4]
    tmp[5] = cube[1]
    tmp[6] = cube[8]
    tmp[7] = cube[5]
    tmp[8] = cube[2]
    cube = tmp
    print("F")

# reverse rotate front face: F'
def front_reverse():
    tmp = cube
    tmp[0] = cube[2]
    tmp[1] = cube[5]
    tmp[2] = cube[8]
    tmp[3] = cube[1]
    tmp[4] = cube[4]
    tmp[5] = cube[7]
    tmp[6] = cube[0]
    tmp[7] = cube[3]
    tmp[8] = cube[6]
    cube = tmp
    print("F'")

# double rotate front face: F2
def double_front():
    tmp = cube
    tmp[0] = cube[8]
    tmp[1] = cube[7]
    tmp[2] = cube[6]
    tmp[3] = cube[5]
    tmp[4] = cube[4]
    tmp[5] = cube[3]
    tmp[6] = cube[2]
    tmp[7] = cube[1]
    tmp[8] = cube[0]
    cube = tmp
    print("F2")
