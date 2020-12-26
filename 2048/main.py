import sys
sys.path.append('../')

import random

import numpy
import pandas as pd
import pygame

from Utils.pygame_util import Label, Button, Frame


BOARD = numpy.zeros((4, 4), dtype='int')
undos = [BOARD.copy()]
last_score = score = depth = 0
restarting = False

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


def getEmpty(board):
    """ Empty spaces """
    lst = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                lst.append((i, j))
    return lst


def drop(board, n):
    """ Random drops """
    for i in range(n):
        row, col = random.choice(getEmpty(board))
        board[row][col] = random.choice(vals)
    return board


def removeSpaces(board):
    """ remove the spaces between tiles """
    for x in range(3):
        for i in range(4):
            for j in range(x, 4):
                if board[i][x] == 0:
                    board[i][x] = board[i][j]
                    board[i][j] = 0
    return board


def move(board, direction):
    """ Move in Left, Right, Up or Down """

    global score, last_score
    initial_score = score
    board1 = board.copy()
    board2 = numpy.rot90(board1, direction)
    board2 = removeSpaces(board2)

    # merge adjacent tiles
    for i in range(4):
        for j in range(1, 4):
            if board2[i][j] == board2[i][j - 1]:
                board2[i][j - 1] *= 2
                score += board2[i][j - 1]
                board2[i][j] = 0

    board2 = removeSpaces(board2)
    board1 = numpy.rot90(board2, -direction)

    if not numpy.array_equal(board, board1):
        undos.append(board)
        board1 = drop(board1, 1)

    if initial_score != score:
        last_score = initial_score

    return board1


def state(board):
    """ 1 for win, 0 for not finished, -1 for lose """
    for i in range(4):  # check for empty spaces
        for j in range(4):
            if board[i][j] == 0:
                return 0

    for i in range(4):  # Horizontal Check
        for j in range(1, 4):
            if board[i][j] == board[i][j - 1]:
                return 0

    for i in range(3):  # Vertical Check
        for j in range(4):
            if board[i][j] == board[i + 1][j]:
                return 0

    return -1


class Block(pygame.sprite.Sprite):
    text = ' '
    fontColor = color = BLACK

    def __init__(self, x, y, val):
        super().__init__()

        self.val = val
        self.font = pygame.font.SysFont("Clear Sans", 35)
        self.image = pygame.Surface(block_size)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.textSurf = self.font.render(self.text, 1, self.fontColor)

    def update(self):
        """ update the sprite and its text """
        curVal = BOARD[self.val[0]][self.val[1]]
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


def create_tiles(block_list, top):
    for i in range(4):
        for j in range(4):
            block = Block(j * (block_size[0] + spaces[0]) + spaces[1], top, (i, j))
            block_list.add(block)

        top += block_size[1] + spaces[2]


def undo(x=None):
    global BOARD, score, last_score

    BOARD = undos[-1]
    score = last_score


def set_restart(value):
    global restarting

    restarting = value


def new():
    global BOARD, score, last_score, undos

    BOARD = numpy.zeros((4, 4), dtype='int')
    last_score = score = 0
    drop(BOARD, 2)
    undos = [BOARD.copy()]


def run(_depth=0):
    global BOARD, last_score, score, undos, restarting, depth

    """ Pygame variables and fonts """
    pygame.init()
    screen = pygame.display.set_mode((SCREENX, SCREENY), 0, 32)
    clock = pygame.time.Clock()
    block_list = pygame.sprite.Group()

    fonts = [pygame.font.SysFont('Arial', size, True) for size in [70, 40, 25]]

    lose_label = Label((0,0,200,100), font=fonts[1], text='You Lose', fgcolor=BLACK, bgcolor=(192,100,100))
    restartUI = [Frame((45, 145, 405, 405), bgcolor=BLACK, transparency=100),
                 Frame((150,300,200,100), bgcolor=(192,100,100)),
                 Label((150,300,200,50), font=fonts[1], text='Restart?', fgcolor=BLACK, bgcolor=(192,100,100)),
                 Button((160,360,75,35), font=fonts[1], text='Yes', fgcolor=BLACK, bgcolor=(100,100,180), command=lambda x: run(_depth+1)),
                 Button((265,360,75,35), font=fonts[1], text='No', fgcolor=BLACK, bgcolor=(100,100,180), command=lambda x: set_restart(False))]
    
    mainUI = [Button((390,95,50,50), image=pygame.image.load('undo.png'), bgcolor=BGCOLOR, command=undo),
              Button(((330,95,50,50)), image=pygame.image.load('restart.png'), bgcolor=BGCOLOR, command=lambda x: set_restart(True)),
              Label((25,50,200,80), font=fonts[0], text="2048", bgcolor=BGCOLOR, fgcolor=BLACK)]

    """ re-initialize board """
    depth = max(depth, _depth)
    if not depth:
        [score, last_score] = numpy.loadtxt('score.csv', dtype='int')
        [undos, BOARD] = numpy.loadtxt('data.csv', dtype='int').reshape((2, 4, 4))
        undos = [undos]
    else:
        new()

    create_tiles(block_list, DIST_Y)
    restarting = False
    running = True

    while running:
        if _depth != depth:
            continue

        screen.fill(BGCOLOR)
        pygame.draw.rect(screen, (119, 110, 101), (45, 145, 405, 405))
        block_list.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN and not restarting:
                "game movement based on keys pressed "

                if event.key == pygame.K_w: BOARD = move(BOARD, 1)
                elif event.key == pygame.K_a: BOARD = move(BOARD, 0)
                elif event.key == pygame.K_s: BOARD = move(BOARD, 3)
                elif event.key == pygame.K_d: BOARD = move(BOARD, 2)
                elif event.key == pygame.K_u:
                    if len(undos):
                        BOARD = undos.pop()
                        score = last_score

        x = state(BOARD)
        block_list.update()
        if x == -1:
            lose_label.draw(screen, centre=True)
            restarting = True

        if restarting: [u.draw(screen) for u in restartUI]

        Label((275,50,180,50), font=fonts[2], text=f"SCORE: {score}", bgcolor=BGCOLOR, fgcolor=BLACK).draw(screen)
        [u.draw(screen) for u in mainUI]

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    undos.append(BOARD)
    data = numpy.array(undos[-2:]).reshape(8, 4)

    if depth == _depth:
        numpy.savetxt('data.csv', data, fmt='%d')
        numpy.savetxt('score.csv', [score, last_score], fmt='%d')


if __name__ == "__main__":
    run()
