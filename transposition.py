from othello import move_code

MaxCode = 128  # 64 per color (color-1)*64 + row*8 + col

Table = {}


def look(board):
    """Return table entry or None."""
    if board.h in Table:
        return Table[board.h]
    return None


def add(board):
    """Add entry: [nplayouts, [ni per move], [wi per move]]."""
    moves = board.legalMoves()
    n = len(moves)
    nplayouts = [0 for _ in range(n)]
    nwins = [0.0 for _ in range(n)]
    Table[board.h] = [0, nplayouts, nwins]
    return Table[board.h]


def addAMAF(board):
    """Add entry with AMAF stats for RAVE/GRAVE."""
    moves = board.legalMoves()
    n = len(moves)
    nplayouts = [0 for _ in range(n)]
    nwins = [0.0 for _ in range(n)]
    nplayoutsAMAF = [0.0 for _ in range(MaxCode)]
    nwinsAMAF = [0.0 for _ in range(MaxCode)]
    Table[board.h] = [0, nplayouts, nwins, nplayoutsAMAF, nwinsAMAF]
    return Table[board.h]
