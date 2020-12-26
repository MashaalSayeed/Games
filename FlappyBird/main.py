import pygame
import random
import math

""" General Configuration """
SCREENX = 500
SCREENY = 500
BASEY = 440
FPS = 30
WHITE = (255, 255, 255)

""" Game Configuration """
BIRD_SIZE = (42, 35)
PIPE_WIDTH = 75
GRAVITY = 1.25
JUMPFORCE = 12.5
SPEED = 4
PIPE_GAP_X = 100
PIPE_DISTANCE = (620, 650)

PIPE_SIZE_COMBO = [[x, 320 - x] for x in range(50, 310, 10)]


class Bird(pygame.sprite.Sprite):
   def __init__(self):
      super().__init__()

      # Load the birdie image
      self.img = pygame.image.load('images/bird.png')
      self.img = pygame.transform.scale(self.img, BIRD_SIZE)

      # Scale the image to custom size
      self.image = pygame.transform.rotate(self.img, 0)

      self.rect = self.image.get_rect()
      self.rect.center = (SCREENX / 2, SCREENY / 2)

      self.vector = pygame.math.Vector2

      self.pos = self.vector(self.rect.center)
      self.velocity = self.vector(0, 0)
      self.acceleration = self.vector(0, GRAVITY)


   def update(self):
      self.velocity += self.acceleration
      self.pos += self.velocity + (self.acceleration / 2)
      self.rect.center = self.pos

      # Rotation
      angle = math.atan(-self.velocity.y / SPEED) * 30
      self.image = pygame.transform.rotate(self.img, angle)

   def jump(self):
      self.velocity.y = -JUMPFORCE

   def isAlive(self):
      return 0 < self.rect.y < BASEY


class Pipe(pygame.sprite.Sprite):
   passed = False
   
   def __init__(self, pos_x, height, isTop):
      super().__init__()

      self.img = pygame.image.load('images/green-pipe.png')
      self.image = pygame.transform.scale(self.img, (PIPE_WIDTH, height))

      pos_y = BASEY - height

      if isTop:
         self.image = pygame.transform.rotate(self.image, 180)
         pos_y = 0

      self.rect = self.image.get_rect()
      self.rect.x = pos_x
      self.rect.y = pos_y

   def update(self):
      self.rect.x -= SPEED

      if self.rect.x < 0:
         del self

   def getScore(self, score):
      if self.rect.x < (SCREENX / 2) + (PIPE_WIDTH / 2) and not self.passed:
         self.passed = True
         return 0.5
      
      return 0


def randomPipe():
   p1, p2 = PIPE_DISTANCE
   pipe_x = random.randint(p1, p2)
   pipe_h = random.choice(PIPE_SIZE_COMBO)

   pipe1 = Pipe(pipe_x, pipe_h[1], True)
   pipe2 = Pipe(pipe_x, pipe_h[0], False)

   return (pipe1, pipe2)

def main():
   # Variables
   crashed = start = False
   score = 0
   
   pygame.init()

   screen = pygame.display.set_mode([SCREENX, SCREENY])
   clock = pygame.time.Clock()
   GOFont = restartFont = scoreFont = pygame.font.SysFont("comic", 50, bold=True)

   # Load Background
   load_bg = pygame.image.load('images/bg.png')
   bg = pygame.transform.scale(load_bg, (SCREENX, SCREENY))

   bird = Bird()

   # Create Sprite Group 
   all_sprites = pygame.sprite.Group()
   all_sprites.add(bird)

   pipe1, pipe2 = randomPipe()
   
   pipes = pygame.sprite.Group()
   pipes.add(pipe1, pipe2)
   all_sprites.add(pipe1, pipe2)

   
   # Main Event Loop
   while True:
      for event in pygame.event.get():
         if event.type == pygame.QUIT:
            pygame.quit()
            return

         if event.type == pygame.KEYDOWN:
            start = True
            
            if event.key == pygame.K_SPACE:
               if crashed:
                  return main()
               else:
                  bird.jump()

      # Set Background
      screen.blit(bg, (0, 0))
      
      scoreText = scoreFont.render(str(int(score)), 1, WHITE)
      scoreLabel = scoreText.get_rect()
      scoreLabel.center = (SCREENX/2, 100)

      if start and not crashed:
         collisions = pygame.sprite.spritecollide(bird, pipes, False)

         if not bird.isAlive() or collisions:
            del bird
            crashed = True

         all_sprites.update()

         for p in pipes:
            score += p.getScore(score)

         # Add more pipes
         if pipe1.rect.x < SCREENX - PIPE_GAP_X and pipe2.rect.x < SCREENX - PIPE_GAP_X:
            pipe1, pipe2 = randomPipe()

            pipes.add(pipe1, pipe2)
            all_sprites.add(pipe1, pipe2)

      all_sprites.draw(screen)
      screen.blit(scoreText, scoreLabel)

      """ Now to make a label and a button """

      if crashed:
         # Game Over Label
         GOText = GOFont.render('GAME OVER', True, WHITE)
         GOLabel = GOText.get_rect()
         screen.blit(GOText, (SCREENX/2 - GOLabel[2]/2, SCREENY/2 - GOLabel[3]/2))

         # Restart Button
         restartText = restartFont.render('Restart', True, WHITE)
         restartLabel = restartText.get_rect()

         restartLabel.center = (SCREENX/2, SCREENY/2 + GOLabel[3])
      
         mouse = pygame.mouse.get_pos()
         click = pygame.mouse.get_pressed()

         left, top, width, height = restartLabel
         if left + width > mouse[0] > left and top + height > mouse[1] > top:
            pygame.draw.rect(screen, (144, 238, 144), restartLabel)

            if click[0] == 1:
               return main()
            
         else:
            pygame.draw.rect(screen, (0, 200, 0), restartLabel)

         screen.blit(restartText, restartLabel)

      pygame.display.flip()
      clock.tick(FPS)

      
if __name__ == '__main__':
   main()
