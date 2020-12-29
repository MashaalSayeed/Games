import random

from itertools import product
from copy import deepcopy


EMPTY = ''


class Board:
    def __init__(self):
        self.board = [[EMPTY] * 9 for _ in range(9)]
        self.solution = None

    def get_valid_numbers(self, i, j):
        if self.board[i][j] != EMPTY:
            return {self.board[i][j]}

        valid = set(range(1,10))
        valid.difference_update(
            set(self.board[i]),
            {r[j] for r in self.board},
            {self.board[x][y] for x in range(9) for y in range(9) if x//3 == i//3 and y//3 == j//3}
        )
        
        return valid

    def fill_block(self, i, j):
        valid = self.get_valid_numbers(i, j)
        if len(valid) == 0:
            return False, None

        self.board[i][j] = random.choice(list(valid))
        if i == j == 8:
            return True, self.board

        # Get the next cell indexes
        ni, nj = i+(j+1)//9, (j+1)%9
        check, new_board = self.fill_block(ni, nj)
        while not check:
            valid.discard(self.board[i][j])
            if len(valid) == 0:
                self.board[i][j] = EMPTY
                return False, None
            
            self.board[i][j] = random.choice(list(valid))
            check, new_board = self.fill_block(ni, nj)

        return check, new_board

    def generate_puzzle(self):
        self.board = [[EMPTY] * 9 for _ in range(9)]
        self.board = self.fill_block(0, 0)[1]
        self.solution = deepcopy(self.board)

        remove = random.sample(list(product(range(9), repeat=2)), 49) # remove 64 blocks, 17 remain
        for i, j in remove:
            self.board[i][j] = EMPTY
        return self.board

    def solve(self):
        for i in range(9):
            for j in range(9):
                if board[i][j] == EMPTY:
                    self.solution = self.fill_block(i, j)[1]
                    return self.solution

    def print_board(self):
        print("╔═══╤═══╤═══╦═══╤═══╤═══╦═══╤═══╤═══╗")
        for i in range(9):
            print("║", end='')
            for j in range(9):
                end = "║" if j % 3 == 2 else "│"
                print(f" {self.board[i][j]} ", end=end)
            
            if i == 8:
                print("\n╚═══╧═══╧═══╩═══╧═══╧═══╩═══╧═══╧═══╝")
            elif i % 3 == 2:
                print("\n╠═══╪═══╪═══╬═══╪═══╪═══╬═══╪═══╪═══╣")
            else:
                print("\n╟───┼───┼───╫───┼───┼───╫───┼───┼───╢")

