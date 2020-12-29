import tkinter as tk
from tkinter import ttk
import time

import sudoku


FONT1 = ('Arial Black', 20)
FONT2 = ('Arial', 15)


class MainWindow(tk.Tk):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.board = sudoku.Board()
        self.entries = []

        self.title('Sudoku')
        self.geometry('501x425')
        self.resizable(False, False)
        self.create_widgets()

        self.new_game()

    def create_widgets(self):
        tk.Label(self, text='SUDOKU', font=FONT1).pack(fill='x')
        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=10, pady=10)

        tk.Frame().pack()
        sudoku_frame = tk.Frame(self, bg='black', width=1)
        sudoku_frame.pack(fill='both', padx=80, ipady=1)

        vcmd = (self.register(self.validate_input), '%P')
        for i in range(9):
            self.entries.append([])
            for j in range(9):
                padx = (2,0) if j%3 == 0 else 0
                pady = (2,0) if i%3 == 0 else 0
                entry = tk.Entry(
                    sudoku_frame, font=FONT2, justify='center',
                    width=3, validate='all', validatecommand=vcmd
                )

                self.entries[i].append(entry)
                entry.grid(row=i, column=j, sticky='nsew', ipady=2, padx=padx, pady=pady)
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill='x', expand=True, padx=80, pady=10)
        tk.Button(btn_frame, text='Clear', font=FONT2, bg='red', fg='white', command=self.reset).pack(side='left', fill='both', expand=True, padx=5)
        tk.Button(btn_frame, text='New Game', font=FONT2, bg='green', fg='white', command=self.new_game).pack(side='left', fill='both', expand=True, padx=5)
        tk.Button(btn_frame, text='Solve', font=FONT2, bg='blue', fg='white', command=self.solve).pack(side='right', fill='both', expand=True, padx=5)

    def validate_input(self, value):
        if len(value) <= 1 and value != '0' and (value.isdigit() or value.strip() == ''):
            return True
        else:
            return False

    def reset(self):
        for i in range(9):
            for j in range(9):
                value = self.board.board[i][j]
                entry = self.entries[i][j]
                entry.configure(state='normal')

                entry.delete('0', 'end')
                entry.insert('0', value)

                if value != '':
                    entry.configure(state='readonly')                

    def new_game(self):
        self.board.generate_puzzle()
        self.reset()

    def solve(self):
        for i in range(9):
            for j in range(9):
                entry = self.entries[i][j]
                sol = self.board.solution[i][j]
    
                if entry != sol:
                    self.update()
                    time.sleep(0.01)
                    entry.delete('0', 'end')
                    entry.insert('0', sol)


if __name__ == "__main__":
    gui = MainWindow()
    gui.mainloop()