import pygame
import random
import copy


FPS = 30
SCREENX, SCREENY = (600, 610)

BLACK = (0,0,0)
WHITE = (255,255,255)

SSHAPE = [
    [1,0],
    [1,1],
    [0,1],
]

ZSHAPE = [
    [0,1],
    [1,1],
    [1,0]
]

TSHAPE = [
    [0,1],
    [1,1],
    [0,1]
]

LSHAPE = [
    [1,0],
    [1,0],
    [1,1],
]

JSHAPE = [
    [1,1],
    [1,0],
    [1,0],
]

OSHAPE = [
    [1,1],
    [1,1],
]

ISHAPE = [
    [1],[1],[1],[1]
]


SHAPES = [SSHAPE, ZSHAPE, TSHAPE, LSHAPE, JSHAPE, OSHAPE, ISHAPE]
COLORS = [
    (0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 255, 0),
    (255, 165, 0), (0, 0, 255), (128, 0, 128)
]


class Piece:
    def __init__(self, shape, x):
        self.shape = SHAPES[shape]
        self.color = COLORS[shape]

        self.x, self.y = x, -1
        self.rotate(random.randint(0,3))
    
    def update(self):
        self.y += 1

    def rotate(self, rot=1):
        for _ in range(rot):
            self.shape = list(zip(*self.shape[::-1]))


class Game:
    def __init__(self):
        pygame.display.set_caption('Tetris')
        self.screen = pygame.display.set_mode((SCREENX, SCREENY))
        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont('Arial Black', 40, bold=True)
        self.score_font = pygame.font.SysFont('Courier', 24, bold=True)
        self.title_label = self.title_font.render('TETRIS', 1, WHITE)
        self.next_piece_label = self.score_font.render('Next Piece', 1, WHITE)
        self.pause_img = pygame.transform.scale(pygame.image.load('pause.jpg'), (50, 50))
    
    def draw_grid(self, grid):
        grid_rect = pygame.Rect(45, 0, 310, SCREENY)
        pygame.draw.rect(self.screen, (255,0,0), grid_rect)

        for i in range(20):
            for j in range(10):
                cell_rect = pygame.Rect(grid_rect.x+5+30*j, grid_rect.y+5+30*i, 30, 30)
                pygame.draw.rect(self.screen, BLACK, cell_rect)
                pygame.draw.rect(self.screen, grid[i][j], cell_rect.inflate(-1,-1))
    
    def draw_ui(self):
        self.screen.blit(self.title_label, (385, 100))
        self.screen.blit(self.next_piece_label, (405, 180))

        grid_rect = pygame.Rect(385, 220, 190, 190)
        pygame.draw.rect(self.screen, (255,0,0), grid_rect)
        pygame.draw.rect(self.screen, BLACK, grid_rect.inflate(-5,-5))

        next_shape = self.next_piece.shape
        h, w = len(next_shape), len(next_shape[0])
        x, y = 355+(255-30*(w+2))/2, 220+(180-30*(h+2))/2#407.5, 240#
        for i in range(h):
            for j in range(w):
                cell_rect = pygame.Rect(x+30*(j+1), y+30*(i+1), 30, 30)
                pygame.draw.rect(self.screen, BLACK, cell_rect)
                if next_shape[i][j]:
                    color = self.next_piece.color
                    pygame.draw.rect(self.screen, color, cell_rect.inflate(-1,-1))

        score_label = self.score_font.render('Score:{:8}'.format(self.score), 1, WHITE)
        level_label = self.score_font.render('Level:{:8}'.format(self.level), 1, WHITE)
        lines_label = self.score_font.render('Lines:{:8}'.format(self.lines), 1, WHITE)
        self.screen.blit(score_label, (380,450))
        self.screen.blit(level_label, (380,480))
        self.screen.blit(lines_label, (380,510))

        self.screen.blit(self.pause_img, (380, 550))
    
    def place_shape(self):
        grid = copy.deepcopy(self.grid)
        for i, row in enumerate(self.current_piece.shape, start=self.current_piece.y):
            for j, cell in enumerate(row, start=self.current_piece.x):
                if i >= 0 and cell:
                    grid[i][j] = self.current_piece.color
        return grid
    
    def new_piece(self):
        shape = random.randint(0, 6)
        posx = random.randint(0, 6)
        return Piece(shape, posx)
    
    def check_valid(self):
        for i, row in enumerate(self.current_piece.shape, start=self.current_piece.y):
            for j, cell in enumerate(row, start=self.current_piece.x):
                if cell and (not (-2 < i < 20) or not (-1 < j < 10)):
                    return False
                if i >= 0 and j >= 0 and cell and self.grid[i][j] != BLACK:
                    return False
        return True
    
    def move_piece(self, inc):
        self.current_piece.x += inc
        if not self.check_valid():
            self.current_piece.x -= inc
    
    def drop(self, grid, hard=False):
        self.current_piece.update()
        self.score += 2 * self.hard_drop
        if not self.check_valid():
            if self.current_piece.y == 0:
                return print('lost')

            self.grid = grid
            self.current_piece = self.next_piece
            self.next_piece = self.new_piece()
            self.clear_rows()
            return True
        return False
    
    def rotate_piece(self):
        self.current_piece.rotate(1)
        if not self.check_valid():
            self.current_piece.rotate(3)
    
    def clear_rows(self):
        cleared = 0
        for i in range(len(self.grid)):
            if all(cell != BLACK for cell in self.grid[i]):
                self.grid[i] = [BLACK] * 10
                cleared += 1
                for r in range(i-1, -1, -1):
                    self.grid[r], self.grid[r+1] = self.grid[r+1], self.grid[r]

        points = [0, 100, 300, 600, 1000]
        self.score += points[cleared] * self.level
        self.lines += cleared
        if self.lines > self.level * 10:
            self.level += 1
            self.delay *= 0.9

    def run(self):
        self.grid = grid = [[BLACK for _ in range(10)] for _ in range(20)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.score = self.lines = 0
        self.level = 1
        self.delay = 1000
        self.hard_drop = False
        paused = game_over = False
        last_moved = 0

        while not game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                elif not paused and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r: self.rotate_piece()
                    if event.key == pygame.K_a: self.move_piece(-1)
                    if event.key == pygame.K_d: self.move_piece(1)
            
            pressed = pygame.key.get_pressed()
            self.hard_drop = False
            if pressed[pygame.K_s]: self.hard_drop = True
            
            now = pygame.time.get_ticks()
            delay = self.delay if not self.hard_drop else self.hard_drop ** 0.5
            if now - delay > last_moved:
                last_moved = now
                self.drop(grid)

            self.screen.fill(BLACK)
            grid = self.place_shape()
            self.draw_grid(grid)
            self.draw_ui()

            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == '__main__':
    pygame.init()
    Game().run()
