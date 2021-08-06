import pygame
from constants import *


def multiline_text(surface, font, color, text, top=0):
    "Renders a multiline text at the center of the given surface"
    labels = []
    width = surface.get_width()
    for line in text.strip().splitlines():
        label = font.render(line, 1, color)
        rect = label.get_rect(centerx=width/2, top=top)
        surface.blit(label, rect)
        top += rect.height


class UIScreen:
    state = ''
    def __init__(
        self, manager, size=(SCREENX, SCREENY), 
        bg='darkgreen', transparent=False
    ):
        self.manager = manager
        self.assets = manager.assets
        self.game = manager.game
        self.buttons = []

        self.surface = pygame.Surface(size)
        self.surface.fill(bg)
        if transparent:
            self.surface.set_colorkey(bg)
    
    def change_state(self, new_state):
        self.game.state = new_state

    def prepare(self):
        pass

    def run(self, screen):
        screen.blit(self.surface, (0, 0))


class MenuScreen(UIScreen):
    state = 'MENU'
    def prepare(self):
        self.surface.blit(self.assets['bg_img'], (10, 30))
        multiline_text(
            self.surface, self.assets['font1'], 
            WHITE,  'AIR HOCKEY\nPYTHON', top=50
        )

        buttons = [
            ('PLAY AI', lambda: self.change_state('PLAYING')),
            ('PLAY ONLINE', self.game.connect_client),
            ('ABOUT', lambda: self.change_state('ABOUT')),
            ('EXIT', self.game.quit)
        ]

        for i, (btn_text, func) in enumerate(buttons):
            btn_img = self.assets['menu_btn_img'].copy()
            btn_img_rect = btn_img.get_rect(center=(SCREENX/2, 250+i*75))
            btn_label = self.assets['font3'].render(btn_text, 1, BLACK)
            btn_rect = btn_label.get_rect(center=(btn_img_rect.w//2, btn_img_rect.h//2))
            self.buttons.append((btn_img_rect, func))

            btn_img.blit(btn_label, btn_rect)
            self.surface.blit(btn_img, btn_img_rect)


class AboutScreen(UIScreen):
    state = 'ABOUT'
    def prepare(self):
        about_label = self.assets['font1'].render('ABOUT', 1, WHITE)
        about_rect = about_label.get_rect(center=(SCREENX/2, 50))
        self.surface.blit(about_label, about_rect)

        multiline_text(
            self.surface, self.assets['font4'],
            WHITE, ABOUT_TEXT, top=120
        )

        close_btn_rect = self.assets['close_img'].get_rect(center=(SCREENX/2, 500))
        self.buttons.append((close_btn_rect, lambda: self.change_state('MENU')))
        self.surface.blit(self.assets['close_img'], close_btn_rect)


class PlayingScreen(UIScreen):
    state = 'PLAYING'
    def draw_board(self, size):
        "Drawing the game board"
        surface = pygame.Surface(size)
        surface.fill((0, 0xC0, 0))
        rect = surface.get_rect()

        pygame.draw.circle(surface, WHITE, rect.center, 80, 3)
        pygame.draw.line(surface, WHITE, rect.midright, rect.midleft, 3)

        goal_edge_size = (rect.width - GOAL_WIDTH) // 2

        pygame.draw.rect(surface, WHITE, (goal_edge_size-40, -10, goal_edge_size+80, 100), 3)
        pygame.draw.rect(surface, WHITE, (goal_edge_size-40, rect.height - 90, goal_edge_size+80, 100), 3)

        pygame.draw.line(surface, BLACK, (goal_edge_size, 0), (goal_edge_size + GOAL_WIDTH, 0), 6)
        pygame.draw.line(surface, BLACK, (goal_edge_size, rect.height), (goal_edge_size + GOAL_WIDTH, rect.height), 7)
        return surface, rect

    def prepare(self):
        board_surface, board_rect = self.draw_board((SCREENX, SCREENY - 50))
        self.game.board_rect = board_rect.move(0, 50)
        self.surface.blit(board_surface, (0, 50))

        title_label = self.assets['font2'].render('AIR HOCKEY', 1, WHITE)
        pause_rect = self.assets['pause_img'].get_rect(right=SCREENX - 5, y=0)
        self.surface.blit(title_label, (10, 5))
        self.surface.blit(self.assets['pause_img'], pause_rect)

        self.buttons.append((pause_rect, self.game.pause))

        self.goal_label = self.assets['font1'].render('GOAL!!', 1, WHITE)
        self.goal_rect = self.goal_label.get_rect(center=(SCREENX//2, SCREENY//2))

    def run(self, screen):
        screen.blit(self.surface, (0, 0))
        if self.game.goal:
            self.game.players.draw(screen)
        else:
            self.game.all_sprites.draw(screen)

        score_label1 = self.assets['font3'].render(str(self.game.scores[0]), 1, WHITE)
        score_rect1 = score_label1.get_rect(right=SCREENX-5, bottom=SCREENY//2+25)
        score_label2 = self.assets['font3'].render(str(self.game.scores[1]), 1, WHITE)
        score_rect2 = score_label2.get_rect(right=SCREENX-5, top=SCREENY//2+25)

        screen.blit(score_label1, score_rect1)
        screen.blit(score_label2, score_rect2)

        if self.game.goal:
            screen.blit(self.goal_label, self.goal_rect)


class PauseScreen(UIScreen):
    state = 'PAUSED'
    def prepare(self):
        self.pause_bg_img = self.assets['bg_img'].copy()
        self.pause_bg_rect = self.pause_bg_img.get_rect(center=self.game.board_rect.center)

        restart_rect = self.assets['restart_img'].get_rect(x=110, y=75)
        close_rect = self.assets['close_img'].get_rect(x=180, y=75)
        pause_rect = self.assets['pause_img'].get_rect(right=SCREENX - 5, y=0)
        x, y = self.pause_bg_rect.x, self.pause_bg_rect.y

        self.buttons.extend([
            (restart_rect.move(x, y), self.game.restart),
            (close_rect.move(x, y), self.back_to_menu),
            (pause_rect, self.game.pause)
        ])

        self.pause_bg_img.blit(self.assets['restart_img'], restart_rect)
        self.pause_bg_img.blit(self.assets['close_img'], close_rect)
    
    def back_to_menu(self):
        self.game.restart()
        self.change_state('MENU')
    
    def run(self, screen):
        pause_label = self.assets['font1'].render(self.manager.pause_message, 1, WHITE)
        pause_rect = pause_label.get_rect(centerx=SCREENX/2, y=self.pause_bg_rect.y+5)

        screen.blit(self.pause_bg_img, self.pause_bg_rect)
        screen.blit(pause_label, pause_rect)


class WaitingScreen(UIScreen):
    state = 'WAITING'
    def prepare(self):
        self.dots = 0
        close_rect = self.assets['close_img'].get_rect(center=(SCREENX//2, SCREENY-200))
        self.buttons.append((close_rect, self.game.disconnect_client))
        self.surface.blit(self.assets['close_img'], close_rect)
        
    def run(self, screen):
        screen.blit(self.surface, (0, 0))
        self.dots = (self.dots + 1 / FPS) % 4#int((self.dots + 1) * self.game.tick * 100) % 4
        multiline_text(
            screen, self.assets['font1'], WHITE, 
            'WAITING FOR\nPLAYERS' + '.' * int(self.dots), top=SCREENY//2-100
        )


class UIManager:
    "Handles all UI stuff"
    def __init__(self, game):
        self.game = game
        self.assets = self.load_assets()
        self.pause_message = 'PAUSED'
        self.screens = [MenuScreen, AboutScreen, PlayingScreen, PauseScreen, WaitingScreen]
        self.screens = [screen(self) for screen in self.screens]

    def load_assets(self):
        "Loads all the assets used before running the game"
        return {
            'font1': pygame.font.Font('assets/soupofjustice.ttf', 60),
            'font2': pygame.font.Font('assets/soupofjustice.ttf', 45),
            'font3': pygame.font.Font('assets/soupofjustice.ttf', 40),
            'font4': pygame.font.Font('assets/soupofjustice.ttf', 20),

            'restart_img': pygame.image.load('assets/restart.png'),
            'pause_img': pygame.image.load('assets/pause.png'),
            'menu_btn_img': pygame.image.load('assets/button.png'),
            'close_img': pygame.image.load('assets/close.png'),
            'bg_img': pygame.image.load('assets/bg.png')
        }

    def prepare(self):
        "Run before main game loop"
        for screen in self.screens:
            screen.prepare()

    def draw(self, game_screen):
        "Runs on main game loop - state PLAYING"
        for screen in self.screens:
            if screen.state == self.game.state:
                screen.run(game_screen)

    def handle_mouse_up(self):
        "Used for detecting button clicks"
        pos = pygame.mouse.get_pos()
        for screen in self.screens:
            if screen.state != self.game.state:
                continue

            for rect, function in screen.buttons:
                if function and rect.collidepoint(pos):
                    function()
            break