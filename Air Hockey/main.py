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
    
    def update(self):
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
    def __init__(self, game):
        self.game = game
        self.buttons = [] # List[(rect, function)]
        self.load_assets()

    def load_assets(self):
        self.title_font = pygame.font.SysFont('Arial', 30, bold=True)
        self.score_font = pygame.font.SysFont('Arial', 40, bold=True)
        self.goal_font = pygame.font.SysFont('Arial', 60, bold=True)

        self.goal_label = self.goal_font.render('GOAL!!', 1, WHITE)
        self.title_label = self.title_font.render('AIR HOCKEY', 1, WHITE)

        self.restart_img = pygame.image.load('images/restart.png')
        self.pause_img = pygame.image.load('images/pause.png')

    def draw_board(self, size):
        surface = pygame.Surface(size)
        surface.fill('green3')
        rect = surface.get_rect()

        pygame.draw.circle(surface, WHITE, rect.center, 80, 3)
        pygame.draw.line(surface, WHITE, rect.midright, rect.midleft, 3)

        goal_edge_size = (rect.width - GOAL_WIDTH) // 2

        pygame.draw.rect(surface, WHITE, (goal_edge_size-40, -10, goal_edge_size+80, 100), 3)
        pygame.draw.rect(surface, WHITE, (goal_edge_size-40, rect.height - 90, goal_edge_size+80, 100), 3)

        pygame.draw.line(surface, BLACK, (goal_edge_size, 0), (goal_edge_size + GOAL_WIDTH, 0), 6)
        pygame.draw.line(surface, BLACK, (goal_edge_size, rect.height), (goal_edge_size + GOAL_WIDTH, rect.height), 7)
        return surface, rect

    def prepare_main_ui(self):
        self.board_surface, self.board_rect = self.draw_board((SCREENX, SCREENY - 50))
        self.board_rect.move_ip(0, 50)

        self.title_bg = pygame.Surface((SCREENX, 50))
        self.title_bg.fill('forest green')
        self.title_bg.blit(self.title_label, (20, 8))
        
        pause_rect = self.pause_img.get_rect(right=SCREENX - 60, y=0)
        restart_rect = self.restart_img.get_rect(right=SCREENX - 5, y=0)

        self.title_bg.blit(self.pause_img, pause_rect)
        self.title_bg.blit(self.restart_img, restart_rect)

        self.buttons += [(pause_rect, self.game.pause), (restart_rect, self.game.restart)]

        self.goal_rect = self.goal_label.get_rect(center=self.board_rect.center)
        self.pause_bg_img = self.goal_font.render('PAUSED', 1, WHITE)
        self.pause_bg_rect = self.pause_bg_img.get_rect(center=self.board_rect.center)

    def draw_run_ui(self, screen):
        screen.blit(self.board_surface, self.board_rect)
        self.game.all_sprites.draw(screen)

        screen.blit(self.title_bg, (0, 0))

        score_label1 = self.score_font.render(str(self.game.scores[0]), 1, WHITE)
        score_rect1 = score_label1.get_rect(right=SCREENX-5, bottom=SCREENY//2+25)
        score_label2 = self.score_font.render(str(self.game.scores[1]), 1, WHITE)
        score_rect2 = score_label2.get_rect(right=SCREENX-5, top=SCREENY//2+25)

        screen.blit(score_label1, score_rect1)
        screen.blit(score_label2, score_rect2)

        if self.game.goal:
            screen.blit(self.goal_label, self.goal_rect)
    
    def draw_pause_ui(self, screen):
        screen.blit(self.pause_bg_img, self.pause_bg_rect)

    def handle_mouse_down(self):
        pos = pygame.mouse.get_pos()
        for rect, function in self.buttons:
            if rect.collidepoint(pos):
                function()


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREENX, SCREENY))
        self.clock = pygame.time.Clock()
        self.ui = UIManager(self)

        self.state = 'PLAYING'
        self.goal = self.game_over = False
        self.player1 = self.player2 = None
        self.scores = [0, 0]

        self.time_of_goal = 0

    def move_player(self, player):
        if pygame.mouse.get_pressed()[0]:
            target_rect = player.rect.copy()
            target_rect.center = pygame.mouse.get_pos()

            w, h = self.board_rect.size
            bounds = pygame.Rect(0, h//2 + 50, w, h//2)
            player.target_pos = check_bounds(target_rect, bounds).center
    
    def score_goal(self):
        self.goal = True
        self.time_of_goal = time.time()
        if self.ball.rect.centery > SCREENY//2:
            self.scores[0] += 1
        else:
            self.scores[1] += 1
        
        if self.scores[0] == 7:
            message = 'You Lose!'
        elif self.scores[1] == 7:
            message = 'You Win' 

    def reset(self):
        self.ball.reset()
        self.player1.reset()
        self.player2.reset()
        self.goal = False
    
    def pause(self):
        self.state = 'PAUSED' if self.state == 'PLAYING' else 'PLAYING'

    def restart(self):
        self.reset()
        self.scores = [0, 0]
        self.state = 'PLAYING'

    def run(self):
        self.ui.prepare_main_ui()
        self.board_rect = self.ui.board_rect

        self.player1 = AIPlayer(self, 0, SCREENX//2, SCREENY//4 + 50)
        self.player2 = Player(self, 1, SCREENX//2, 3 * SCREENY//4 + 25)
        self.ball = Ball(self, *self.board_rect.center)

        self.all_sprites = pygame.sprite.Group(self.ball, self.player1, self.player2)

        while not self.game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_over = True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.ui.handle_mouse_down()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.pause()
                    elif event.key == pygame.K_r:
                        self.restart()
            
            if self.state == 'PLAYING':
                self.ui.draw_run_ui(self.screen)

                self.ball.check_collision(self.player2)
                self.ball.check_collision(self.player1)

                self.move_player(self.player2)
                self.all_sprites.update()

                if self.goal and time.time() - self.time_of_goal >= GOAL_TEXT_DELAY:
                    self.reset()
            elif self.state == 'PAUSED':
                self.ui.draw_pause_ui(self.screen)

            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == '__main__':
    pygame.init()
    Game().run()