import random
import time
import tkinter as tk
from tkinter import ttk


FONT1 = ('Arial Black', 20)
FONT2 = ('Arial Black', 14)
FONT3 = ('Arial', 10)

PLAYERS = [(None, ' '), ('#036bfc', 'X'), ('#fc2c03', 'O')]


def check_win(state, player):
    positions = [
        (0,1,2), (0,3,6),
        (3,4,5), (1,4,7),
        (6,7,8), (2,5,8),
        (0,4,8), (2,4,6)
    ]
    for p1, p2, p3 in positions:
        if state[p1] == state[p2] == state[p3] == player:
            return True
    return False


def evaluate(state):
    score = 0
    if check_win(state, 1):
        score = -1
    elif check_win(state, -1):
        score = 1
    return score


def minimax(state, player, depth):
    "Returns best position and score"
    if check_win(state, 1):
        return [10, -1]
    elif check_win(state, -1):
        return [10, 1]
    elif depth == 0 or all(state):
        return [10, 0]

    best = 100 if player == 1 else -100
    best_moves = []
    for m in range(9):
        if state[m]:
            continue

        copy = state[:]
        copy[m] = player
        score = minimax(copy, -player, depth-1)
        score[0] = m
        # Maximize score if computer else minimize
        if (player == 1 and score[1] < best) or (player == -1 and score[1] > best):
            best = score[1]
            best_moves = [m]
        elif score[1] == best:
            best_moves.append(m)
    best_move = random.choice(best_moves)
    return [best_move, best]



class Game():
    def __init__(self):
        self.board = [0] * 9 # 0 = empty, 1 = X, -1 = O
        self.turn = random.choice((-1, 1))
        self.winner = self.tie = None

    def move(self, move):
        if self.board[move] or self.winner or self.tie:
            return False

        self.board[move] = self.turn
        if check_win(self.board, self.turn):
            self.winner = self.turn
        elif all(self.board):
            self.tie = True
        self.turn = -self.turn
        return True
    
    def computer_move(self, difficulty):
        depth = self.board.count(0)
        if difficulty == 'Easy':
            return random.choice([x for x in range(9) if not self.board[x]])
        elif difficulty == 'Hard':
            move = minimax(self.board, self.turn, min(5, depth))
            return move[0]
        else:
            if depth == 9:
                return random.choice(range(9))
            move = minimax(self.board, self.turn, depth)
            return move[0]


class MainWindow(tk.Tk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.title('Tictactoe')
        self.geometry('600x400')

        self.computer = tk.BooleanVar(value=True)
        self.difficulty = tk.StringVar(value='Easy')
        self.message = tk.StringVar(value='Player 1 (X)\'s Turn')
        self.buttons = []

        self.create_widgets()
        self.restart()
    
    def create_widgets(self):
        tk.Label(self, text='TICTACTOE', font=FONT1).grid(columnspan=2, sticky='nsew')
        ttk.Separator(self, orient='horizontal').grid(row=1, columnspan=2, sticky='nsew', padx=10)

        side_frame = tk.Frame(self, width=200)
        side_frame.grid(row=2, sticky='nsew')
        menu_frame = tk.LabelFrame(side_frame, text='Menu', font=FONT2)
        menu_frame.pack(padx=10, pady=10, fill='both')

        tk.Radiobutton(menu_frame, text='Computer', variable=self.computer, value=True,font=FONT3).pack(anchor='w')
        tk.Radiobutton(menu_frame, text='Human', variable=self.computer, value=False, font=FONT3).pack(anchor='w')

        tk.Label(menu_frame, text='Difficulty', font=FONT3).pack(side='left')
        tk.OptionMenu(menu_frame, self.difficulty, 'Easy', 'Hard', 'Impossible').pack(side='left', padx=10)

        tk.Label(side_frame, textvariable=self.message, font=FONT2, wraplength=150, height=4, bd=4, relief=tk.GROOVE).pack(padx=10, fill='both')
        self.restartbtn = tk.Button(side_frame, text='Restart', font=FONT2, bg='green', fg='white', command=self.restart)
        
        board_frame = tk.Frame(self)
        board_frame.grid(row=2, column=1, sticky='nsew', padx=10, pady=10)
        for i in range(3):
            for j in range(3):
                btn = tk.Button(board_frame, text='', font=FONT1, width=100, command=lambda x=i*3+j: self.human_move(x))
                btn.grid(row=i, column=j, sticky='nsew')
                self.buttons.append(btn)
        [board_frame.columnconfigure(i, weight=1) for i in range(3)]
        [board_frame.rowconfigure(i, weight=1) for i in range(3)]

        self.columnconfigure(0, weight=1, minsize=200)
        self.columnconfigure(1, weight=6)
        self.rowconfigure(2, weight=1)

    def move(self, m):
        bg, text = PLAYERS[self.game.turn]
        if not self.game.move(m):
            return
        self.buttons[m].configure(text=text, bg=bg)
        self.display_message()
        if self.game.winner or self.game.tie:
            self.restartbtn.pack(padx=10, pady=10, fill='x')
        elif self.computer.get() and self.game.turn == -1:
            self.computer_move()

    def human_move(self, m):
        if self.computer.get() and self.game.turn == -1:
            return
        self.move(m)

    def computer_move(self):
        m = self.game.computer_move(self.difficulty.get())
        self.move(m)
    
    def display_message(self):
        if self.game.winner:
            p = 1 if self.game.winner == 1 else 2
            self.message.set(f'Player {p} ({PLAYERS[p][1]}) Has WON!!')
        elif self.game.tie:
            self.message.set('TIE!!')
        else:
            p = 1 if self.game.turn == 1 else 2
            self.message.set(f'Player {p} ({PLAYERS[p][1]})\'s Turn')

    def restart(self):
        [b.configure(bg=self.cget('bg'), text=' ') for b in self.buttons]
        self.game = Game()
        self.display_message()

        if self.computer.get() and self.game.turn == -1:
            self.computer_move()


if __name__ == "__main__":
    gui = MainWindow()
    gui.mainloop()
