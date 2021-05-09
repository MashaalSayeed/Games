import copy
import pygame

from pieces import *

# BASIC CONFIGURATIONS
SCREENX, SCREENY = 700, 500
FPS = 30

# For storage reference
PIECE_TYPE = {
    "PAWN": Pawn,
    "ROOK": Rook,
    "KNIGHT": Knight,
    "BISHOP": Bishop,
    "KING": King,
    "QUEEN": Queen
}


class Game:
    # 2 seperate lists for the board and their respective blocks (Block class)
    board = [[] for _ in range(8)]
    blocks = [[] for _ in range(8)]
    # Stores all valid moves for current piece
    moves = []
    # Current player color
    turn = 'WHITE'
    # Other boolean values
    running = True
    selected = None
    inCheck = False
    # Number of moves without capture / pawn movement (Tie)
    move50 = 0

    def __init__(self):
        pygame.init()

        # Basic pygame modules
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((SCREENX, SCREENY))

        # Sprite groups one for all pieces and one for all sprites
        self.all_sprites = pygame.sprite.Group()
        self.piece_sprites = pygame.sprite.Group()

        self.create_board()
        self.board_history = []
        self.run()

        pygame.quit()

    def copy_board(self, board):
        "Returs a copy of the 2d board"
        return [[c for c in r] for r in board]

    def create_board(self):
        "Create the board UI and place chess pieces on the board"
        for i in range(8):
            for j in range(8):
                self.blocks[i].append(Block(j, i, (i+j)%2 == 0))

        pieces = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        self.board = [
            [pieces[i](i, 0, 'BLACK') for i in range(8)],
            [Pawn(i, 1, 'BLACK') for i in range(8)],
            [None for _ in range(8)],
            [None for _ in range(8)],
            [None for _ in range(8)],
            [None for _ in range(8)],
            [Pawn(i, 6, 'WHITE') for i in range(8)],
            [pieces[i](i, 7, 'WHITE') for i in range(8)]
        ]

        self.piece_sprites.add(self.board[0:2], self.board[6:8])
        self.all_sprites.add(self.blocks, self.piece_sprites)

        # Store kings for both players, useful for checks and castling
        self.kings = {'WHITE': self.board[7][4], 'BLACK': self.board[0][4]}

    def select_piece(self):
        "Get the selected piece, unselect if already selected, get all valid moves"
        pos = pygame.mouse.get_pos()
        clicked_sprites = [s for s in self.piece_sprites if s.rect.collidepoint(pos)]

        if len(clicked_sprites) == 1 and clicked_sprites[0].color == self.turn:
            # unselect previously selected piece
            if self.selected:
                self.blocks[self.selected.y][self.selected.x].select()

            self.selected = clicked_sprites[0]
            moves = clicked_sprites[0].moves(self.board)
            # Check if castling is possible
            is_king = isinstance(self.selected, King)
            if is_king:
                moves += self.check_castle(self.board)

            self.moves = copy.deepcopy(moves)
            # validate every move
            for m in moves:
                boardcpy = self.copy_board(self.board)
                boardcpy[m[0]][m[1]] = self.selected
                boardcpy[self.selected.y][self.selected.x] = None

                if self.is_check(boardcpy, m[1], m[0], is_king=is_king):
                    self.moves.remove(m)

            self.blocks[self.selected.y][self.selected.x].select()

    def move_piece(self, piece, y, x):
        "Move a chess piece in the board"
        opiece = self.board[y][x]

        if isinstance(piece, Pawn) or opiece:
            self.move50 = 0

            # Kill whoever is in that place
            if opiece:
                opiece.kill()
        else:
            self.move50 += 1

        # To ensure en passant rule, we must remove all previous pawn double moves
        pawns = [p for p in self.piece_sprites if p.color == self.turn and isinstance(p, Pawn)]
        for pawn in pawns:
            pawn.double = False

        # Store original positions for future reference
        ox, oy = piece.x, piece.y
        # Change coordinates of the moving piece
        ep = piece.move(x, y, self.board)
        self.board[y][x] = piece
        # Original position of piece now empty
        self.board[oy][ox] = None

        self.blocks[oy][ox].select()
        piece.moved = True
        self.selected = None
        self.moves = []

        # Castling...
        if isinstance(piece, King) and abs(x - ox) == 2:
            rook = self.board[piece.y][7 if (x - ox) > 0 else 0]
            diff = 1 if rook.x == 0 else -1

            self.blocks[rook.y][rook.x].select()
            self.move_piece(rook, piece.y, x + diff)

        # Pawn Promotion...
        if isinstance(piece, Pawn) and y in [0, 7]:
            # Just gonna promote it to queen cuz... why not
            # First kill the original pawn
            piece.kill()
            # Create the queen and add it to sprite groups and board
            queen = Queen(x, y, self.turn)
            self.add_piece(queen)
            self.board[y][x] = queen

    def serialize(self, board):
        "Make it so the board can be easily stored"
        boardcpy = self.copy_board(board)
        for row in range(8):
            for col in range(8):
                if boardcpy[row][col]:
                    boardcpy[row][col] = boardcpy[row][col].serialize()

        return boardcpy

    def deserialize(self, board):
        "Extract data from serialized blocks"
        for row in range(8):
            for col in range(8):
                if board[row][col]:
                    pos, piece, color, moved, double = board[row][col]

                    p = PIECE_TYPE[piece](pos[1], pos[0], color)
                    p.moved = moved
                    p.double = double

                    board[row][col] = p
                    self.blocks[p.y][p.x].check(False)

                    if isinstance(p, King):
                        self.kings[color] = p
        return board

    def is_check(self, board, x=None, y=None, is_king=False):
        "Look for a check, return True if it is a checkmate"
        # Get all enemy pieces that do not occupy x,y (place we are going to put our piece)
        enemies = [e for e in self.piece_sprites if e.color != self.turn and e.x != x and e.y != y]
        king = self.kings[self.turn]

        for e in enemies:
            # Loop through all enemy moves and see if the king's position lies in it
            moves = e.moves(board)
            if not is_king and (king.y, king.x) in moves:
                return True
            if is_king and (y, x) in moves:
                return True
        return False

    def add_piece(self, sprite):
        "Add the sprite back to sprite groups"
        self.all_sprites.add(sprite)
        self.piece_sprites.add(sprite)

    def check_castle(self, board):
        "Check if castling is possible, return the possible moves"
        # Get the king and valid rooks
        king = self.kings[self.turn]
        rooks = [r for r in self.piece_sprites if r.color == self.turn and isinstance(r, Rook) and not r.moved]
        rook1 = [r for r in rooks if r.x == 0]
        rook2 = [r for r in rooks if r.x == 7]
        valid = []

        # 1. Both rook and king never moved
        # 2. King should not be in a check
        # 3. Space between rook and king must be empty
        if not rooks or king.moved or self.in_check:
            return []
        if rook1 and not (board[king.y][king.x-1] or board[king.y][king.x-2] or board[king.y][king.x-3]):
            valid.append((king.y, king.x-2))

        if rook2 and not (board[king.y][king.x+1] or board[king.y][king.x+2]):
            valid.append((king.y, king.x+2))

        return valid

    def is_mate(self):
        "Look for a checkmate, see if player has any other possible moves"
        mate = True
        pieces = [p for p in self.piece_sprites if p.color == self.turn]

        for p in pieces:
            # Once we have found it is not a mate break
            if not mate:
                break

            for my, mx in p.moves(self.board):
                # Simulate all posible moves and see if any are valid
                boardcpy = self.copy_board(self.board)
                boardcpy[my][mx] = p
                boardcpy[p.y][p.x] = None

                if not self.is_check(boardcpy, mx, my, is_king=isinstance(p, King)):
                    print('nope', p)
                    mate = False
                    break
        return mate

    def run(self):
        "Main game loop"
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_u and self.board_history:
                        [[p.kill() for p in r if p] for r in self.board]

                        undo_game = self.board_history.pop()
                        self.board = self.deserialize(undo_game["board"])
                        self.move50 = undo_game["move50"]
                        self.turn = undo_game["turn"]

                        [[self.add_piece(p) for p in r if p] for r in self.board]

                elif event.type == pygame.MOUSEBUTTONDOWN and not self.selected:
                    # If no piece is selected, select a piece
                    self.select_piece()

                elif event.type == pygame.MOUSEBUTTONDOWN and self.selected:
                    # else move the piece if the position is valid
                    # calculate square matrix coordinates of mouse
                    x, y = pygame.mouse.get_pos()
                    x = int((x - BOARD_RECT[0]) // BLOCK_SIZE[0])
                    y = int((y - BOARD_RECT[1]) // BLOCK_SIZE[1])

                    if (y, x) in self.moves:
                        self.board_history.append({
                            "board": self.serialize(self.board),
                            "turn": self.turn,
                            "move50": self.move50
                        })

                        king = self.kings[self.turn]
                        self.blocks[king.y][king.x].check(False)

                        # Move the piece and swap turns
                        self.move_piece(self.selected, y, x)

                        # assume the king is not in check (validating moves was done above)
                        king = self.kings[self.turn]
                        self.blocks[king.y][king.x].check(False)

                        self.turn = 'BLACK' if self.turn == 'WHITE' else 'WHITE'
                        self.in_check = self.is_check(self.board)

                        king = self.kings[self.turn]
                        self.blocks[king.y][king.x].check(self.in_check)

                        mate = self.is_mate()
                        # Mate: No move possible
                        if mate:
                            self.running = False
                            if self.inCheck:
                                print("Checkmate:", self.turn, "has lost")
                            else:
                                print("Stalemate: It's a tie!")

                        if self.move50 >= 50:
                            self.running = False
                            print("Tie: 50 moves without a capture or a pawn movement")

                    else:
                        self.select_piece()

            # Draw everything
            self.piece_sprites.update()
            self.all_sprites.draw(self.screen)

            # Show all possible move sets as circle dots
            for my, mx in self.moves:
                cx = int(BOARD_RECT[0] + BLOCK_SIZE[0] * (mx + 0.5))
                cy = int(BOARD_RECT[1] + BLOCK_SIZE[1] * (my + 0.5))

                pygame.draw.circle(self.screen, GREY, (cx, cy), 10)

            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    game = Game()
