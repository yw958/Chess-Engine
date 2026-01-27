import ChessBackend
import time

def perft(gs: ChessBackend.GameState, depth: int) -> int:
    """
    Perform a perft (performance test) to count the number of possible positions
    reachable from the current game state up to a given depth.
    """
    if depth == 1:
        total_caps = 0
        total_checks = 0
        total_mates = 0
        total_discovered_checks = 0
        total_enPassant = 0
        total_castles = 0
        total_promotions = 0
        total_double_checks = 0
        moves_ = gs.validMoves.copy()
        for mv in moves_:
            if mv.pieceCaptured != 0:
                total_caps += 1
            if mv.isCheck:
                total_checks += 1
            if mv.discoveredCheck != None:
                total_discovered_checks += 1
                total_checks += 1
            if mv.isEnPassantMove:
                total_enPassant += 1
            if mv.isCastlingMove:
                total_castles += 1
            if mv.pawnPromotion != 0:
                total_promotions += 1
            if mv.isCheck and mv.discoveredCheck != None:
                total_double_checks += 1
                total_checks -= 1  # avoid double counting
            gs.makeMove(mv)
            if gs.info.winner is not None and gs.info.winner != 0:
                total_mates += 1
            gs.undoMove(reCalculateMoves=False)
        return len(moves_), total_caps, total_checks, total_mates, total_discovered_checks, total_enPassant, total_castles, total_promotions, total_double_checks
    total_caps = 0
    total_checks = 0
    total_mates = 0
    total_discovered_checks = 0
    total_enPassant = 0
    total_castles = 0
    total_promotions = 0
    total_double_checks = 0
    total_nodes = 0
    moves = gs.validMoves.copy()
    for mv in moves:
        gs.makeMove(mv)
        n, c, ch, m, dc, ep, ca, pr, dch = perft(gs, depth - 1)
        total_nodes += n
        total_caps += c 
        total_checks += ch 
        total_mates += m
        total_discovered_checks += dc
        total_enPassant += ep
        total_castles += ca
        total_promotions += pr
        total_double_checks += dch
        gs.undoMove(reCalculateMoves=False)
    return total_nodes, total_caps, total_checks, total_mates, total_discovered_checks, total_enPassant, total_castles, total_promotions, total_double_checks

if __name__ == "__main__":
    gs = ChessBackend.GameState()
    depth = 5 
    startTime = time.time()
    nodes, captures, checks, checkMates, discoveredChecks, enPassants, castles, promotions, doubleChecks = perft(gs, depth)
    endTime = time.time()
    print(f"Perft to depth {depth}: {nodes} nodes")
    print(f"Captures: {captures}, Checks: {checks}, Checkmates: {checkMates}")
    print(f"Discovered Checks: {discoveredChecks}, En Passants: {enPassants}, Castles: {castles}")
    print(f"Promotions: {promotions}, Double Checks: {doubleChecks}")
    print(f"Time taken: {endTime - startTime:.2f} seconds")
    print(f"Nodes per second: {nodes / (endTime - startTime):.2f}")