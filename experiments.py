import sys
import csv
import time
from arena import play_match
from algorithms import (
    BestMoveFlatMC, BestMoveUCT, BestMoveRAVE, BestMoveGRAVE,
    BestMovePPAF, BestMovePPAFM, BestMoveGRAVEPolicyBias,
)

# Match definitions (matches 1-9 from CLAUDE.md)
MATCHES = [
    (1,  "UCT",             BestMoveUCT,             "FlatMC",          BestMoveFlatMC),
    (2,  "RAVE",            BestMoveRAVE,            "UCT",             BestMoveUCT),
    (3,  "GRAVE",           BestMoveGRAVE,           "RAVE",            BestMoveRAVE),
    (4,  "GRAVE",           BestMoveGRAVE,           "UCT",             BestMoveUCT),
    (5,  "PPAF",            BestMovePPAF,            "UCT",             BestMoveUCT),
    (6,  "PPAFM",           BestMovePPAFM,           "PPAF",            BestMovePPAF),
    (7,  "PPAFM",           BestMovePPAFM,           "UCT",             BestMoveUCT),
    (8,  "GRAVEPolicyBias", BestMoveGRAVEPolicyBias, "GRAVE",           BestMoveGRAVE),
    (9,  "GRAVEPolicyBias", BestMoveGRAVEPolicyBias, "PPAFM",           BestMovePPAFM),
]


def run_experiments(n_games=100, n_playouts=1000, dry_run=False):
    if dry_run:
        print("=" * 60)
        print("DRY RUN: UCT vs FlatMC, 4 games, 100 playouts")
        print("=" * 60)
        result = play_match("UCT", BestMoveUCT, "FlatMC", BestMoveFlatMC,
                            n_games=4, n_playouts=100, verbose=True)
        print("\nDry run complete. Result:", result)
        return

    results = []
    timing = {}  # algo_name -> list of avg times

    total_start = time.time()

    for match_id, p1_name, p1_fn, p2_name, p2_fn in MATCHES:
        print(f"\n>>> Match {match_id}/9")
        result = play_match(p1_name, p1_fn, p2_name, p2_fn,
                            n_games=n_games, n_playouts=n_playouts, verbose=True)
        result['match'] = match_id
        results.append(result)

        # Collect timing
        if p1_name not in timing:
            timing[p1_name] = []
        timing[p1_name].append(result['p1_avg_time'])
        if p2_name not in timing:
            timing[p2_name] = []
        timing[p2_name].append(result['p2_avg_time'])

    total_elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"All experiments complete in {total_elapsed/60:.1f} minutes")
    print(f"{'='*60}")

    # Save results.csv
    with open('results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['match', 'player1', 'player2', 'n_games', 'n_playouts',
                         'p1_wins', 'p2_wins', 'draws', 'p1_winrate'])
        for r in results:
            writer.writerow([r['match'], r['player1'], r['player2'], r['n_games'],
                             r['n_playouts'], r['p1_wins'], r['p2_wins'], r['draws'],
                             f"{r['p1_winrate']:.4f}"])
    print("Saved results.csv")

    # Save timing.csv
    with open('timing.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['algorithm', 'avg_time_per_move'])
        for algo, times in sorted(timing.items()):
            avg = sum(times) / len(times)
            writer.writerow([algo, f"{avg:.4f}"])
    print("Saved timing.csv")

    # Print summary table
    print(f"\n{'='*60}")
    print(f"{'Match':<6} {'Player 1':<18} {'Player 2':<18} {'P1 Wins':>7} {'P2 Wins':>7} {'Draws':>5} {'P1 WR':>6}")
    print("-" * 60)
    for r in results:
        print(f"{r['match']:<6} {r['player1']:<18} {r['player2']:<18} "
              f"{r['p1_wins']:>7} {r['p2_wins']:>7} {r['draws']:>5} {r['p1_winrate']:>6.1%}")


if __name__ == '__main__':
    if '--dry-run' in sys.argv:
        run_experiments(dry_run=True)
    else:
        n_games = 100
        n_playouts = 1000
        # Allow overrides via command line
        for arg in sys.argv[1:]:
            if arg.startswith('--games='):
                n_games = int(arg.split('=')[1])
            elif arg.startswith('--playouts='):
                n_playouts = int(arg.split('=')[1])
        run_experiments(n_games=n_games, n_playouts=n_playouts)
