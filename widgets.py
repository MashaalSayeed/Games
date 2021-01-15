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
            self.cpos = self.pos[0] + self.parent.cpos[0], self.pos[1] + self.parent.cpos[1]
        else:
            self.cpos = self.pos
        self.surface = self.create_surface()

    def create_surface(self):
        pass

    def config(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def collidepoint(self, pos):
        x, y = self.cpos
        w, h = self.parent.size
        return x <= pos[0] <= x + w and y <= pos[1] <= y + h

    def draw(self, surface):
        self.surface = self.create_surface()
        self.update_surface(surface)

        if not self.center:
            pos = self.pos
        else:
            w1, h1 = self.surface.get_size() 
            w2, h2 = surface.get_size()
            pos = self.pos = (w2-w1)//2, (h2-h1)//2
        surface.blit(self.surface, pos)

    def update_surface(self, surface):
        pass


class Frame(Widget):
    def __init__(self, pos, size, bgcolor=None, image=None, bordercolor=None, border=0, transparency=0, **kwargs):
        self.bgcolor = bgcolor
        self.image = image
        self.bordercolor = bordercolor
        self.border = border
        self.transparency = transparency
        self.children = []

        if kwargs.get('parent') and not self.bgcolor:
            self.bgcolor = kwargs.get('parent').bgcolor
            print(self)

        super().__init__(pos=pos, size=size, **kwargs)
    
    def create_surface(self):
        surface = pygame.Surface(self.size)
        if self.bordercolor:
            surface.fill(self.bordercolor)

        bd = self.border
        if self.bgcolor:
            surface.fill(self.bgcolor, ((bd,bd), (self.size[0]-bd*2, self.size[1]-bd*2)))
        
        if self.image:
            surface.blit(self.image, ((bd,bd), (self.size[0]-bd*2, self.size[1]-bd*2)))
        
        surface.set_alpha(255 - self.transparency)
        return surface

    def update_surface(self, surface):
        for c in self.children:
            c.draw(self.surface)


class Label(Widget):
    def __init__(self, font=None, text="", fgcolor=(0,0,0), **kwargs):
        self.text = text
        self.font = font or pygame.font.SysFont("Clear Sans", 35)
        self.fgcolor = fgcolor

        super().__init__(**kwargs)
        self.size = kwargs.get('size', self.font.size(self.text))

    def create_surface(self):
        return self.font.render(self.text, False, self.fgcolor)


class Button(Label):
    def __init__(self, command=None, **kwargs):
        self.command = command
        super().__init__(**kwargs)

    def update_surface(self, surface):
        pos = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        if self.collidepoint(pos) and click[0] == 1:
            if self.command:
                self.command(self)



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

