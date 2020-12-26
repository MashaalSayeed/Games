"""
Utility widget classes for Pygame GUIs
- Frames
- Labels
- Buttons
"""

import pygame


class Widget:
    def __init__(self, parent=None, pos=(0,0), size=(0,0), center=False, disabled=False):
        self.parent = parent
        self.pos = pos
        self.size = size
        self.center = center
        self.disabled = disabled

        if parent:
            parent.children.append(self)
        self.surface = self.create_surface()

    def create_surface(self):
        pass

    def collidepoint(self, pos):
        x, y = self.pos
        w, h = self.size
        return x <= pos[0] <= x + w and y <= pos[1] <= y + h

    def draw(self, surface):
        if not self.center:
            pos = self.pos
        else:
            w1, h1 = self.surface.get_size() 
            w2, h2 = surface.get_size()
            pos = self.pos = (w2-w1)//2, (h2-h1)//2
        surface.blit(self.surface, pos)



class Frame(Widget):
    def __init__(self, pos, size, bgcolor=None, image=None, bordercolor=None, border=0, transparency=0, **kwargs):
        self.bgcolor = bgcolor
        self.image = image
        self.bordercolor = bordercolor
        self.border = border
        self.transparency = transparency
        self.children = []

        super().__init__(pos=pos, size=size, **kwargs)
    
    def create_surface(self):
        surface = pygame.Surface(self.size)
        if self.bordercolor:
            surface.fill(self.bordercolor)

        bd = self.border
        if self.bgcolor:
            surface.fill(self.bgcolor, ((bd,bd), (self.size[0]-bd*2, self.size[1]-bd*2)))
        
        if self.image:
            surface.blit(self.image, ((bd,bd), (self.ize[0]-bd*2, self.size[1]-bd*2)))
        
        surface.set_alpha(255 - self.transparency)
        return surface

    def draw(self, surface):
        for c in self.children:
            c.draw(self.surface)
        super().draw(surface)


class Label(Widget):
    def __init__(self, font=None, text="", fgcolor=(0,0,0), **kwargs):
        self.text = text
        self.font = font or pygame.font.get_default_font()
        self.fgcolor = fgcolor

        super().__init__(**kwargs)
        self.size = kwargs.get('size', self.font.size(self.text))

    def create_surface(self):
        return self.font.render(self.text, False, self.fgcolor)


class Button(Label):
    def __init__(self, command=None, **kwargs):
        self.command = command
        super().__init__(**kwargs)

    def draw(self, surface):
        pos = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        if self.collidepoint(pos) and click[0] == 1:
            if self.command:
                self.command(self)
        
        super().draw(surface)



if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((500, 500))
    clock = pygame.time.Clock()

    font = pygame.font.SysFont('Arial', 20)

    bg = Frame((0,0), (250,500), bgcolor=(255,0,0), border=10)
    Button(parent=bg, size=(250,500), command=print, center=True, font=font, fgcolor=(255,255,255), text="hello world this is me")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        
        screen.fill((255,255,255))
        bg.draw(screen)
        
        pygame.display.flip()
        clock.tick(30)

