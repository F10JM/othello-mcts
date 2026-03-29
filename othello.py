import numpy as np
import random
import copy

# Constants
EMPTY = 0
BLACK = 1
WHITE = 2

# Directions: (dr, dc) for N, NE, E, SE, S, SW, W, NW
DIRECTIONS = [(-1, 0), (-1, 1), (0, 1), (1, 1),
              (1, 0), (1, -1), (0, -1), (-1, -1)]

# Zobrist hashing tables
# zobrist[piece][row][col] — piece in {0=BLACK, 1=WHITE}
zobrist = [[random.getrandbits(64) for _ in range(64)] for _ in range(2)]
# zobrist_turn: XOR when it's White's turn
zobrist_turn = random.getrandbits(64)


def move_code(move, color):
    """Encode a move for AMAF/PPAF: color * 64 + row * 8 + col."""
    return (color - 1) * 64 + move[0] * 8 + move[1]


class Board:
    def __init__(self):
        self.board = np.zeros((8, 8), dtype=np.int8)
        # Standard starting position
        self.board[3][3] = WHITE
        self.board[3][4] = BLACK
        self.board[4][3] = BLACK
        self.board[4][4] = WHITE
        self.turn = BLACK  # Black plays first
        self.rollout = []  # moves played (for PPAF)
        self.pass_count = 0  # consecutive passes
        # Compute initial Zobrist hash
        self.h = self._compute_hash()

    def _compute_hash(self):
        h = 0
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p != EMPTY:
                    h ^= zobrist[p - 1][r * 8 + c]
        if self.turn == WHITE:
            h ^= zobrist_turn
        return h

    def copy(self):
        b = Board.__new__(Board)
        b.board = self.board.copy()
        b.turn = self.turn
        b.rollout = self.rollout[:]
        b.pass_count = self.pass_count
        b.h = self.h
        return b

    def opponent(self):
        return WHITE if self.turn == BLACK else BLACK

    def _flips_in_dir(self, r, c, dr, dc, color):
        """Return list of positions to flip in one direction."""
        opp = WHITE if color == BLACK else BLACK
        flips = []
        r, c = r + dr, c + dc
        while 0 <= r < 8 and 0 <= c < 8:
            if self.board[r][c] == opp:
                flips.append((r, c))
            elif self.board[r][c] == color:
                return flips
            else:
                return []
            r, c = r + dr, c + dc
        return []

    def _get_flips(self, r, c, color):
        """Return all positions flipped by placing color at (r, c)."""
        if self.board[r][c] != EMPTY:
            return []
        all_flips = []
        for dr, dc in DIRECTIONS:
            all_flips.extend(self._flips_in_dir(r, c, dr, dc, color))
        return all_flips

    def legalMoves(self):
        """Return list of legal (row, col) moves for current player."""
        moves = []
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == EMPTY:
                    if self._get_flips(r, c, self.turn):
                        moves.append((r, c))
        return moves

    def play(self, move):
        """Play a move (row, col) or handle pass (None)."""
        if move is None:
            # Pass
            self.pass_count += 1
            self.h ^= zobrist_turn  # switch turn in hash
            self.turn = self.opponent()
            return

        self.pass_count = 0
        r, c = move
        color = self.turn
        opp = self.opponent()

        # Get flips
        flips = self._get_flips(r, c, color)

        # Place stone
        self.board[r][c] = color
        self.h ^= zobrist[color - 1][r * 8 + c]

        # Flip captured stones
        for fr, fc in flips:
            self.board[fr][fc] = color
            # XOR out old color, XOR in new color
            self.h ^= zobrist[opp - 1][fr * 8 + fc]
            self.h ^= zobrist[color - 1][fr * 8 + fc]

        # Record move
        self.rollout.append(move_code(move, color))

        # Switch turn
        self.h ^= zobrist_turn
        self.turn = opp

    def terminal(self):
        """Game is over if both players have passed consecutively."""
        if self.pass_count >= 2:
            return True
        return False

    def score(self):
        """1.0 if Black wins, 0.0 if White wins, 0.5 if draw."""
        black = np.count_nonzero(self.board == BLACK)
        white = np.count_nonzero(self.board == WHITE)
        if black > white:
            return 1.0
        elif white > black:
            return 0.0
        else:
            return 0.5

    def playout(self):
        """Play random moves until terminal, return score."""
        while not self.terminal():
            moves = self.legalMoves()
            if moves:
                self.play(random.choice(moves))
            else:
                self.play(None)
        return self.score()

    def playoutAMAF(self):
        """Playout that records all moves played (for RAVE/GRAVE).
        Returns (score, rollout_from_start_of_playout)."""
        start = len(self.rollout)
        while not self.terminal():
            moves = self.legalMoves()
            if moves:
                self.play(random.choice(moves))
            else:
                self.play(None)
        return self.score(), self.rollout[start:]

    def __str__(self):
        symbols = {EMPTY: '.', BLACK: 'X', WHITE: 'O'}
        lines = ['  a b c d e f g h']
        for r in range(8):
            row = ' '.join(symbols[self.board[r][c]] for c in range(8))
            lines.append(f'{r + 1} {row}')
        lines.append(f'Turn: {"Black(X)" if self.turn == BLACK else "White(O)"}')
        return '\n'.join(lines)


# ---- Validation ----

if __name__ == '__main__':
    print("Running 10,000 random games...")
    total_moves = 0
    n_games = 10000
    scores = {1.0: 0, 0.0: 0, 0.5: 0}

    for i in range(n_games):
        b = Board()
        move_count = 0
        while not b.terminal():
            moves = b.legalMoves()
            if moves:
                b.play(random.choice(moves))
                move_count += 1
            else:
                b.play(None)
        s = b.score()
        scores[s] = scores.get(s, 0) + 1
        total_moves += move_count

    avg_len = total_moves / n_games
    print(f"Average game length: {avg_len:.1f} moves")
    print(f"Black wins: {scores[1.0]}, White wins: {scores[0.0]}, Draws: {scores[0.5]}")
    print(f"Black win rate: {scores[1.0] / n_games:.3f}")
    print()

    # Display a sample game step by step
    print("=== Sample Game ===")
    b = Board()
    print(f"Initial board:\n{b}\n")
    move_num = 0
    while not b.terminal():
        moves = b.legalMoves()
        if moves:
            m = random.choice(moves)
            player = "Black" if b.turn == BLACK else "White"
            move_num += 1
            b.play(m)
            if move_num <= 10 or b.terminal():
                col_letter = chr(ord('a') + m[1])
                print(f"Move {move_num}: {player} plays {col_letter}{m[0]+1}")
                print(b)
                print()
        else:
            player = "Black" if b.turn == BLACK else "White"
            print(f"{player} passes")
            b.play(None)

    if move_num > 10:
        print(f"... (showing first 10 and last move, total {move_num} moves)")

    print(f"\nFinal score: Black={np.count_nonzero(b.board == BLACK)}, "
          f"White={np.count_nonzero(b.board == WHITE)}")
    result = "Black wins" if b.score() == 1.0 else "White wins" if b.score() == 0.0 else "Draw"
    print(f"Result: {result}")

    # Verify Zobrist hash consistency
    print("\n=== Zobrist Hash Consistency Check ===")
    consistent = True
    for _ in range(100):
        b = Board()
        while not b.terminal():
            moves = b.legalMoves()
            if moves:
                b.play(random.choice(moves))
            else:
                b.play(None)
            if b.h != b._compute_hash():
                consistent = False
                break
        if not consistent:
            break
    print(f"Hash consistency: {'PASS' if consistent else 'FAIL'}")
