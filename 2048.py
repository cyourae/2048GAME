board = [
    [0,0,0,0],
    [0,2,0,0],
    [0,2,4,0],
    [0,0,0,0]
]

import random

SIZE = 4

def create_board():
    return [[0 for _ in range(SIZE)] for _ in range(SIZE)]

def add_random_tile(board):
    empty_cells = []

    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0:
                empty_cells.append((r, c))

    if not empty_cells:
        return board

    r, c = random.choice(empty_cells)
    board[r][c] = 2 if random.random() < 0.9 else 4
    return board

def print_board(board, score):
    print("Score:", score)
    for row in board:
        print(row)
    print()

def move_row_left(row):
    new_row = [x for x in row if x != 0]

    result = []
    score = 0
    i = 0

    while i < len(new_row):
        if i + 1 < len(new_row) and new_row[i] == new_row[i + 1]:
            merged = new_row[i] * 2
            result.append(merged)
            score += merged
            i += 2
        else:
            result.append(new_row[i])
            i += 1

    while len(result) < SIZE:
        result.append(0)

    return result, score

def move_left(board):
    new_board = []
    total_score = 0

    for row in board:
        new_row, score = move_row_left(row)
        new_board.append(new_row)
        total_score += score

    return new_board, total_score

def reverse_board(board):
    return [row[::-1] for row in board]

def transpose(board):
    return [list(row) for row in zip(*board)]

def move_right(board):
    reversed_board = reverse_board(board)
    moved_board, score = move_left(reversed_board)
    final_board = reverse_board(moved_board)
    return final_board, score

def move_up(board):
    transposed = transpose(board)
    moved_board, score = move_left(transposed)
    final_board = transpose(moved_board)
    return final_board, score

def move_down(board):
    transposed = transpose(board)
    moved_board, score = move_right(transposed)
    final_board = transpose(moved_board)
    return final_board, score

def boards_equal(board1, board2):
    return board1 == board2

def can_move(board):
    if any(0 in row for row in board):
        return True

    for move in [move_left, move_right, move_up, move_down]:
        new_board, _ = move(board)
        if new_board != board:
            return True

    return False

import time

moves = {
    "w": move_up,
    "s": move_down,
    "a": move_left,
    "d": move_right
}
def count_empty(board):
    count = 0
    for row in board:
        count += row.count(0)
    return count

def max_tile(board):
    return max(max(row) for row in board)

def smoothness(board):
    penalty = 0

    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0:
                continue

            if c + 1 < SIZE and board[r][c + 1] != 0:
                penalty += abs(board[r][c] - board[r][c + 1])

            if r + 1 < SIZE and board[r + 1][c] != 0:
                penalty += abs(board[r][c] - board[r + 1][c])

    return -penalty


def corner_bonus(board):
    biggest = max_tile(board)

    corners = [
        board[0][0],
        board[0][3],
        board[3][0],
        board[3][3]
    ]

    if biggest in corners:
        return biggest * 10

    return 0


def monotonicity(board):
    score = 0

    # reward decreasing order from left to right
    for row in board:
        for i in range(SIZE - 1):
            if row[i] >= row[i + 1]:
                score += row[i]

    # reward decreasing order from top to bottom
    for c in range(SIZE):
        for r in range(SIZE - 1):
            if board[r][c] >= board[r + 1][c]:
                score += board[r][c]

    return score


def evaluate(board):
    empty = count_empty(board)
    biggest = max_tile(board)

    return (
        empty * 1000
        + biggest * 2
        + smoothness(board) * 0.1
        + corner_bonus(board)
        + monotonicity(board) * 1
    )

def search_score(board, depth):
    if depth == 0 or not can_move(board):
        return evaluate(board)

    best_score = -999999999

    for key, move_function in moves.items():
        new_board, gained = move_function(board)

        if new_board == board:
            continue

        score = search_score(new_board, depth - 1)

        if score > best_score:
            best_score = score

    return best_score

def ai_move(board, depth=3):
    best_score = -999999999
    best_move = None

    for key, move_function in moves.items():
        new_board, gained = move_function(board)

        if new_board == board:
            continue

        score = search_score(new_board, depth - 1)

        if score > best_score:
            best_score = score
            best_move = key

    return best_move

def play_game(show=False):
    board = create_board()
    add_random_tile(board)
    add_random_tile(board)

    score = 0
    steps = 0

    while can_move(board):
        if show:
            print_board(board, score)

        command = ai_move(board, depth=4)

        if command is None:
            break

        if command == "a":
            new_board, gained = move_left(board)
        elif command == "d":
            new_board, gained = move_right(board)
        elif command == "w":
            new_board, gained = move_up(board)
        elif command == "s":
            new_board, gained = move_down(board)

        if new_board != board:
            board = new_board
            score += gained
            steps += 1
            add_random_tile(board)

    return score, max_tile(board), steps
def run_experiments(n=100):

    scores = []
    max_tiles = []
    steps_list = []

    for i in range(n):

        score, tile, steps = play_game(show=False)

        scores.append(score)
        max_tiles.append(tile)
        steps_list.append(steps)

        print(f"Game {i+1}: Score={score}, MaxTile={tile}")

    print("\n===== RESULTS =====")
    print("Games:", n)
    print("Average Score:", sum(scores)/n)
    print("Best Score:", max(scores))
    print("Average Max Tile:", sum(max_tiles)/n)
    print("Best Max Tile:", max(max_tiles))
    print("Average Steps:", sum(steps_list)/n)

run_experiments(100)
