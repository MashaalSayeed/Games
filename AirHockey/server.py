import socket
import selectors
import time

import pygame

from sprites import Ball, BaseGame
from constants import *
from socketclient import SocketClient


class Game(BaseGame):
    def __init__(self, server, client1, client2):
        super().__init__()
        self.server = server
        self.player1, self.player2 = client1, client2
        self.board_rect = pygame.Rect(0, 50, SCREENX, SCREENY-50)
        self.ball = Ball(self, *self.board_rect.center)

        self.player1.set_side(self, 'TOP')
        self.player2.set_side(self, 'DOWN')
    
    def score_goal(self):
        super().score_goal()
        self.player1.send('GOAL', {'scores': self.scores[::-1]})
        self.player2.send('GOAL', {'scores': self.scores})
        self.send_winner()

    def send_winner(self):
        if self.winner:
            for player in (self.player1, self.player2):
                # idk why != works
                player.send('GAME_OVER', {'winner': self.winner.side != player.side})
            self.close()
    
    def reset(self):
        self.player1.set_side(self, 'TOP')
        self.player2.set_side(self, 'DOWN')
        self.ball.reset()
        self.goal = False

    def update(self):
        if self.goal:
            if time.time() - self.time_of_goal >= GOAL_TEXT_DELAY:
                self.reset()
            return

        self.player1.update()
        self.player2.update()
        self.ball.update()
        self.tick = self.clock.tick(60)
    
    def close(self):
        self.server.games.remove(self)
        [p.reset() for p in (self.player1, self.player2)]


class SocketPlayer(SocketClient):
    def __init__(self, server, selector, sock, address):
        super().__init__(selector, sock, address)
        self.server = server
        self.reset()
    
    def reset(self):
        self.game = self.rect = self.side = None
        self.velocity = pygame.math.Vector2()

    def set_side(self, game, side):
        self.game = game
        self.side = side
        y = SCREENY//4 + 50 if side == 'TOP' else 3 * SCREENY//4

        self.rect = pygame.Rect(0, 0, PLAYER_RADIUS, PLAYER_RADIUS)
        self.rect.center = SCREENX//2, y
        self.send('PLAYER_POS', {'rect': self.resolve_side(self.rect.center)})
    
    def resolve_side(self, pos):
        if self.side == 'DOWN':
            return pos

        center = self.game.board_rect.center
        dx, dy = pos[0] - center[0], pos[1] - center[1]
        return center[0] - dx, center[1] - dy

    def update(self):
        opponent = self.game.player2 if self == self.game.player1 else self.game.player1
        self.send('GAME_UPDATE', {
            'ball': self.resolve_side(self.game.ball.rect.center),
            'opponent': self.resolve_side(opponent.rect.center)
        })

    def close(self):
        if self.game:
            self.game.winner = self
            self.game.close()
        if self in self.server.waiting:
            self.server.waiting.remove(self)
        super().close()
    
    def handle_request(self, data):
        header, body = data['header'], data['body']
        if header == 'JOIN_GAME':
            self.server.find_game(self)
        elif header == 'PLAYER_MOVE' and self.game:
            self.rect.center = self.resolve_side(body['rect'])
            self.velocity = pygame.math.Vector2(body['velocity'])
            self.velocity = -self.velocity if self.side == 'TOP' else self.velocity


class SocketServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))

        self.clients = set()
        self.waiting = []
        self.games = []
    
    def find_game(self, client):
        if not self.waiting:
            self.waiting.append(client)
        else:
            opponent = self.waiting.pop(0)
            game = Game(self, client, opponent)
            print(f'New game created')
            self.games.append(game)
            return game

    def accept(self):
        sock, address = self.sock.accept()
        client = SocketPlayer(self, sel, sock, address)
        self.clients.add(client)
        print(f'Connected to client: {address}')

    def listen(self):
        print(f"Listening to port {self.port}")
        self.sock.listen()
        self.sock.setblocking(False)
        sel.register(self.sock, selectors.EVENT_READ, data=None)

        try:
            while True:
                for game in self.games:
                    game.update()

                events = sel.select(timeout=1)
                for key, mask in events:
                    if key.data is None:
                        self.accept()
                    else:
                        client = key.data
                        try:
                            client.process_event(mask)
                        except Exception as e:
                            print("Client exception caught:", e)
                            client.close()
                            self.clients.remove(client)
        except (KeyboardInterrupt, SystemExit):
            print("Got keyboard interrupt, Exiting...")
        except Exception as e:
            print('Server exception caught:', e)
        finally:
            sel.close()
            [c.close() for c in self.clients]
            self.sock.close()


if __name__ == "__main__":
    sel = selectors.DefaultSelector()
    SocketServer(host='', port=22222).listen()