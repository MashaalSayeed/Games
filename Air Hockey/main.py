import time
import pygame

# Game Constants
FPS = 30
SCREENX, SCREENY = (360, 600)
GOAL_WIDTH = SCREENX // 3
BORDER_WIDTH = 20

AI_DIFFICULTY = 4 # Set higher for more difficulty (1-4)
PLAYER_RADIUS = GOAL_WIDTH // 4.5
BALL_RADIUS = 20
MAX_PLAYER_SPEED = 20

GOAL_TEXT_DELAY = 3

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

PLAYERS = [RED, BLUE]

ABOUT_TEXT = """Air hockey is a game where
two players play against each other

Move your player using the mouse
Hit the ball to the opponent's
side to score a goal
First one to get 7 goals wins!\n
-----------------------------------\n
Credits:\n
Creator - Mashaal Sayeed
Font - OmenType
Images - pzUH
"""


def check_bounds(rect, bounds):
    "Ensures that the given rect is within the bounds rect"
    if rect.left < bounds.left:
        rect.left = bounds.left
    elif rect.right > bounds.right:
        rect.right = bounds.right

    if rect.top < bounds.top:
        rect.top = bounds.top
    elif rect.bottom > bounds.bottom:
        rect.bottom = bounds.bottom
    return rect


def multiline_text(surface, font, color, text, top=0):
    labels = []
    width = surface.get_width()
    for line in text.strip().splitlines():
        label = font.render(line, 1, color)
        rect = label.get_rect(centerx=width/2, top=top)
        surface.blit(label, rect)
        top += rect.height


class Player(pygame.sprite.Sprite):
    "Controls player sprites"
    def __init__(self, game, side, x, y):
        super().__init__()

        self.game = game
        self.side = side
        self.color = PLAYERS[side]
        self.start_pos = [x, y]
        self.target_pos = self.start_pos
        self.velocity = pygame.math.Vector2()

        self.image = pygame.Surface((2 * PLAYER_RADIUS, 2 * PLAYER_RADIUS))
        self.image.fill(GREEN)
        self.image.set_colorkey(GREEN)
        self.rect = self.image.get_rect(center=self.start_pos)

        pygame.draw.circle(self.image, BLACK, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS)
        pygame.draw.circle(self.image, self.color, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS - 5)
        pygame.draw.circle(self.image, BLACK, (PLAYER_RADIUS, PLAYER_RADIUS), 5)

    def move_player(self):
        if pygame.mouse.get_pressed()[0]:
            target_rect = self.rect.copy()
            target_rect.center = pygame.mouse.get_pos()

            w, h = self.game.board_rect.size
            bounds = pygame.Rect(0, h//2 + 50, w, h//2)
            self.target_pos = check_bounds(target_rect, bounds).center
    
    def update(self):
        self.move_player()
        self.rect = self.move_to(self.target_pos, MAX_PLAYER_SPEED)

    def move_to(self, target, max_speed):
        self.velocity = pygame.math.Vector2(target[0] - self.rect.centerx, target[1] - self.rect.centery)
        if self.velocity.length() > max_speed:
            self.velocity.scale_to_length(max_speed)

        return self.rect.move(self.velocity.x, self.velocity.y)

    def reset(self):
        self.rect.center = self.start_pos
        self.target_pos = self.start_pos


class AIPlayer(Player):
    def __init__(self, game, side, x, y):
        super().__init__(game, side, x, y)

        self.opponent = game.player2
        board_size = game.board_rect.size
        if self.side == 0:
            self.bounds = pygame.Rect(0, 50, board_size[0], board_size[1]//2)
        else:
            self.bounds = pygame.Rect(0, board_size[1]//2 + 50, board_size[0], board_size[1]//2)

    def update(self):
        target_rect = self.rect.copy()
        ball_rect = self.game.ball.rect
        if self.bounds.collidepoint(ball_rect.center):
            # ball is in my field!
            max_speed = AI_DIFFICULTY * MAX_PLAYER_SPEED / 4
            if self.check_ball_collision():
                target_rect.center = (2 * self.rect.centerx - ball_rect.centerx, 2 * self.rect.centery - ball_rect.centery)
            else:
                target_rect.center = (ball_rect.centerx, ball_rect.centery)
        else:
            # Just move horizontally towards the ball, vertically to center
            max_speed = AI_DIFFICULTY * MAX_PLAYER_SPEED / 8
            target_rect.center = (ball_rect.centerx, self.bounds.centery)
        
        target_rect = check_bounds(target_rect, self.bounds)
        self.rect = self.move_to(target_rect.center, max_speed)

    def check_ball_collision(self):
        distance = (self.rect.centerx - self.game.ball.rect.centerx) ** 2  + (self.rect.centery - self.game.ball.rect.centery) ** 2
        return distance ** 0.5 < PLAYER_RADIUS + BALL_RADIUS - (2 * AI_DIFFICULTY)


class Ball(pygame.sprite.Sprite):
    "Controls the ball sprite"
    def __init__(self, game, x, y):
        super().__init__()

        self.start_pos = x, y
        self.game = game
        self.velocity = pygame.math.Vector2()
        self.bounds = pygame.Rect(0, 50, *game.board_rect.size)
        self.goal = False

        self.image = pygame.Surface((2 * BALL_RADIUS, 2 * BALL_RADIUS))
        self.image.fill(GREEN)
        self.image.set_colorkey(GREEN)
        self.rect = self.image.get_rect(center=self.start_pos)

        pygame.draw.circle(self.image, BLACK, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
        pygame.draw.circle(self.image, WHITE, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS - 5)
    
    def check_collision(self, player):
        "Check collisions with players and bounce accordingly"
        # https://stackoverflow.com/a/345863
        # Check for collisions (distance b/w centers <= sum of radii)
        collision = pygame.math.Vector2(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
        distance = collision.length()
        if distance > PLAYER_RADIUS + BALL_RADIUS:
            return False
        
        # Get projections of both vectors in the direction of collision
        direction = collision / (distance or 1)
        bvi = self.velocity.dot(direction)
        pvi = player.velocity.dot(direction)

        # Apply collision in 1D (mass of player >> mass of ball)
        bvf = 2 * pvi - bvi
        self.velocity += (bvf - bvi) * direction * 0.6

        # Prevent sticking
        offset = PLAYER_RADIUS + BALL_RADIUS - distance + 2
        self.rect.move_ip(-direction.x * offset, -direction.y * offset)
        return True
    
    def update(self):
        is_goal, self.rect = self.move(self.rect, self.velocity)
        if not is_goal:
            self.rect = check_bounds(self.rect, self.bounds)
    
    def move(self, rect, velocity):
        "Returns (is goal, new rect), velocity changes in-place"
        # Do bouncing of walls
        target_rect = rect.move(velocity.x, velocity.y)
        if self.is_goal(target_rect):
            return True, target_rect

        if target_rect.left < self.bounds.left or target_rect.right > self.bounds.right:
            velocity.x *= -0.9
        if target_rect.top < self.bounds.top or target_rect.bottom > self.bounds.bottom:
            velocity.y *= -0.9
        
        return False, rect.move(velocity.x, velocity.y)

    def is_goal(self, rect):
        if self.game.goal:
            return True

        if rect.top < self.bounds.top or rect.bottom > self.bounds.bottom:
            goal_edge_size = (self.bounds.width - GOAL_WIDTH) // 2
            if rect.left > goal_edge_size and rect.right < goal_edge_size + GOAL_WIDTH:
                self.game.score_goal()
                return True
        return False

    def reset(self):
        self.rect.center = self.start_pos
        self.velocity = pygame.math.Vector2()


class UIManager:
    "Handles all UI stuff"
    def __init__(self, game):
        self.game = game
        self.buttons = [] # List[(rect, function)]
        self.pause_message = 'PAUSED'
        self.load_assets()

    def load_assets(self):
        "Loads all the assets used before running the game"
        self.font1 = pygame.font.Font('assets/soupofjustice.ttf', 60)
        self.font2 = pygame.font.Font('assets/soupofjustice.ttf', 45)
        self.font3 = pygame.font.Font('assets/soupofjustice.ttf', 40)
        self.font4 = pygame.font.Font('assets/soupofjustice.ttf', 20)

        self.goal_label = self.font1.render('GOAL!!', 1, WHITE)
        self.title_label = self.font2.render('AIR HOCKEY', 1, WHITE)

        self.restart_img = pygame.image.load('assets/restart.png')
        self.pause_img = pygame.image.load('assets/pause.png')
        self.menu_btn_img =  pygame.image.load('assets/button.png')
        self.close_img = pygame.image.load('assets/close.png')
        self.bg_img = pygame.image.load('assets/bg.png')

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

    def prepare_menu_surface(self):
        self.menu_surface = pygame.Surface((SCREENX, SCREENY))
        self.menu_surface.fill('darkgreen')
        
        self.menu_surface.blit(self.bg_img, (10, 30))
        multiline_text(self.menu_surface, self.font1, WHITE, 'AIR HOCKEY\nPYTHON', top=50)

        buttons = [
            ('PLAY AI', lambda: self.change_state('MENU', 'PLAYING')),
            ('PLAY ONLINE', None),
            ('ABOUT', lambda: self.change_state('MENU', 'ABOUT')),
            ('EXIT', self.game.quit)
        ]
        for i, (btn_text, func) in enumerate(buttons):
            btn_img = self.menu_btn_img.copy()
            btn_img_rect = btn_img.get_rect(center=(SCREENX/2, 250+i*75))
            btn_label = self.font3.render(btn_text, 1, BLACK)
            btn_rect = btn_label.get_rect(center=(btn_img_rect.w//2, btn_img_rect.h//2))
            self.buttons.append((btn_img_rect, func))

            btn_img.blit(btn_label, btn_rect)
            self.menu_surface.blit(btn_img, btn_img_rect)
    
    def prepare_about_surface(self):
        self.about_surface = pygame.Surface((SCREENX, SCREENY))
        self.about_surface.fill('darkgreen')

        about_label = self.font1.render('ABOUT', 1, WHITE)
        about_rect = about_label.get_rect(center=(SCREENX/2, 50))
        self.about_surface.blit(about_label, about_rect)

        multiline_text(self.about_surface, self.font4, WHITE, ABOUT_TEXT, top=120)

        close_btn_rect = self.close_img.get_rect(center=(SCREENX/2, 500))
        self.buttons.append((close_btn_rect, lambda: self.change_state('ABOUT', 'MENU')))
        self.about_surface.blit(self.close_img, close_btn_rect)

    def prepare_pause_surface(self):
        self.pause_bg_img = self.bg_img.copy()
        self.pause_bg_rect = self.pause_bg_img.get_rect(center=self.board_rect.center)

        restart_rect = self.restart_img.get_rect(x=110, y=75)
        close_rect = self.close_img.get_rect(x=180, y=75)
        self.buttons += [
            (restart_rect.move(self.pause_bg_rect.x, self.pause_bg_rect.y), self.game.restart),
            (close_rect.move(self.pause_bg_rect.x, self.pause_bg_rect.y), lambda: self.change_state('PAUSED', 'MENU'))
        ]
        self.pause_bg_img.blit(self.restart_img, restart_rect)
        self.pause_bg_img.blit(self.close_img, close_rect)

    def change_state(self, current, next_state):
        if self.game.state == current:
            self.game.state = next_state

    def prepare(self):
        "Run before main game loop"
        self.prepare_menu_surface()
        self.prepare_about_surface()

        self.board_surface, self.board_rect = self.draw_board((SCREENX, SCREENY - 50))
        self.board_rect.move_ip(0, 50)

        self.title_bg = pygame.Surface((SCREENX, 50))
        self.title_bg.fill('darkgreen')
        self.title_bg.blit(self.title_label, (10, 5))

        pause_rect = self.pause_img.get_rect(right=SCREENX - 5, y=0)
        self.title_bg.blit(self.pause_img, pause_rect)

        self.buttons.append((pause_rect, self.game.pause))
        self.goal_rect = self.goal_label.get_rect(center=(SCREENX//2, SCREENY//2))
        
        self.prepare_pause_surface()

    def draw(self, screen):
        "Runs on main game loop - state PLAYING"
        if self.game.state == 'MENU':
            screen.blit(self.menu_surface, (0,0))
        elif self.game.state == 'ABOUT':
            screen.blit(self.about_surface, (0,0))
        elif self.game.state == 'PLAYING':
            screen.blit(self.board_surface, self.board_rect)
            self.game.all_sprites.draw(screen)

            screen.blit(self.title_bg, (0, 0))

            score_label1 = self.font3.render(str(self.game.scores[0]), 1, WHITE)
            score_rect1 = score_label1.get_rect(right=SCREENX-5, bottom=SCREENY//2+25)
            score_label2 = self.font3.render(str(self.game.scores[1]), 1, WHITE)
            score_rect2 = score_label2.get_rect(right=SCREENX-5, top=SCREENY//2+25)

            screen.blit(score_label1, score_rect1)
            screen.blit(score_label2, score_rect2)

            if self.game.goal:
                screen.blit(self.goal_label, self.goal_rect)
        elif self.game.state == 'PAUSED':    
            pause_label = self.font1.render(self.pause_message, 1, WHITE)
            pause_rect = pause_label.get_rect(centerx=SCREENX/2, y=self.pause_bg_rect.y+5)

            screen.blit(self.pause_bg_img, self.pause_bg_rect)
            screen.blit(pause_label, pause_rect)

    def handle_mouse_up(self):
        "Used for detecting button clicks"
        pos = pygame.mouse.get_pos()
        for rect, function in self.buttons:
            if function and rect.collidepoint(pos):
                function()


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREENX, SCREENY))
        self.clock = pygame.time.Clock()
        self.ui = UIManager(self)

        self.state = 'MENU'
        self.win = self.goal = self.game_over = False
        self.player1 = self.player2 = None
        self.scores = [0, 0]

        self.time_of_goal = 0

        pygame.display.set_caption('Air Hockey Python')
    
    def score_goal(self):
        self.goal = True
        self.time_of_goal = time.time()
        if self.ball.rect.centery > SCREENY//2:
            self.scores[0] += 1
        else:
            self.scores[1] += 1

        if 7 in self.scores:
            self.state = 'PAUSED'
            self.ui.pause_message = 'You Lose!' if self.scores[0] == 7 else 'You Win'
            self.win = True
    
    def reset(self):
        [sprite.reset() for sprite in self.all_sprites]
        self.win = self.goal = False

    def pause(self):
        if self.state == 'PLAYING':
            self.state = 'PAUSED' 
        elif self.state == 'PAUSED' and not self.win:
            self.state = 'PLAYING'

    def restart(self):
        if self.state == 'PAUSED':
            self.reset()
            self.scores = [0, 0]
            self.state = 'PLAYING'
        
    def quit(self):
        if self.state == 'MENU':
            self.game_over = True

    def run(self):
        self.ui.prepare()
        self.board_rect = self.ui.board_rect

        self.player1 = AIPlayer(self, 0, SCREENX//2, SCREENY//4 + 50)
        self.player2 = Player(self, 1, SCREENX//2, 3 * SCREENY//4 + 25)
        self.ball = Ball(self, *self.board_rect.center)

        self.all_sprites = pygame.sprite.Group(self.ball, self.player1, self.player2)

        while not self.game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_over = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.ui.handle_mouse_up()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.pause()
                    elif event.key == pygame.K_r:
                        self.restart()

            self.ui.draw(self.screen)
            if self.state == 'PLAYING':
                self.ball.check_collision(self.player2)
                self.ball.check_collision(self.player1)
                self.all_sprites.update()

                if self.goal and time.time() - self.time_of_goal >= GOAL_TEXT_DELAY:
                    self.reset()

            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == '__main__':
    pygame.init()
    Game().run()