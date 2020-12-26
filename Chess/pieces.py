import pygame


# COLORS REQUIRED (RGB)
GREEN = (118,150,86)
WHITE = (255, 255, 255)
GREY = (211, 211, 211)
YELLOW = (253, 253, 150)
RED = (240, 72, 72)

# BOARD CONFIGURATIONS
BOARD_RECT = 0, 0, 500, 500
BLOCK_SIZE = BOARD_RECT[2] / 8, BOARD_RECT[3] / 8
PIECE_SIZE = 40, 40

# IMAGE LOCATIONS
IMAGES = {
    "WHITE": {
        "PAWN": "images/WhitePawn.png",
        "ROOK": "images/WhiteRook.png",
        "KNIGHT": "images/WhiteKnight.png",
        "BISHOP": "images/WhiteBishop.png",
        "KING": "images/WhiteKing.png",
        "QUEEN": "images/WhiteQueen.png"
        },
    "BLACK": {
        "PAWN": "images/BlackPawn.png",
        "ROOK": "images/BlackRook.png",
        "KNIGHT": "images/BlackKnight.png",
        "BISHOP": "images/BlackBishop.png",
        "KING": "images/BlackKing.png",
        "QUEEN": "images/BlackQueen.png"
        }
    }


# Class for a block, usually handles all background changes when selected
class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()

        # Create a rectangle of required size and color
        self.image = pygame.Surface(BLOCK_SIZE)
        self.color = WHITE if color else GREEN
        self.image.fill(self.color)

        self.rect = self.image.get_rect()
        self.rect.x = BOARD_RECT[0] + BLOCK_SIZE[0] * x
        self.rect.y = BOARD_RECT[1] + BLOCK_SIZE[1] * y

        self.selected = False
        self.is_check = False

    def select(self):
        # Change color to yellow when selected and change back to original when unselected
        if not self.selected:
            self.image.fill(YELLOW)
        elif self.is_check:
            self.image.fill(RED)
        else:
            self.image.fill(self.color)

        self.selected = not self.selected

    def check(self, isCheck):
        self.image.fill(RED if isCheck else self.color)
        self.is_check = isCheck


# Base class for all pieces        
class Piece(pygame.sprite.Sprite): 
    def __init__(self, x, y, color, piece):
        super().__init__()

        # x, y coordinates of piece in square matrix
        self.x = x
        self.y = y
        
        # color of the piece, will also determine the team it is in
        self.color = color
        self.piece = piece

        # Load the image and resize it
        self.img = pygame.image.load(IMAGES[color][piece])
        self.image = pygame.transform.scale(self.img, PIECE_SIZE)

        self.rect = self.image.get_rect()
        # Used for Castling
        self.moved = False
        # Used for En Passant
        self.double = False

    def move(self, x, y, board):
        # update the coordinates of piece in square matrix
        self.x = x
        self.y = y

    def serialize(self):
        return ((self.y, self.x), self.piece, self.color, self.moved, self.double)

    def update(self):
        # update position of image in the screen
        self.rect.center = BOARD_RECT[0] + BLOCK_SIZE[0] * (self.x + 0.5), BOARD_RECT[1] + BLOCK_SIZE[1] * (self.y + 0.5)

    def check_valid(self, board, x, y):
        # Checks whether the move position is valid (not out of board and not occupied by same team pieces)
        return 0 <= x < 8 and 0 <= y < 8 and (not board[y][x] or board[y][x].color != self.color)
            
    def gen_moves(self, board, lst):
        # Get all valid moves based on incremented directions (diagonal, vertical, horizontal)
        valid = []
        
        for ix, iy in lst:
            curx, cury = self.x, self.y
            
            while True:
                curx, cury = curx + ix, cury + iy
                
                if self.check_valid(board, curx, cury):
                    valid.append((cury, curx))
                    
                    if board[cury][curx]:
                        break
                else:
                    break
        return valid

    def diagonal_moves(self, board):
        # Get all possible diagonal moves
        lst = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
        return self.gen_moves(board, lst)
        
    def linear_moves(self, board):
        # Get all horizontal and vertical moves
        lst = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        return self.gen_moves(board, lst)         


class Pawn(Piece):
    # Reference for increment values of 2 colors
    rec = {'WHITE': -1, 'BLACK': 1}
    def __init__(self, x, y, color):
        super().__init__(x, y, color, 'PAWN')

    def moves(self, board):
        valid = []
        nposy = self.y + self.rec[self.color]
        
        if 0 <= nposy <= 7:
            # Diagonal attack
            if 0 <= self.x+1 <= 7 and board[nposy][self.x+1] and board[nposy][self.x+1].color != self.color:
                valid.append((nposy, self.x+1))
                
            if 0 <= self.x-1 <= 7 and board[nposy][self.x-1] and board[nposy][self.x-1].color != self.color:
                valid.append((nposy, self.x-1))

        # Forward Movement
        if 0 <= nposy <= 7 and board[nposy][self.x] == None:
            valid.append((nposy, self.x))
                
            # Double Forward
            if (self.color == 'WHITE' and self.y == 6) or (self.color == 'BLACK' and self.y == 1):
                nposy += self.rec[self.color]

                if board[nposy][self.x] == None:
                    valid.append((nposy, self.x))
        
        # En passant rule
        # 1. Both pawns must be in the same row and adjacent to each other
        # 2. Victim pawn has moved 2 spaces in the previous move
        if self.x > 0:
            piece = board[self.y][self.x-1]
            if type(piece) == Pawn and piece.color != self.color and piece.double:
                valid.append((self.y + self.rec[self.color], self.x-1))
        
        if self.x < 7:    
            piece = board[self.y][self.x+1]
            if type(piece) == Pawn and piece.color != self.color and piece.double:
                valid.append((self.y + self.rec[self.color], self.x+1))

        return valid
    
    def move(self, x, y, board):
        # Moved 2 spaces
        if abs(self.y-y) == 2:
            self.double = True

        # If En Passant, Kill the other pawn
        piece = board[y - self.rec[self.color]][x]
        if type(piece) == Pawn and piece.color != self.color and piece.double:
            board[piece.y][piece.x] = None
            piece.kill()
        self.x, self.y = x, y

        return piece
            

class Rook(Piece):
    def __init__(self, x, y, color):
        super().__init__(x, y, color, 'ROOK')

    def moves(self, board):
        return self.linear_moves(board)


class Knight(Piece):
    def __init__(self, x, y, color):
        super().__init__(x, y, color, 'KNIGHT')

    def moves(self, board):
        # Generates max 8 moves based on increment values
        lst = [(1, 2), (2, 1), (-1, 2), (2, -1), (-1, -2), (-2, -1), (-2, 1), (1, -2)]
        valid = []

        for ix, iy in lst:
            nx, ny = self.x + ix, self.y + iy
            
            if self.check_valid(board, nx, ny):
                valid.append((ny, nx))

        return valid                    


class Bishop(Piece):
    def __init__(self, x, y, color):
        super().__init__(x, y, color, 'BISHOP')

    def moves(self, board):
        return self.diagonal_moves(board)


class King(Piece):
    def __init__(self, x, y, color):
        super().__init__(x, y, color, 'KING')

    def moves(self, board):
        # Generates max 8 moves based on increment values (Similar to horse)
        lst = [(1,1), (0,1), (1,0), (-1,-1), (0,-1), (-1,0), (-1,1), (1,-1)]
        valid = []

        for ix, iy in lst:
            nx, ny = self.x + ix, self.y + iy

            if self.check_valid(board, nx, ny):
                valid.append((ny, nx))
                
        return valid


class Queen(Piece):
    def __init__(self, x, y, color):
        super().__init__(x, y, color, 'QUEEN')

    def moves(self, board):
        return self.diagonal_moves(board) + self.linear_moves(board)

