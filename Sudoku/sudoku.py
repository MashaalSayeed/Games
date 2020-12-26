import random
from itertools import product
from copy import deepcopy
import time

import tkinter


counter = 0
def fill_block(grid, i, j):
    global counter
    counter += 1
    if grid[i][j] != ' ':
        valid = {grid[i][j]}
    else:
        valid = set(range(1,10)) - set(grid[i]) - {r[j] for r in grid} - {grid[x][y] for x in range(9) for y in range(9) if x//3 == i//3 and y//3 == j//3}
    if len(valid) == 0:
        return False, None
    
    if j == 8:
        ni, nj = i+1, 0
    else:
        ni, nj = i, j+1

    grid[i][j] = random.choice(list(valid))
    if i == j == 8:
        return True, grid

    check, new_grid = fill_block(deepcopy(grid), ni, nj)
    while not check:
        valid.discard(grid[i][j])
        if len(valid) == 0:
            return False, None
        
        grid[i][j] = random.choice(list(valid))
        check, new_grid = fill_block(deepcopy(grid), ni, nj)

    return check, new_grid


def generate_puzzle():
    start = time.time()
    # randomize initial row
    grid = [random.sample(range(1,10), 9)] + [[' '] * 9 for _ in range(8)]
    grid = fill_block(grid, 1, 0)[1]

    end = time.time()
    print("Time taken:", round(end-start, 3), "seconds")

    print_grid(grid)
    print()
    remove = random.sample(list(product(range(9), repeat=2)), 64) # remove 64 blocks, 17 remain
    for i, j in remove:
        grid[i][j] = ' '
    return grid


def solver(grid):
    for i in range(9):
        for j in range(9):
            if grid[i][j] == ' ':
                return fill_block(grid, i, j)[1]


def print_grid(grid):
    print("╔═══╤═══╤═══╦═══╤═══╤═══╦═══╤═══╤═══╗")
    for i in range(9):
        print("║", end='')
        for j in range(9):
            end = "║" if j % 3 == 2 else "│"
            print(f" {grid[i][j]} ", end=end)
        
        if i == 8:
            print("\n╚═══╧═══╧═══╩═══╧═══╧═══╩═══╧═══╧═══╝")
        elif i % 3 == 2:
            print("\n╠═══╪═══╪═══╬═══╪═══╪═══╬═══╪═══╪═══╣")
        else:
            print("\n╟───┼───┼───╫───┼───┼───╫───┼───┼───╢")


grid = generate_puzzle()
print_grid(grid)
print(counter)
counter = 0
solved = solver(grid)
print_grid(solved)
print(counter)
