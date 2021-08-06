import pygame
import time
from constants import *


class Player(pygame.sprite.Sprite):
    "Controls player sprites"
    def __init__(self, game, side, x, y):
        super().__init__()
        self.game = game
        self.side = side
        self.color = PLAYERS[side]
        self.start_pos = [x, y]
        self.velocity = pygame.math.Vector2()

        self.image = pygame.Surface((2 * PLAYER_RADIUS, 2 * PLAYER_RADIUS))
        self.image.fill(GREEN)
        self.image.set_colorkey(GREEN)
        self.rect = self.image.get_rect(center=self.start_pos)

        pygame.draw.circle(self.image, BLACK, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS)
        pygame.draw.circle(self.image, self.color, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS - 5)
        pygame.draw.circle(self.image, BLACK, (PLAYER_RADIUS, PLAYER_RADIUS), 5)

    def update(self):
        if pygame.mouse.get_pressed()[0]:
            target_rect = self.rect.copy()
            target_rect.center = pygame.mouse.get_pos()

            w, h = self.game.board_rect.size
            bounds = pygame.Rect(0, h//2 + 50, w, h//2)
            target_pos = check_bounds(target_rect, bounds).center

            self.rect = self.move_to(target_pos, MAX_PLAYER_SPEED)

    def move_to(self, target, max_speed):
        self.velocity = pygame.math.Vector2(target[0] - self.rect.centerx, target[1] - self.rect.centery)
        if self.velocity.length() > max_speed * self.game.tick:
            self.velocity.scale_to_length(max_speed * self.game.tick)

        return self.rect.move(self.velocity.x, self.velocity.y)

    def reset(self):
        self.rect.center = self.start_pos


class AIPlayer(Player):
    "Controls the AI Player"
    def __init__(self, game, side, x, y, difficulty=2):
        super().__init__(game, side, x, y)
        self.opponent = game.player2
        self.difficulty = difficulty
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
            max_speed = self.difficulty * MAX_PLAYER_SPEED / 4
            if self.check_ball_collision():
                target_rect.center = (2 * self.rect.centerx - ball_rect.centerx, 2 * self.rect.centery - ball_rect.centery)
            else:
                target_rect.center = (ball_rect.centerx, ball_rect.centery)
        else:
            # Just move horizontally towards the ball, vertically to center
            max_speed = self.difficulty * MAX_PLAYER_SPEED / 8
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
        self.velocity += (bvf - bvi) * direction

        # Prevent sticking
        offset = PLAYER_RADIUS + BALL_RADIUS - distance + 2
        self.rect.move_ip(-direction.x * offset, -direction.y * offset)
        return True
    
    def update(self):
        c1 = self.check_collision(self.game.player1)
        c2 = self.check_collision(self.game.player2)
        
        # Restrict max speed
        if self.velocity.length() > MAX_BALL_SPEED * self.game.tick:
            self.velocity.scale_to_length(MAX_BALL_SPEED * self.game.tick)

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
            velocity.x *= -0.5
        if target_rect.top < self.bounds.top or target_rect.bottom > self.bounds.bottom:
            velocity.y *= -0.5
        
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


class BaseGame:
    "Base Game Class to be used by both server and client"
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.player1 = self.player2 = self.ball = None
        self.board_rect = None
        self.winner = None
        self.goal = False
        self.time_of_goal = self.tick = 0
        self.scores = [0, 0]

    def score_goal(self):
        self.goal = True
        self.time_of_goal = time.time()
        if self.ball.rect.centery < SCREENY//2:
            self.scores[0] += 1
        else:
            self.scores[1] += 1

        if self.scores[0] == 7:
            self.winner = self.player1
        elif self.scores[1] == 7:
            self.winner = self.player2

