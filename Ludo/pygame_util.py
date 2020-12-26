'''
Pygame Utility module for ease of creation UI tools
- Frames
- Labels
- Buttons
'''

import pygame


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


class Label(object):
    hover_surface = pressed_surface = None
    
    def __init__(self, rect, image=None, text='', fgcolor=WHITE, font=None, bgcolor=None, border=0, bordercolor=BLACK,
                 transparency=0):
        super().__init__()

        self.rect = self._rect = pygame.Rect(rect)
        
        self.image = image
        self.text = text
        self.fgcolor = fgcolor
        self.font = font or pygame.font.SysFont('Arial', 20)
        self.bgcolor = bgcolor
        self.border = border
        self.bordercolor = bordercolor
        self.transparency = transparency

        self.surface = self.create_surface(self.bgcolor)

    def create_surface(self, color):
        if self.border:
            self._rect = pygame.Rect([-self.border, -self.border, self.rect[2] + 2*self.border, self.rect[3] + 2*self.border])
            
        surface = pygame.Surface(self._rect[2:])
        if self.border:
            surface.fill(self.bordercolor)

        if color:
            pygame.draw.rect(surface, color, (self.border, self.border, *self.rect[2:]))
        else:
            surface.set_colorkey(BLACK) 

        if self.image:
            imagerect = self.image.get_rect()
            surface.blit(self.image, (self._rect.width/2 - imagerect.width/2, self._rect.height/2 - imagerect.height/2))

        if self.text:
            textbox = self.font.render(self.text, True, self.fgcolor)
            textrect = textbox.get_rect()
            surface.blit(textbox, (self._rect.width/2 - textrect.width/2, self._rect.height/2 - textrect.height/2))

        surface.set_alpha(255 - self.transparency)
        return surface

    def config(self, **kwargs):
        self.rect = kwargs.get('rect', self.rect)
        
        self.image = kwargs.get('image', self.image)
        self.text = kwargs.get('text', self.text)
        self.fgcolor = kwargs.get('fgcolor', self.fgcolor)
        self.font = kwargs.get('font', self.font)
        self.bgcolor = kwargs.get('bgcolor', self.bgcolor)
        self.border = kwargs.get('border', self.border)
        self.bordercolor = kwargs.get('bordercolor', self.bordercolor)
        self.transparency = kwargs.get('transparency', self.transparency)

        self.surface = self.create_surface(self.bgcolor) 

    def draw(self, screen, center=False, pos=None, surface=None):
        if center:
            pos = (screen.get_width()/2 - self._rect.width/2, screen.get_height()/2 - self._rect.height/2)
        elif not pos:
            pos = self.rect[:2]

        #self._rect[:2] = screen
        screen.blit(surface or self.surface, pos)


class Button(Label):
    def __init__(self, rect, command=None, hovercolor=None, pressedcolor=None, disabled=False, **kwargs):
        super().__init__(rect, **kwargs)

        self.command = command
        self.hovercolor = hovercolor
        self.pressedcolor = pressedcolor
        self.disabled = disabled
        
        if self.hovercolor:
            self.hover_surface = self.create_surface(self.hovercolor)

        if self.pressedcolor:
            self.pressed_surface = self.create_surface(self.pressedcolor)

        self.disabled_surface = self.surface.copy()
        self.disabled_surface.blit(Frame((0,0,*self._rect[2:]), bgcolor=(120,100,120), transparency=120).surface, (0,0))

    def config(self, **kwargs):
        super().config(**kwargs)

        self.hovercolor = kwargs.get('hovercolor', self.hovercolor)
        self.pressedcolor = kwargs.get('pressedcolor', self.pressedcolor)
        self.disabled = kwargs.get('disabled', self.disabled)
        
        if self.hovercolor:
            self.hover_surface = self.create_surface(self.hovercolor)

        if self.pressedcolor:
            self.pressed_surface = self.create_surface(self.pressedcolor)

        self.disabled_surface = self.surface.copy()
        self.disabled_surface.blit(Frame((0,0,*self._rect[2:]), bgcolor=(120,100,120), transparency=120).surface, (0,0))

    def draw(self, screen, disabled=False, **kwargs):
        pos = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        surface = self.surface

        if disabled or self.disabled:
            surface = self.disabled_surface
        else:
            if isinstance(screen, Frame):
                rect = screen._rect
                screen = screen.surface
            else:
                rect = screen.get_rect()

            if self.rect.collidepoint((pos[0] - rect[0], pos[1] - rect[1])):
                if click[0] == 1:
                    surface = self.pressed_surface
                    if self.command:
                        self.command(self)
                else:
                    surface = self.hover_surface

        super().draw(screen, surface=surface, **kwargs)


class Frame(object):
    def __init__(self, rect, bgcolor=None, border=0, bordercolor=BLACK, transparency=0):
        super().__init__()
        
        self.rect = self._rect = pygame.Rect(rect)
        self.bgcolor = bgcolor
        self.border = border
        self.bordercolor = bordercolor
        self.transparency = transparency

        self.surface = self.create_surface()

    def create_surface(self): 
        if self.border:
            self._rect = pygame.Rect([-self.border, -self.border, self.rect[2] + 2*self.border, self.rect[3] + 2*self.border])

        surface = pygame.Surface(self._rect[2:])
        if self.border:
            surface.fill(self.bordercolor)

        if self.bgcolor:
            pygame.draw.rect(surface, self.bgcolor, (self.border, self.border, *self.rect[2:]))
        else:
            surface.set_colorkey(BLACK)

        surface.set_alpha(255 - self.transparency)
        return surface

    def draw(self, screen, center=False, pos=None, surface=None):
        if center:
            pos = (screen.get_width()/2 - self._rect.width/2, screen.get_height()/2 - self._rect.height/2)
        elif not pos:
            pos = self.rect[:2]

        self._rect[:2] = pos
        screen.blit(surface or self.surface, pos)


class MessageBox(Frame):
    disabled = False
    
    def __init__(self, rect, title, message, ok_command=None, **kwargs):
        super().__init__(rect, bgcolor=(100,100,200), **kwargs)

        self.title = title
        self.message = message
        self.ok_command = ok_command
        
        self.surface = self._create_surface()

    def _create_surface(self):
        x,y,w,h = self.rect
        
        title = Label((0,0, w*0.75, h*0.25), text=self.title, fgcolor=(255,255,255), bgcolor=(50,50,200))
        message = Label((0, h*0.25, w, h*0.55), fgcolor=(0,0,0), bgcolor=(255,255,255), text=self.message)

        self.x_btn = Button((x+w*0.75,y, w*0.25, h*0.25), text='X', bgcolor=(200,0,0), hovercolor=(220,50,50), command=self.disable)

        self.ok_btn = Button((x+w*0.1, y+h*0.75, w*0.3, h*0.2),
                             text='OK', bgcolor=(140,120,140), hovercolor=(0,0,0), command=self.ok_command)

        self.cancel_btn = Button((x+w*0.6, y+h*0.75, w*0.3, h*0.2),
                                 text='Cancel', bgcolor=(140,120,140), hovercolor=(0,0,0), command=self.disable)

        self.surface.blit(title.surface, (0,0))
        self.surface.blit(message.surface, (0, h*0.25))

        pygame.draw.rect(self.surface, (200,200,200), (0, h*0.7, w, h*0.30))
        return self.surface

    def disable(self, __=None):
        self.disabled = True

    def draw(self, screen, **kwargs):
        if not self.disabled:
            super().draw(screen, **kwargs)
            
            self.ok_btn.draw(screen)
            self.cancel_btn.draw(screen)
            self.x_btn.draw(screen)



"""
pygame.init()
screen = pygame.display.set_mode((500, 500))
clock = pygame.time.Clock()

#frame = Frame((50,50,400,400), bgcolor=(255,255,255), border=5)
btn = Button((100,50,200,50), text='helo', hovercolor=(255,255,0), disabled=True,
             bgcolor=(200,0,20), command=lambda self: self.config(text='sure'))

def func(__):
    box.disable()
    btn.config(disabled=False)

box = MessageBox((100,150,300,200), "Warning", "dont go ahead... please", ok_command=func)


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            break

    screen.fill((0, 200, 0))
    box.draw(screen)
    btn.draw(screen)
    
    pygame.display.flip()
    clock.tick(30)
"""
