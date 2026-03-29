import random

# Constants
EMPTY = 0
BLACK = 1
WHITE = 2

# Directions as flat offsets on a 10x10 padded board (sentinel-based)
# We use a 10x10 board with SENTINEL=3 border to avoid bounds checking
SENTINEL = 3
BOARD_SIZE = 100  # 10x10

# Direction offsets on 10-wide board
DIR_OFFSETS = [-10, -9, 1, 11, 10, 9, -1, -11]  # N, NE, E, SE, S, SW, W, NW

# Mapping (row, col) in 8x8 to index in 10x10
def rc_to_idx(r, c):
    return (r + 1) * 10 + (c + 1)

def idx_to_rc(idx):
    return (idx // 10 - 1, idx % 10 - 1)

# All valid cell indices on the 10x10 board
VALID_CELLS = [rc_to_idx(r, c) for r in range(8) for c in range(8)]

# Zobrist hashing tables
# zobrist[piece][cell_index] — piece in {0=BLACK-1, 1=WHITE-1}
zobrist = [[random.getrandbits(64) for _ in range(BOARD_SIZE)] for _ in range(2)]
zobrist_turn = random.getrandbits(64)


def move_code(move, color):
    """Encode a move for AMAF/PPAF: (color-1)*64 + row*8 + col."""
    return (color - 1) * 64 + move[0] * 8 + move[1]


class Board:
    __slots__ = ['cells', 'turn', 'rollout', 'pass_count', 'h']

    def __init__(self):
        # 10x10 padded board with sentinels
        self.cells = [SENTINEL] * BOARD_SIZE
        for idx in VALID_CELLS:
            self.cells[idx] = EMPTY
        # Standard starting position
        self.cells[rc_to_idx(3, 3)] = WHITE
        self.cells[rc_to_idx(3, 4)] = BLACK
        self.cells[rc_to_idx(4, 3)] = BLACK
        self.cells[rc_to_idx(4, 4)] = WHITE
        self.turn = BLACK
        self.rollout = []
        self.pass_count = 0
        self.h = self._compute_hash()

    def _compute_hash(self):
        h = 0
        cells = self.cells
        for idx in VALID_CELLS:
            p = cells[idx]
            if p == BLACK or p == WHITE:
                h ^= zobrist[p - 1][idx]
        if self.turn == WHITE:
            h ^= zobrist_turn
        return h

    def copy(self):
        b = Board.__new__(Board)
        b.cells = self.cells[:]
        b.turn = self.turn
        b.rollout = self.rollout[:]
        b.pass_count = self.pass_count
        b.h = self.h
        return b

    def legalMoves(self):
        """Return list of legal (row, col) moves for current player."""
        color = self.turn
        opp = 3 - color  # BLACK=1->WHITE=2, WHITE=2->BLACK=1
        cells = self.cells
        moves = []
        for idx in VALID_CELLS:
            if cells[idx] != EMPTY:
                continue
            # Check each direction
            for d in DIR_OFFSETS:
                pos = idx + d
                if cells[pos] != opp:
                    continue
                # Walk in this direction
                pos += d
                while cells[pos] == opp:
                    pos += d
                if cells[pos] == color:
                    moves.append(idx_to_rc(idx))
                    break
        return moves

    def play(self, move):
        """Play a move (row, col) or handle pass (None)."""
        if move is None:
            self.pass_count += 1
            self.h ^= zobrist_turn
            self.turn = 3 - self.turn
            return

        self.pass_count = 0
        r, c = move
        idx = rc_to_idx(r, c)
        color = self.turn
        opp = 3 - color
        cells = self.cells

        # Place stone
        cells[idx] = color
        h = self.h ^ zobrist[color - 1][idx]

        # Flip in each direction
        for d in DIR_OFFSETS:
            pos = idx + d
            if cells[pos] != opp:
                continue
            # Collect flips
            flips = []
            while cells[pos] == opp:
                flips.append(pos)
                pos += d
            if cells[pos] == color:
                for f in flips:
                    cells[f] = color
                    h ^= zobrist[opp - 1][f] ^ zobrist[color - 1][f]

        # Record move and switch turn
        self.rollout.append((color - 1) * 64 + r * 8 + c)
        h ^= zobrist_turn
        self.h = h
        self.turn = opp

    def terminal(self):
        return self.pass_count >= 2

    def score(self):
        """1.0 if Black wins, 0.0 if White wins, 0.5 if draw."""
        black = 0
        white = 0
        cells = self.cells
        for idx in VALID_CELLS:
            p = cells[idx]
            if p == BLACK:
                black += 1
            elif p == WHITE:
                white += 1
        if black > white:
            return 1.0
        elif white > black:
            return 0.0
        return 0.5

    def playout(self):
        """Play random moves until terminal, return score."""
        while self.pass_count < 2:
            moves = self.legalMoves()
            if moves:
                self.play(moves[random.randrange(len(moves))])
            else:
                self.pass_count += 1
                self.h ^= zobrist_turn
                self.turn = 3 - self.turn
        return self.score()

    def playoutAMAF(self):
        """Playout recording moves for RAVE/GRAVE. Returns (score, new_moves)."""
        start = len(self.rollout)
        while self.pass_count < 2:
            moves = self.legalMoves()
            if moves:
                self.play(moves[random.randrange(len(moves))])
            else:
                self.pass_count += 1
                self.h ^= zobrist_turn
                self.turn = 3 - self.turn
        return self.score(), self.rollout[start:]

    def __str__(self):
        symbols = {EMPTY: '.', BLACK: 'X', WHITE: 'O'}
        lines = ['  a b c d e f g h']
        for r in range(8):
            row = ' '.join(symbols[self.cells[rc_to_idx(r, c)]] for c in range(8))
            lines.append(f'{r + 1} {row}')
        lines.append(f'Turn: {"Black(X)" if self.turn == BLACK else "White(O)"}')
        return '\n'.join(lines)


# ---- Validation ----

if __name__ == '__main__':
    import time
    print("Benchmarking playout speed...")
    b = Board()
    t0 = time.time()
    N = 1000
    for _ in range(N):
        b2 = b.copy()
        b2.playout()
    t1 = time.time()
    print(f"{N} playouts in {t1-t0:.2f}s = {N/(t1-t0):.0f} playouts/sec")
    print()

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

    # Zobrist hash consistency
    print("\nZobrist hash consistency...", end=" ")
    ok = True
    for _ in range(100):
        b = Board()
        while not b.terminal():
            moves = b.legalMoves()
            if moves:
                b.play(random.choice(moves))
            else:
                b.play(None)
            if b.h != b._compute_hash():
                ok = False
                break
        if not ok:
            break
    print("PASS" if ok else "FAIL")
