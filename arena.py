import time
from othello import Board, BLACK, WHITE
from algorithms import resetPPAFM


def play_match(algo1_name, algo1_fn, algo2_name, algo2_fn,
               n_games=100, n_playouts=1000, verbose=True):
    """Play n_games between algo1 and algo2.
    First half: algo1=Black, second half: algo1=White.
    Returns dict with results and timing info."""
    a1_wins = 0
    a2_wins = 0
    draws = 0
    a1_total_time = 0.0
    a2_total_time = 0.0
    a1_moves = 0
    a2_moves = 0

    if verbose:
        print(f"\n{'='*60}")
        print(f"{algo1_name} vs {algo2_name}: {n_games} games, {n_playouts} playouts")
        print(f"{'='*60}")

    for game in range(n_games):
        board = Board()
        a1_is_black = (game < n_games // 2)
        resetPPAFM()

        while not board.terminal():
            moves = board.legalMoves()
            if not moves:
                board.play(None)
                continue

            if (board.turn == BLACK) == a1_is_black:
                t0 = time.time()
                move = algo1_fn(board, n_playouts)
                a1_total_time += time.time() - t0
                a1_moves += 1
            else:
                t0 = time.time()
                move = algo2_fn(board, n_playouts)
                a2_total_time += time.time() - t0
                a2_moves += 1
            board.play(move)

        s = board.score()
        if a1_is_black:
            if s == 1.0: a1_wins += 1
            elif s == 0.0: a2_wins += 1
            else: draws += 1
        else:
            if s == 0.0: a1_wins += 1
            elif s == 1.0: a2_wins += 1
            else: draws += 1

        if verbose and (game + 1) % 10 == 0:
            print(f"  After {game+1} games: {algo1_name} {a1_wins} - {a2_wins} {algo2_name} ({draws} draws)")

    a1_avg_time = a1_total_time / a1_moves if a1_moves > 0 else 0
    a2_avg_time = a2_total_time / a2_moves if a2_moves > 0 else 0

    result = {
        'player1': algo1_name,
        'player2': algo2_name,
        'n_games': n_games,
        'n_playouts': n_playouts,
        'p1_wins': a1_wins,
        'p2_wins': a2_wins,
        'draws': draws,
        'p1_winrate': a1_wins / n_games,
        'p1_avg_time': a1_avg_time,
        'p2_avg_time': a2_avg_time,
    }

    if verbose:
        print(f"  FINAL: {algo1_name} {a1_wins} - {a2_wins} {algo2_name} ({draws} draws)")
        print(f"  {algo1_name} win rate: {a1_wins / n_games:.1%}")
        print(f"  Avg time/move: {algo1_name}={a1_avg_time:.3f}s, {algo2_name}={a2_avg_time:.3f}s")

    return result
