import random
import math
from othello import Board, BLACK, WHITE, move_code
import transposition

# ---- Constants ----
C = 0.4  # UCB/UCT exploration constant
BIAS = 1e-5  # RAVE bias
GRAVE_THRESHOLD = 50  # min playouts for GRAVE ref node


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
# RAVE
# ===================================================================

def RAVE(board):
    """Recursive RAVE (UCT + AMAF). Returns score from Black's perspective."""
    if board.terminal():
        return board.score(), []

    t = transposition.look(board)
    if t is not None:
        moves = board.legalMoves()
        if not moves:
            board.play(None)
            return RAVE(board)

        # Select best child via RAVE formula
        bestValue = -1e9
        bestIndex = 0
        for i in range(len(moves)):
            if t[1][i] == 0:
                bestIndex = i
                bestValue = 1e9
                break
            code = move_code(moves[i], board.turn)
            # UCT part
            exploit = t[2][i] / t[1][i]
            if board.turn == WHITE:
                exploit = 1.0 - exploit
            explore = C * math.sqrt(math.log(t[0]) / t[1][i])
            value = exploit + explore
            # AMAF part
            if t[3][code] > 0:
                amaf = t[4][code] / t[3][code]
                if board.turn == WHITE:
                    amaf = 1.0 - amaf
                beta = t[3][code] / (t[3][code] + t[1][i] + BIAS * t[3][code] * t[1][i])
                value = (1.0 - beta) * (exploit + explore) + beta * amaf
            if value > bestValue:
                bestValue = value
                bestIndex = i

        board.play(moves[bestIndex])
        res, played = RAVE(board)

        # Update stats
        t[0] += 1
        t[1][bestIndex] += 1
        t[2][bestIndex] += res

        # Update AMAF for all moves played during the rest of the game
        for code in played:
            t[3][code] += 1
            t[4][code] += res

        return res, played
    else:
        moves = board.legalMoves()
        if not moves:
            board.play(None)
            return RAVE(board)
        transposition.addAMAF(board)
        res, played = board.playoutAMAF()
        return res, played


def BestMoveRAVE(board, n):
    """Run n RAVE iterations, return most visited move."""
    transposition.Table.clear()
    for _ in range(n):
        b = board.copy()
        RAVE(b)

    t = transposition.look(board)
    if t is None:
        return None
    moves = board.legalMoves()
    if not moves:
        return None

    bestIndex = 0
    bestCount = -1
    for i in range(len(moves)):
        if t[1][i] > bestCount:
            bestCount = t[1][i]
            bestIndex = i
    return moves[bestIndex]


# ===================================================================
# GRAVE
# ===================================================================

def GRAVE(board, tref):
    """Recursive GRAVE. Uses ancestor with enough playouts as AMAF reference.
    Returns score from Black's perspective and list of move codes played."""
    if board.terminal():
        return board.score(), []

    t = transposition.look(board)
    if t is not None:
        moves = board.legalMoves()
        if not moves:
            board.play(None)
            return GRAVE(board, tref)

        # Update tref if this node has enough playouts
        if t[0] > GRAVE_THRESHOLD:
            tref = t

        # Select best child
        bestValue = -1e9
        bestIndex = 0
        for i in range(len(moves)):
            if t[1][i] == 0:
                bestIndex = i
                bestValue = 1e9
                break
            # UCT part
            exploit = t[2][i] / t[1][i]
            if board.turn == WHITE:
                exploit = 1.0 - exploit
            explore = C * math.sqrt(math.log(t[0]) / t[1][i])
            value = exploit + explore
            # AMAF from tref (GRAVE key difference)
            if tref is not None:
                code = move_code(moves[i], board.turn)
                if tref[3][code] > 0:
                    amaf = tref[4][code] / tref[3][code]
                    if board.turn == WHITE:
                        amaf = 1.0 - amaf
                    beta = tref[3][code] / (tref[3][code] + t[1][i] + BIAS * tref[3][code] * t[1][i])
                    value = (1.0 - beta) * (exploit + explore) + beta * amaf
            if value > bestValue:
                bestValue = value
                bestIndex = i

        board.play(moves[bestIndex])
        res, played = GRAVE(board, tref)

        # Update stats
        t[0] += 1
        t[1][bestIndex] += 1
        t[2][bestIndex] += res

        # Update AMAF
        for code in played:
            t[3][code] += 1
            t[4][code] += res

        return res, played
    else:
        moves = board.legalMoves()
        if not moves:
            board.play(None)
            return GRAVE(board, tref)
        transposition.addAMAF(board)
        res, played = board.playoutAMAF()
        return res, played


def BestMoveGRAVE(board, n):
    """Run n GRAVE iterations, return most visited move."""
    transposition.Table.clear()
    for _ in range(n):
        b = board.copy()
        GRAVE(b, None)

    t = transposition.look(board)
    if t is None:
        return None
    moves = board.legalMoves()
    if not moves:
        return None

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

def run_match(algo1_name, algo1_fn, algo2_name, algo2_fn, n_games=20, n_playouts=200):
    """Run a match between two algorithms, alternating colors."""
    a1_wins = 0
    a2_wins = 0
    draws = 0

    print(f"{algo1_name} vs {algo2_name}: {n_games} games, {n_playouts} playouts each")

    for game in range(n_games):
        board = Board()
        a1_is_black = (game % 2 == 0)

        while not board.terminal():
            moves = board.legalMoves()
            if not moves:
                board.play(None)
                continue

            if (board.turn == BLACK) == a1_is_black:
                move = algo1_fn(board, n_playouts)
            else:
                move = algo2_fn(board, n_playouts)
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

        color_str = "Black" if a1_is_black else "White"
        if (a1_is_black and s == 1.0) or (not a1_is_black and s == 0.0):
            winner = algo1_name
        elif (a1_is_black and s == 0.0) or (not a1_is_black and s == 1.0):
            winner = algo2_name
        else:
            winner = "Draw"
        print(f"  Game {game+1:2d}: {algo1_name}={color_str}, Winner={winner}")

    print(f"  => {algo1_name} {a1_wins} - {a2_wins} {algo2_name} ({draws} draws)")
    print(f"  => {algo1_name} win rate: {a1_wins / n_games:.1%}")
    print()


if __name__ == '__main__':
    run_match("RAVE", BestMoveRAVE, "UCT", BestMoveUCT)
    run_match("GRAVE", BestMoveGRAVE, "RAVE", BestMoveRAVE)
