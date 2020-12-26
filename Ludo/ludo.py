import pygame
import random
import numpy

from pygame_util import Button, Label, Frame


"General Configuration"
SCREENX = 750
SCREENY = 600
FPS = 30

TILEX, TILEY = 40, 40
BOARD_SIZE = 600, 600
DICE_SIZE = 120, 120
PIECE_RADIUS = 10

DICE_POS = 675, 70

"Colors"
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


class Piece(pygame.sprite.Sprite):
    "Piece class, 4 of each color"
    moved = False
    moves = 0
    tile = None
    
    def __init__(self, x, y, color):
        super().__init__()

        # Create a circle with a black border
        self.image = pygame.Surface((PIECE_RADIUS*2, PIECE_RADIUS*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLACK, (PIECE_RADIUS, PIECE_RADIUS), PIECE_RADIUS)
        pygame.draw.circle(self.image, color, (PIECE_RADIUS, PIECE_RADIUS), PIECE_RADIUS - 2)
        
        self.rect = self.image.get_rect()
        
        # set the initial spawn point and color
        self.rect.center = x, y
        self.spawn_pos = x, y

        self.font = pygame.font.SysFont("Arial Black", 15, bold=True)
        self.color = color

    def can_move(self, mag):
        "Check if the piece can move any further"
        return (mag == 6 and not self.moved) or (self.moved and (self.moves + mag < 57))

    def move(self, board, mag):
        "Moves the piece"
        for m in range(1, mag+1):
            self.moves += 1

            # if piece has moved 51 or more times, then put it in the colored path
            if self.moves >= 51:
                new_tile = board.homePath[self.color][self.moves - 51]
            else:
                next_p = 24 + (self.tile.position + m - 24) % 52
                new_tile = [t for t in board.tiles if t.position == next_p][0]

        # Place the piece on the new tile and refresh the old tile 
        kills = new_tile.place(board, self)
        self.tile.refresh(board)
        
        self.tile = new_tile
        return self.moves == 56 or kills > 0 

    def start(self, board):
        "Determine initial starting tile"
        spawn = [t for t in board.tiles if t.spawn and t.color == self.color][0]
        self.tile = spawn
        
        spawn.place(board, self)
        self.moved = True

    def spawn(self):
        "Piece got killed - back to spawn "
        self.rect.center = self.spawn_pos
        self.redraw()
        self.moved = False
        self.moves = 0

    def text(self, num):
        "Draw text on the tile (in case of stacking)"
        self.redraw()
        if num < 2: return
        
        textSurf = self.font.render(str(num), 1, BLACK)
        self.image.blit(textSurf, [4, -1])

    def redraw(self):
        "Draws the circle again - (removes the previous text)"
        pygame.draw.circle(self.image, BLACK, (PIECE_RADIUS, PIECE_RADIUS), PIECE_RADIUS)
        pygame.draw.circle(self.image, self.color, (PIECE_RADIUS, PIECE_RADIUS), PIECE_RADIUS - 2)
        

class Dice(pygame.sprite.Sprite):
    "Dice class mainly for GUI purpose"
    current = 1
    rolling = -1
    finish = turn = None
    
    def __init__(self, turn):
        super().__init__()

        self.images = [pygame.transform.scale(pygame.image.load(f"images/dice{i}.png"), DICE_SIZE) for i in range(1, 7)]

        self.turn = turn
        self.draw(self.images[0], turn)
        self.rect = self.image.get_rect()
        self.rect.center = DICE_POS

    def roll(self, turn, finish=None):
        "Selects a random number from 1-6 and changes the image"
        self.current = random.randint(1, 6)
        self.turn = turn
        self.rolling = 0
        self.finish = finish

        return self.current

    def update(self):
        "Handle animation logic here"
        if -1 < self.rolling < 36:
            self.draw(self.images[(self.rolling//4)%6], self.turn)
            self.rolling += 1
        elif self.rolling == 36:
            self.rolling = -1
            self.change_bg(self.turn)
        elif self.rolling == -1 and self.finish:
            self.finish()
            self.finish = None

    def change_bg(self, color):
        self.draw(self.images[self.current - 1], color)

    def draw(self, image, bgcolor):
        self.image = pygame.Surface(DICE_SIZE)
        self.image.fill(bgcolor)

        self.image.blit(image, (0,0))


class Tile(pygame.sprite.Sprite):
    "Tile class that pieces land on, handles GUI and piece placing logic"
    spawn = False
    
    def __init__(self, position, x, y, color, **kwargs):
        super().__init__()

        self.position = position
        self.last = kwargs.get('last')
        self.double = kwargs.get('double')

        self.spawn = kwargs.get('spawn')
        self.safe = kwargs.get('safe')
        self.home = kwargs.get('home')

        self.draw(color)
        self.rect = self.image.get_rect()
        self.rect.center = x, y

    def draw(self, color):
        "Draws the image based on type of tile (home, spawn, safe)"
        self.image = pygame.Surface((TILEX, TILEY))
        self.image.fill(BLACK if not self.last else color)

        self.color = color
        color = self.color if self.color == WHITE else [c if c == 0 else c-25 for c in self.color]
        self.fgcolor = pygame.Surface((TILEX-1, TILEY-1))
        self.fgcolor.fill(color)

        self.image.blit(self.fgcolor, (1, 1))
        if self.safe:
            self.image.blit(pygame.image.load('images/star.png'), (0,0))

    def refresh(self, board):
        self.position_piece(board, self.find_pieces(board))
        
    def place(self, board, player):
        "Places a piece on a tile, killing any enemy pieces on it"
        players = self.find_pieces(board)
        kills = 0
        if not self.safe and not self.spawn:
            kills = len([p.spawn() for p in players if p.color != player.color])
            players = self.find_pieces(board)
            
        players.append(player)
        self.position_piece(board, players)
        return kills

    def position_piece(self, board, players):
        "In case of more than 1 piece on same tile, position all pieces and indicate number of stacked pieces"
        colors = [[p for p in players if p.color == c] for c in board.colors]
        colors = [c for c in colors if c] # Remove empty lists
        positions = [(-1, -1), (1, 1), (1, -1), (-1, 1)]
        num = len(colors)

        if num == 1:
            for p in colors[0]:
                p.rect.center = self.rect.center
                p.text(len(colors[0]))
        
        else:
            for i, color in enumerate(colors):
                for p in color:
                    p.rect.center = numpy.add(self.rect.center, numpy.multiply(positions[i], (TILEX//4, TILEY//4)))
                    p.text(len(color))

    def find_pieces(self, board):
        "Get all pieces placed on the tile"
        return pygame.sprite.spritecollide(self, board.pieces, False)


class AIPlayer:
    "AI to find best moves ..."
    def __init__(self, game, color):
        self.game = game
        self.color = color

        self.board = game.board
        self.pieces = [p for p in game.board.pieces if p.color == self.color]
        self.enemies = [p for p in game.board.pieces if p.color != self.color]

    def find_best_move(self, mag):
        pieces = [p for p in self.pieces if p.can_move(mag)]
        if len(pieces) == 0: return
        
        for p in pieces:
            if p.moves + mag == 56:
                return p

        enemy_tiles = [(24 + (e.tile.position - 24) % 52) for e in self.enemies if e.tile]
        for p in pieces:
            if p.tile and (24 + (p.tile.position + mag - 24) % 52) in enemy_tiles:
                return p

        if mag == 6:
            for p in pieces:
                if not p.moved:
                    return p

        order = sorted(pieces, key=lambda p: p.moves, reverse=True)
        for p in order:
            if (p.tile.position + mag - 27) % 13 == 0:
                return p

        for p in order:
            if not p.tile.safe:
                return p

        return order[0]


class Board:
    center = numpy.divide(BOARD_SIZE, 2)
    colors = [GREEN, YELLOW, BLUE, RED]
    path = []
    corners = [(0, 0, RED),
               (BOARD_SIZE[0] - 6 * TILEX, 0, GREEN),
               (BOARD_SIZE[0] - 6 * TILEX, BOARD_SIZE[1] - 6 * TILEY, YELLOW),
               (0, BOARD_SIZE[1] - 6 * TILEY, BLUE)]
    
    def __init__(self, game):
        self.game = game
        self.homePath = {k: [] for k in self.colors}
        
        self.tiles = pygame.sprite.Group()
        self.pieces = pygame.sprite.Group()
        
        self.create_tiles()
        self.tiles.add(self.path)

    def create_tiles(self):
        "Create tiles with their respective types and colors"
        x, y =  6.5 * TILEX, 5.5 * TILEY
        direction = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        position = d = 0

        # Create home path tiles
        for i in range(4):
            for j in range(6):
                hx, hy = numpy.add(self.center, numpy.multiply(direction[i], (TILEX, TILEY)) * (1+j))

                tile = Tile(position, hx, hy, self.colors[i], home=True, last=(j==5))
                self.homePath[self.colors[i]].insert(0, tile)
                self.tiles.add(tile)
                
                position += 1

        # Create other regular tiles
        for i in range(4):
            for j in range(13):
                if j < 3 or 3 < j < 6 or j == 7 or 8 < j:
                    self.path.append(Tile(position, x, y, WHITE))
                elif j == 3:
                    self.path.append(Tile(position, x, y, WHITE, safe=True))
                elif j == 6:
                    self.path.append(Tile(position, x, y, WHITE, double=True))
                else:
                    self.path.append(Tile(position, x, y, self.colors[i], spawn=True))

                if j in [5,7]: d = (d+1)%4

                x += direction[d][0] * TILEX
                y += direction[d][1] * TILEY
                position += 1

            d -= 1
            x += direction[d][0] * TILEX
            y += direction[d][1] * TILEY

    def create_pieces(self):
        "Create pieces based on the players playing"
        for x, y, color in self.corners:
            for ix, iy in [(1, 1), (1, 2), (2, 1), (2, 2)]:
                if color in self.game.players:
                    self.pieces.add(Piece(x + (2*TILEX) * ix, y + (2*TILEY) * iy, color))
            
    def draw(self, screen):
        "Draws the big boxes (base) and triangles on the board"
        for i, (x, y, color) in enumerate(self.corners):
            # Draw Box
            pygame.draw.rect(screen, color, ((x, y),(6 * TILEX, 6 * TILEY)))
            pygame.draw.rect(screen, WHITE, ((x + TILEX, y + TILEY), (4 * TILEX, 4 * TILEY)))

            # Draw Triangle
            p1 = self.get_triangle_pos(i)
            p2 = self.get_triangle_pos((i+1)%4)
            pygame.draw.polygon(screen, color, [self.center, p1, p2])
            
    def get_triangle_pos(self, index):
        triangles = [(1, -1), (1, 1), (-1, 1), (-1, -1)]
        
        return numpy.subtract(self.center, numpy.multiply(triangles[index], (TILEX, TILEY)) * 1.5)
        

class Game(object):
    "Main game class, handles player selection GUI as well as handling user inputs (dice, piece)"
    players = [RED, GREEN, YELLOW, BLUE]
    AI = humans = []
    roll = True
    winner = None
    next_ai_roll = next_ai_move = float('inf')
    turn = 0

    def __init__(self):
        super().__init__()
        pygame.init()

        self.screen = pygame.display.set_mode((SCREENX, SCREENY))
        self.clock = pygame.time.Clock()

        self.dice = Dice(self.players[self.turn])
        self.board = Board(self)
        
        self.all_sprites = pygame.sprite.Group(self.board.tiles, self.dice)

    def roll_dice(self):
        "Rolls the dice, skipping turns if no valid move is possible"
        self.dice.roll(self.players[self.turn], finish=self.ai_move)
        self.roll = False

    def ai_move(self):
        pieces = [s for s in self.board.pieces if s.color == self.players[self.turn]]
        if not any(p for p in pieces if p.can_move(self.dice.current)):
            self.change_turn()
            self.roll = True
        elif self.players[self.turn] not in self.humans:
            self.next_ai_move = pygame.time.get_ticks() + 1000

    def move_piece(self, piece):
        "Moves pieces and checks for wins"
        double = False

        if not piece.moved and self.dice.current == 6:
            piece.start(self.board)
        elif piece.can_move(self.dice.current):
            double = piece.move(self.board, self.dice.current)
            
            if self.check_win(self.players[self.turn]):
                self.winner = self.turn
                self.win_surface = pygame.Surface((SCREENX, SCREENY))
                self.win_surface.set_alpha(100)
                self.win_surface.fill((200, 200, 200))
                
                self.win_label = Label((0,0,200, 70), text=f'Player {self.winner + 1} WINS!', bgcolor=(0, 200, 0), border=5)
        else:
            return

        self.roll = True
        if self.dice.current != 6 and not double:
            self.change_turn()
        else:
            if self.players[self.turn] not in self.humans:
                self.next_ai_roll = pygame.time.get_ticks() + 1000

    def change_turn(self):
        self.turn = (self.turn + 1) % len(self.players)
        self.dice.change_bg(self.turn)

        if self.players[self.turn] not in self.humans:
            self.next_ai_roll = pygame.time.get_ticks() + 1000

    def check_win(self, color):
        return all(s.moves == 56 for s in self.board.pieces if s.color == color)

    def start(self):
        "Handle player selection GUI"
        fonts = [pygame.font.SysFont('Arial', x, bold=True) for x in [80,60,30,20]]
        
        label = Label((SCREENX/2-150,50,300,100), text="LUDO", font=fonts[0])
        self.start_btn = Button((SCREENX/2-150, 500, 300, 70), text="START", font=fonts[1], bgcolor=GREEN,
                                hovercolor=(100,255,100), border=5, command=self.check_and_run)

        self.surfaces = [] # (Frame, button) list for each color (player)
        for i, color in enumerate([RED, GREEN, YELLOW, BLUE]):
            posx, posy = 170*(i+0.25), 220
            surf = Frame((posx, posy, 150, 200), bgcolor=color, border=2)
            player_label = Label((2,2,150,60), text=f'Player {i+1}', bgcolor=color, fgcolor=BLACK, font=fonts[2])
            
            text_btn = Button((posx+12,posy+70,130,100), text='HUMAN', fgcolor=BLACK, bgcolor=color, font=fonts[3], command=self.change_text)

            surf.surface.blit(player_label.surface, (2,2))
            self.surfaces.append((surf, text_btn))

        # Blit Gui
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return pygame.quit()

            self.screen.fill((0, 0, 128))
            pygame.draw.rect(self.screen, (50,50,200), (25,25,SCREENX-50,160)) 
            label.draw(self.screen)
            self.start_btn.draw(self.screen)
            
            for (surf, btn) in self.surfaces:
                surf.draw(self.screen)
                btn.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(FPS)

    def change_text(self, button):
        "Handles button clicks"
        if button.text == 'HUMAN': text = 'COMPUTER'
        elif button.text == 'COMPUTER': text = 'Not Playing'
        else: text = 'HUMAN'
        
        pygame.time.wait(200)
        button.config(text=text)

        if len([b for (_, b) in self.surfaces if b.text != 'Not Playing']) > 1:
            self.start_btn.config(disabled=False)
        else:
            self.start_btn.config(disabled=True)

    def check_and_run(self, button):
        "Initialises players playing and starts the game"
        buttons = [b for (_, b) in self.surfaces if b.text != 'Not Playing']
        self.players = [p for p in self.players if p in [b.bgcolor for b in buttons]]
        self.board.create_pieces()
        self.all_sprites.add(self.board.pieces)
        
        self.AI = [AIPlayer(self, b.bgcolor) for b in buttons if b.text == 'COMPUTER']
        self.humans = [b.bgcolor for b in buttons if b.text == 'HUMAN']
        
        self.run()

    def run(self):
        "Main Game loop"
        if self.players[self.turn] not in self.humans:
            self.next_ai_roll = pygame.time.get_ticks() + 1000
            
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return pygame.quit()
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()

                    if self.roll and self.dice.rect.collidepoint(pos) and self.winner == None:
                        self.roll_dice()
                    elif not self.roll and self.winner == None:
                        clicked_sprites = [s for s in self.board.pieces if s.rect.collidepoint(pos)]
                        
                        if len(clicked_sprites) and clicked_sprites[0].color == self.players[self.turn]:
                            self.move_piece(clicked_sprites[0])

            self.screen.fill((0,0,128))
            self.board.draw(self.screen)

            self.all_sprites.draw(self.screen)
            if self.winner != None:
                self.screen.blit(self.win_surface, (0,0))
                self.win_label.draw(self.screen, center=True)
            else:
                self.all_sprites.update()

            now = pygame.time.get_ticks()
            if self.roll and self.winner == None and now >= self.next_ai_roll:
                self.next_ai_roll = float('inf')
                self.roll_dice()
            elif now >= self.next_ai_move:
                self.next_ai_move = float('inf')
                AI = [a for a in self.AI if a.color == self.players[self.turn]][0]
                piece = AI.find_best_move(self.dice.current)
                self.move_piece(piece) 
            
            pygame.display.flip()
            self.clock.tick(FPS)       


if __name__ == "__main__":
    Game().start()


