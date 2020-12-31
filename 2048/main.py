import sys
sys.path.append('../')

import random
import copy

import pygame

from Ludo.pygame_util import Label, Button, Frame


BGCOLOR = (250, 248, 239)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SCREENX = 500
SCREENY = 600
FPS = 30

# size and positioning of the block
block_size = (95, 95)
spaces = [5, 50, 5]
DIST_Y = 150

# 2 = 90%, 4 = 10%
vals = [2] * 9 + [4]

colors = {
    '0': (129, 120, 111),
    '2': (238, 228, 218),
    '4': (237, 224, 190),
    '8': (242, 177, 121),
    '16': (245, 150, 99),
    '32': (246, 125, 95),
    '64': (246, 93, 59),
    '128': (237, 206, 114),
    '256': (237, 204, 97),
    '512': (237, 200, 80),
    '1024': (237, 197, 63),
    '2048': (237, 194, 46)
}


class Block(pygame.sprite.Sprite):
    text = ' '
    fontColor = color = BLACK

    def __init__(self, game, x, y, val):
        super().__init__()

        self.game = game
        self.val = val
        self.font = pygame.font.SysFont("Clear Sans", 35)
        self.image = pygame.Surface(block_size)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.textSurf = self.font.render(self.text, 1, self.fontColor)

    def update(self):
        """ update the sprite and its text """
        curVal = self.game.board[self.val[0]][self.val[1]]
        self.text = str(curVal or ' ')

        if str(curVal) in colors:
            self.color = colors[str(curVal)]
            self.fontColor = BLACK
        else:
            self.color = BLACK
            self.fontColor = WHITE

        self.image.fill(self.color)
        self.textSurf = self.font.render(self.text, 1, self.fontColor)

        W = self.textSurf.get_width()
        H = self.textSurf.get_height()

        self.image.blit(self.textSurf, [block_size[0] / 2 - W / 2, block_size[1] / 2 - H / 2])


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREENX, SCREENY), 0, 32)
        self.clock = pygame.time.Clock()
        self.block_list = pygame.sprite.Group()

        self.create_tiles(DIST_Y)
        self.board = None
        self.undos = None
        self.restarting = False

        self.create_widgets()

    def create_widgets(self):
        self.fonts = fonts = [pygame.font.SysFont('Arial', size, True) for size in [70, 40, 25]]

        self.lose_label = Label((0,0,200,100), font=fonts[1], text='You Lose', fgcolor=BLACK, bgcolor=(192,100,100))
        self.restartUI = [
            Frame((45, 145, 405, 405), bgcolor=BLACK, transparency=100),
            Frame((150,300,200,100), bgcolor=(192,100,100)),
            Label((150,300,200,50), font=fonts[1], text='Restart?', fgcolor=BLACK, bgcolor=(192,100,100)),
            Button((160,360,75,35), font=fonts[1], text='Yes', fgcolor=BLACK, bgcolor=(100,100,180), command=self.restart),
            Button((265,360,75,35), font=fonts[1], text='No', fgcolor=BLACK, bgcolor=(100,100,180), command=lambda x: self.set_restart(False))
        ]
        
        self.mainUI = [
            Button((390,95,50,50), image=pygame.image.load('undo.png'), bgcolor=BGCOLOR, command=self.undo),
            Button(((330,95,50,50)), image=pygame.image.load('restart.png'), bgcolor=BGCOLOR, command=lambda x: self.set_restart(True)),
            Label((25,50,200,80), font=fonts[0], text="2048", bgcolor=BGCOLOR, fgcolor=BLACK)
        ]


    def state(self):
        """0 for not finished, -1 for lose """
        # Check for empty spaces
        if any(self.board[i][j] == 0 for j in range(4) for i in range(4)):
            return 0

        # Check if 2 similar numbers are in consecutive cells
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == self.board[i+1][j] or self.board[i][j] == self.board[i][j+1]:
                    return 0
        
        return -1
    
    def generate_board(self):
        self.board = [[0 for _ in range(4)] for _ in range(4)]
        self.drop(self.board, 2)

        self.undos = [copy.deepcopy(self.board)]
        self.score = self.last_score = 0

    def create_tiles(self, top):
        for i in range(4):
            for j in range(4):
                block = Block(self, j * (block_size[0] + spaces[0]) + spaces[1], top, (i, j))
                self.block_list.add(block)

            top += block_size[1] + spaces[2]

    def getEmpty(self, board):
        """ Empty spaces """
        return [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    
    def removeSpaces(self, board):
        """ remove the spaces between tiles """
        print(board)
        for x in range(3):
            for i in range(4):
                for j in range(x, 4):
                    if board[i][x] == 0:
                        board[i][x] = board[i][j]
                        board[i][j] = 0
        return board
    
    def rot90(self, board, direction):
        if direction < 0:
            direction += 4
        for _ in range(direction):
            board = [list(row) for row in zip(*board)][::-1]
        return board

    def drop(self, board, n):
        """ Random drops """
        for i in range(n):
            row, col = random.choice(self.getEmpty(board))
            board[row][col] = random.choice(vals)
        return board

    def move(self, direction):
        """ Move in Left, Right, Up or Down """
        initial_score = self.score
        board1 = copy.deepcopy(self.board)
        board2 = self.rot90(board1, direction)
        board2 = self.removeSpaces(board2)

        # merge adjacent tiles
        for i in range(4):
            for j in range(1, 4):
                if board2[i][j] == board2[i][j - 1]:
                    board2[i][j - 1] *= 2
                    self.score += board2[i][j - 1]
                    board2[i][j] = 0

        board2 = self.removeSpaces(board2)
        board1 = self.rot90(board2, -direction)

        if self.board != board1:
            self.undos.append(self.board)
            board1 = self.drop(board1, 1)

        if initial_score != self.score:
            self.last_score = initial_score

        return board1

    def undo(self, _=None):
        try:
            self.board = self.undos.pop()
            self.score = self.last_score
        except:
            pass

    def set_restart(self, value):
        self.restarting = value
    
    def restart(self, _=None):
        self.running = False
        self.run()

    def run(self):
        self.generate_board()
        self.running = True
        self.restarting = False
        while self.running:
            self.screen.fill(BGCOLOR)
            pygame.draw.rect(self.screen, (119, 110, 101), (45, 145, 405, 405))
            self.block_list.draw(self.screen)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:# and not restarting:
                    "game movement based on keys pressed "
                    
                    if event.key == pygame.K_w: self.board = self.move(1)
                    elif event.key == pygame.K_a: self.board = self.move(0)
                    elif event.key == pygame.K_s: self.board = self.move(3)
                    elif event.key == pygame.K_d: self.board = self.move(2)
                    elif event.key == pygame.K_u and len(self.undos):
                        self.undo()

            x = self.state()
            self.block_list.update()
            if x == -1:
                self.lose_label.draw(screen, centre=True)
                self.restarting = True

            if self.restarting:
                [u.draw(self.screen) for u in self.restartUI]

            Label((275,50,180,50), font=self.fonts[2], text=f"SCORE: {self.score}", bgcolor=BGCOLOR, fgcolor=BLACK).draw(self.screen)
            [u.draw(self.screen) for u in self.mainUI]

            pygame.display.flip()
            self.clock.tick(FPS)



if __name__ == "__main__":
    pygame.init()
    Game().run()
