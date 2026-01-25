import ChessBackend
import time

def perft(gs: ChessBackend.GameState, depth: int) -> int:
    """
    Perform a perft (performance test) to count the number of possible positions
    reachable from the current game state up to a given depth.
    """
    if depth == 0:
        moves = 1
        captures = gs.moveLog[-1].pieceCaptured != 0
        checks = gs.info.inCheck[gs.player]
        mates = 1 if gs.info.winner is not None else 0
        return moves, captures, checks, mates
    total_nodes = 0
    total_caps = 0
    total_checks = 0
    total_mates = 0
    moves = gs.validMoves.copy()
    for mv in moves:
        gs.makeMove(mv)
        n, c, ch, m = perft(gs, depth - 1)
        total_nodes += n
        total_caps += c 
        total_checks += ch 
        total_mates += m
        gs.undoMove(reCalculateMoves=False)
    return total_nodes, total_caps, total_checks, total_mates

if __name__ == "__main__":
    gs = ChessBackend.GameState()
    depth = 4 
    startTime = time.time()
    nodes, captures, checks, checkMates = perft(gs, depth)
    endTime = time.time()
    print(f"Perft to depth {depth}: {nodes} nodes")
    print(f"Captures: {captures}, Checks: {checks}, Checkmates: {checkMates}")
    print(f"Time taken: {endTime - startTime:.2f} seconds")
    print(f"Nodes per second: {nodes / (endTime - startTime):.2f}")