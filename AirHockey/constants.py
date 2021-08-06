"""All Game Constants"""
FPS = 60
SCREENX, SCREENY = (360, 600)
GOAL_WIDTH = SCREENX // 3
BORDER_WIDTH = 20

AI_DIFFICULTY = 1 # Set higher for more difficulty (1-4)
PLAYER_RADIUS = GOAL_WIDTH // 4.5
BALL_RADIUS = 20
MAX_PLAYER_SPEED = 0.8
MAX_BALL_SPEED = 1.6

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