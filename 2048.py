import argparse
import json
import random
from pathlib import Path

SIZE = 4

DEFAULT_WEIGHTS = {
    "empty": 2200,
    "biggest": 3,
    "smooth": 0.3,
    "corner": 8,
    "mono": 3
}

WEIGHTS_FILE = Path(__file__).with_name("best_weights.json")
weights = DEFAULT_WEIGHTS.copy()

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


def load_weights(path=WEIGHTS_FILE):
    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
    except FileNotFoundError:
        return DEFAULT_WEIGHTS.copy()

    result = DEFAULT_WEIGHTS.copy()
    for key in result:
        if key in loaded:
            result[key] = float(loaded[key])
    return result


def save_weights(best_weights, path=WEIGHTS_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(best_weights, f, indent=2)
        f.write("\n")


def set_weights(new_weights):
    weights.clear()
    weights.update(new_weights)


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


moves = {
    "w": move_up,
    "s": move_down,
    "a": move_left,
    "d": move_right
}


def can_move(board):
    if any(0 in row for row in board):
        return True

    for move_function in moves.values():
        new_board, _ = move_function(board)
        if new_board != board:
            return True

    return False


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

    if board[0][0] == biggest:
        return biggest * 20

    return 0

def corner_locked_bonus(board):
    biggest = max_tile(board)

    if biggest in [board[0][0], board[0][3], board[3][0], board[3][3]]:
        return biggest * 30

    return 0

def monotonicity(board):
    score = 0

    for row in board:
        for i in range(SIZE - 1):
            if row[i] >= row[i + 1]:
                score += row[i]

    for c in range(SIZE):
        for r in range(SIZE - 1):
            if board[r][c] >= board[r + 1][c]:
                score += board[r][c]

    return score

def evaluate(board, weights):
    empty = count_empty(board)
    biggest = max_tile(board)

    smooth = smoothness(board)
    corner = corner_bonus(board)
    locked = corner_locked_bonus(board)
    mono = monotonicity(board)

    high_tile_bonus = 0

    if biggest >= 1024:
        high_tile_bonus += biggest * 50

    if biggest >= 2048:
        high_tile_bonus += biggest * 200

    score = (
        empty * weights["empty"]
        + biggest * weights["biggest"]
        + smooth * weights["smooth"]
        + corner * weights["corner"]
        + locked
        + mono * weights["mono"]
        + high_tile_bonus
    )

    return score
 
def search_score(board, depth, weights):
    if depth == 0 or not can_move(board):
        return evaluate(board, weights)

    best_score = -999999999

    for key, move_function in moves.items():
        new_board, gained = move_function(board)

        if new_board == board:
            continue

        score = gained + search_score(new_board, depth - 1, weights)

        if score > best_score:
            best_score = score

    return best_score


def get_empty_cells(board):
    cells = []

    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0:
                cells.append((r, c))

    return cells


def copy_board(board):
    return [row[:] for row in board]


def expectimax(board, depth, is_player_turn):
    if depth == 0 or not can_move(board):
        return evaluate(board, weights)

    if is_player_turn:
        best_score = -999999999

        for key, move_function in moves.items():
            new_board, gained = move_function(board)

            if new_board == board:
                continue

            score = gained + expectimax(new_board, depth - 1, False)

            if score > best_score:
                best_score = score

        return best_score

    else:
        empty_cells = get_empty_cells(board)

        if not empty_cells:
            return evaluate(board, weights)

        total_score = 0

        for r, c in empty_cells:
            board_2 = copy_board(board)
            board_2[r][c] = 2
            total_score += 0.9 * expectimax(board_2, depth - 1, True)

            board_4 = copy_board(board)
            board_4[r][c] = 4
            total_score += 0.1 * expectimax(board_4, depth - 1, True)

        return total_score / len(empty_cells)


def ai_move(board, depth=3):
    best_score = -999999999
    best_move = None

    for key, move_function in moves.items():
        new_board, gained = move_function(board)

        if new_board == board:
            continue

        score = gained + expectimax(new_board, depth - 1, False)

        if score > best_score:
            best_score = score
            best_move = key

    return best_move

def choose_depth(board):
    biggest = max_tile(board)

    if biggest >= 1024:
        return 5
    elif biggest >= 512:
        return 4
    else:
        return 3
    
def play_game(show=False, depth=4, adaptive_depth=True, seed=None, strategy_weights=None):
    if seed is not None:
        random.seed(seed)

    if strategy_weights is not None:
        set_weights(strategy_weights)

    board = create_board()
    add_random_tile(board)
    add_random_tile(board)

    score = 0
    steps = 0

    while can_move(board):
        if show:
            print_board(board, score)

        current_depth = choose_depth(board) if adaptive_depth else depth

        command = ai_move(board, depth=current_depth)

        if command is None:
            break

        new_board, gained = moves[command](board)

        if new_board != board:
            board = new_board
            score += gained
            steps += 1
            add_random_tile(board)

    return score, max_tile(board), steps


def run_experiments(n=200, depth=4, adaptive_depth=True, strategy_weights=None):
    scores = []
    max_tiles = []
    steps_list = []
    tile_counts = {}

    for i in range(n):
        score, tile, steps = play_game(
            show=False,
            depth=depth,
            adaptive_depth=adaptive_depth,
            strategy_weights=strategy_weights,
        )

        scores.append(score)
        max_tiles.append(tile)
        steps_list.append(steps)

        if tile not in tile_counts:
            tile_counts[tile] = 0

        tile_counts[tile] += 1

        print(f"Game {i + 1}: Score={score}, MaxTile={tile}, Steps={steps}")

    print("\n===== RESULTS =====")
    print("Games:", n)
    print("Depth:", "adaptive" if adaptive_depth else depth)

    print("\nAverage Score:", sum(scores) / n)
    print("Best Score:", max(scores))

    print("\nAverage Max Tile:", sum(max_tiles) / n)
    print("Best Max Tile:", max(max_tiles))

    print("\nAverage Steps:", sum(steps_list) / n)

    print("\n===== TILE DISTRIBUTION =====")

    for tile in sorted(tile_counts.keys()):
        count = tile_counts[tile]
        percentage = (count / n) * 100
        print(f"{tile}: {count} games ({percentage:.2f}%)")


WEIGHT_RANGES = {
    "empty": (500, 6000),
    "biggest": (0, 20),
    "smooth": (0.0, 3.0),
    "corner": (0, 30),
    "mono": (0, 15),
}


def clamp(value, low, high):
    return max(low, min(high, value))


def random_weights():
    return {
        key: random.uniform(low, high)
        for key, (low, high) in WEIGHT_RANGES.items()
    }


def mutate(parent, mutation_rate=0.35, mutation_strength=0.25):
    child = parent.copy()

    for key, (low, high) in WEIGHT_RANGES.items():
        if random.random() < mutation_rate:
            span = high - low
            child[key] = clamp(
                child[key] + random.gauss(0, span * mutation_strength),
                low,
                high,
            )

    return child


def crossover(a, b):
    return {
        key: a[key] if random.random() < 0.5 else b[key]
        for key in WEIGHT_RANGES
    }


def evaluate_weights(candidate, seeds, depth=3, adaptive_depth=False):
    scores = []
    tiles = []
    steps_list = []

    for seed in seeds:
        score, tile, steps = play_game(
            show=False,
            depth=depth,
            adaptive_depth=adaptive_depth,
            seed=seed,
            strategy_weights=candidate,
        )
        scores.append(score)
        tiles.append(tile)
        steps_list.append(steps)

    avg_score = sum(scores) / len(scores)
    avg_tile = sum(tiles) / len(tiles)
    avg_steps = sum(steps_list) / len(steps_list)
    success_2048 = sum(1 for tile in tiles if tile >= 2048) / len(tiles)

    # Average score is the main objective. Tile size and survival time are small
    # auxiliary terms so the search prefers stable high-tile strategies.
    fitness = avg_score + avg_tile * 20 + avg_steps * 2 + success_2048 * 5000

    return {
        "fitness": fitness,
        "avg_score": avg_score,
        "avg_tile": avg_tile,
        "avg_steps": avg_steps,
        "best_score": max(scores),
        "best_tile": max(tiles),
        "success_2048": success_2048,
    }


def tournament_select(scored_population, k=3):
    candidates = random.sample(scored_population, k)
    candidates.sort(key=lambda item: item[0]["fitness"], reverse=True)
    return candidates[0][1]


def evolve_weights(
    generations=8,
    population_size=10,
    games_per_candidate=5,
    depth=3,
    adaptive_depth=False,
    elite_count=2,
    seed=42,
):
    random.seed(seed)

    population = [DEFAULT_WEIGHTS.copy()]
    while len(population) < population_size:
        population.append(random_weights())

    best_metrics = None
    best_candidate = None
    archive = [DEFAULT_WEIGHTS.copy()]

    for generation in range(1, generations + 1):
        seeds = [seed * 100000 + generation * 1000 + i for i in range(games_per_candidate)]
        scored_population = []

        for candidate in population:
            metrics = evaluate_weights(candidate, seeds, depth=depth, adaptive_depth=adaptive_depth)
            scored_population.append((metrics, candidate))
            archive.append(candidate.copy())

            if best_metrics is None or metrics["fitness"] > best_metrics["fitness"]:
                best_metrics = metrics
                best_candidate = candidate.copy()

        scored_population.sort(key=lambda item: item[0]["fitness"], reverse=True)
        generation_best_metrics, generation_best_weights = scored_population[0]

        print(
            f"Generation {generation}/{generations}: "
            f"fitness={generation_best_metrics['fitness']:.2f}, "
            f"avg_score={generation_best_metrics['avg_score']:.2f}, "
            f"avg_tile={generation_best_metrics['avg_tile']:.2f}, "
            f"avg_steps={generation_best_metrics['avg_steps']:.2f}, "
            f"best_tile={generation_best_metrics['best_tile']}"
        )
        print("  weights:", format_weights(generation_best_weights))

        next_population = [candidate.copy() for _, candidate in scored_population[:elite_count]]
        while len(next_population) < population_size:
            parent_a = tournament_select(scored_population)
            parent_b = tournament_select(scored_population)
            child = crossover(parent_a, parent_b)
            child = mutate(child)
            next_population.append(child)

        population = next_population

    validation_seeds = [seed * 100000 + 900000 + i for i in range(max(10, games_per_candidate * 2))]
    validation_results = []
    seen = set()
    for candidate in archive:
        key = tuple(round(candidate[name], 8) for name in WEIGHT_RANGES)
        if key in seen:
            continue
        seen.add(key)
        metrics = evaluate_weights(candidate, validation_seeds, depth=depth, adaptive_depth=adaptive_depth)
        validation_results.append((metrics, candidate))

    validation_results.sort(key=lambda item: item[0]["fitness"], reverse=True)
    validation_metrics, validation_best = validation_results[0]

    save_weights(validation_best)
    print("\nSaved best weights to best_weights.json")
    print("Best training metrics:", best_metrics)
    print("Best validation metrics:", validation_metrics)
    print("Best validation weights:", format_weights(validation_best))
    return validation_best, validation_metrics


def compare_weights(games=20, depth=3, adaptive_depth=False, seed=2026):
    best = load_weights()
    seeds = [seed + i for i in range(games)]

    baseline_metrics = evaluate_weights(DEFAULT_WEIGHTS.copy(), seeds, depth=depth, adaptive_depth=adaptive_depth)
    evolved_metrics = evaluate_weights(best, seeds, depth=depth, adaptive_depth=adaptive_depth)

    print("===== BASELINE DEFAULT WEIGHTS =====")
    print_metrics(baseline_metrics)
    print("weights:", format_weights(DEFAULT_WEIGHTS))

    print("\n===== EVOLVED WEIGHTS =====")
    print_metrics(evolved_metrics)
    print("weights:", format_weights(best))

    improvement = evolved_metrics["avg_score"] - baseline_metrics["avg_score"]
    percentage = improvement / baseline_metrics["avg_score"] * 100 if baseline_metrics["avg_score"] else 0
    print(f"\nAverage score change: {improvement:.2f} ({percentage:.2f}%)")


def print_metrics(metrics):
    print(f"Fitness: {metrics['fitness']:.2f}")
    print(f"Average Score: {metrics['avg_score']:.2f}")
    print(f"Best Score: {metrics['best_score']}")
    print(f"Average Max Tile: {metrics['avg_tile']:.2f}")
    print(f"Best Max Tile: {metrics['best_tile']}")
    print(f"Average Steps: {metrics['avg_steps']:.2f}")
    print(f"2048 Rate: {metrics['success_2048'] * 100:.2f}%")


def format_weights(strategy_weights):
    return json.dumps(
        {key: round(strategy_weights[key], 4) for key in WEIGHT_RANGES},
        sort_keys=True,
    )


def main():
    parser = argparse.ArgumentParser(description="2048 AI experiments and evolutionary optimization")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run normal experiments")
    run_parser.add_argument("--games", type=int, default=20)
    run_parser.add_argument("--depth", type=int, default=4)
    run_parser.add_argument("--adaptive-depth", action="store_true")
    run_parser.add_argument("--use-best", action="store_true")

    evolve_parser = subparsers.add_parser("evolve", help="Optimize heuristic weights with a genetic algorithm")
    evolve_parser.add_argument("--generations", type=int, default=8)
    evolve_parser.add_argument("--population", type=int, default=10)
    evolve_parser.add_argument("--games", type=int, default=5)
    evolve_parser.add_argument("--depth", type=int, default=3)
    evolve_parser.add_argument("--adaptive-depth", action="store_true")
    evolve_parser.add_argument("--seed", type=int, default=42)

    compare_parser = subparsers.add_parser("compare", help="Compare default weights with best_weights.json")
    compare_parser.add_argument("--games", type=int, default=20)
    compare_parser.add_argument("--depth", type=int, default=3)
    compare_parser.add_argument("--adaptive-depth", action="store_true")
    compare_parser.add_argument("--seed", type=int, default=2026)

    args = parser.parse_args()

    if args.command == "evolve":
        evolve_weights(
            generations=args.generations,
            population_size=args.population,
            games_per_candidate=args.games,
            depth=args.depth,
            adaptive_depth=args.adaptive_depth,
            seed=args.seed,
        )
    elif args.command == "compare":
        compare_weights(
            games=args.games,
            depth=args.depth,
            adaptive_depth=args.adaptive_depth,
            seed=args.seed,
        )
    else:
        selected_weights = load_weights() if getattr(args, "use_best", False) else DEFAULT_WEIGHTS.copy()
        run_experiments(
            n=getattr(args, "games", 20),
            depth=getattr(args, "depth", 4),
            adaptive_depth=getattr(args, "adaptive_depth", False),
            strategy_weights=selected_weights,
        )


if __name__ == "__main__":
    main()
