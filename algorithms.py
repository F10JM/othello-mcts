import random
import math
from othello import Board, BLACK, WHITE, move_code
import transposition

# ---- Constants ----
C = 0.4  # UCB/UCT exploration constant


# ===================================================================
# Flat Monte Carlo
# ===================================================================

def BestMoveFlatMC(board, n):
    """Flat Monte Carlo: distribute n playouts equally among legal moves."""
    moves = board.legalMoves()
    if not moves:
        return None
    bestScore = -1
    bestMove = moves[0]
    for m in moves:
        sum_score = 0.0
        nb = n // len(moves)
        for _ in range(nb):
            b = board.copy()
            b.play(m)
            sum_score += b.playout()
        # Score from current player's perspective
        if board.turn == WHITE:
            sum_score = nb - sum_score
        if sum_score > bestScore:
            bestScore = sum_score
            bestMove = m
    return bestMove


# ===================================================================
# UCT
# ===================================================================

def UCT(board):
    """Recursive UCT. Returns score from Black's perspective."""
    if board.terminal():
        return board.score()

    t = transposition.look(board)
    if t is not None:
        moves = board.legalMoves()
        if not moves:
            # Must pass
            board.play(None)
            return UCT(board)

        # Select best child via UCB
        bestValue = -1e9
        bestIndex = 0
        for i in range(len(moves)):
            if t[1][i] == 0:
                bestIndex = i
                bestValue = 1e9
                break
            # UCB formula
            exploit = t[2][i] / t[1][i]
            if board.turn == WHITE:
                exploit = 1.0 - exploit
            explore = C * math.sqrt(math.log(t[0]) / t[1][i])
            value = exploit + explore
            if value > bestValue:
                bestValue = value
                bestIndex = i

        # Play selected move
        board.play(moves[bestIndex])
        res = UCT(board)

        # Update stats (always store from Black's perspective)
        t[0] += 1
        t[1][bestIndex] += 1
        t[2][bestIndex] += res
        return res
    else:
        # Leaf node: add to table and playout
        moves = board.legalMoves()
        if not moves:
            board.play(None)
            return UCT(board)
        transposition.add(board)
        return board.playout()


def BestMoveUCT(board, n):
    """Run n UCT iterations, return the most visited move."""
    transposition.Table.clear()
    for _ in range(n):
        b = board.copy()
        UCT(b)

    t = transposition.look(board)
    if t is None:
        return None

    moves = board.legalMoves()
    if not moves:
        return None

    # Return most visited move
    bestIndex = 0
    bestCount = -1
    for i in range(len(moves)):
        if t[1][i] > bestCount:
            bestCount = t[1][i]
            bestIndex = i
    return moves[bestIndex]


# ===================================================================
# Test: UCT vs Flat MC
# ===================================================================

if __name__ == '__main__':
    n_games = 20
    n_playouts = 200
    uct_wins = 0
    flat_wins = 0
    draws = 0

    print(f"UCT vs Flat MC: {n_games} games, {n_playouts} playouts each")
    print()

    for game in range(n_games):
        board = Board()
        # Alternate colors: even games UCT=Black, odd games UCT=White
        uct_is_black = (game % 2 == 0)

        while not board.terminal():
            moves = board.legalMoves()
            if not moves:
                board.play(None)
                continue

            if (board.turn == BLACK) == uct_is_black:
                move = BestMoveUCT(board, n_playouts)
            else:
                move = BestMoveFlatMC(board, n_playouts)
            board.play(move)

        s = board.score()
        # Determine result from UCT's perspective
        if uct_is_black:
            if s == 1.0:
                uct_wins += 1
            elif s == 0.0:
                flat_wins += 1
            else:
                draws += 1
        else:
            if s == 0.0:
                uct_wins += 1
            elif s == 1.0:
                flat_wins += 1
            else:
                draws += 1

        color_str = "Black" if uct_is_black else "White"
        result = "UCT" if ((uct_is_black and s == 1.0) or (not uct_is_black and s == 0.0)) else \
                 "Flat" if ((uct_is_black and s == 0.0) or (not uct_is_black and s == 1.0)) else "Draw"
        print(f"Game {game+1:2d}: UCT={color_str}, Winner={result}")

    print()
    print(f"Results: UCT {uct_wins} - {flat_wins} Flat MC ({draws} draws)")
    print(f"UCT win rate: {uct_wins / n_games:.1%}")
