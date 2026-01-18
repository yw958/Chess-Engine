"""
A module containing the minimax algorithm with alpha-beta pruning for chess.
"""


from Chess import ChessBackend

def miniMax(gameState: ChessBackend.GameState, depth: int, alpha: float, beta: float, player) -> float:
    if depth == 0 or gameState.info.winner is not None:
        return gameState.info.eval

    if player == 1:
        maxEval = float('-inf')
        allMoves = []
        for moves in gameState.info.validMoves.values():
            allMoves += moves
        for move in allMoves:
            gameState.makeMove(move)
            eval = miniMax(gameState, depth - 1, alpha, beta, -1)
            gameState.undoMove(reCalculateMoves=False)
            maxEval = max(maxEval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return maxEval
    else:
        minEval = float('inf')
        allMoves = []
        for moves in gameState.info.validMoves.values():
            allMoves += moves
        for move in allMoves:
            gameState.makeMove(move)
            eval = miniMax(gameState, depth - 1, alpha, beta, 1)
            gameState.undoMove(reCalculateMoves=False)
            minEval = min(minEval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return minEval
    
def findBestMove(gameState: ChessBackend.GameState, depth: int = 10) -> ChessBackend.Move:
    bestMove = None
    if gameState.player == 1:
        maxEval = float('-inf')
        allMoves = []
        for moves in gameState.info.validMoves.values():
            allMoves += moves
        for move in allMoves:
            gameState.makeMove(move)
            eval = miniMax(gameState, depth - 1, float('-inf'), float('inf'), -1)
            gameState.undoMove(reCalculateMoves=False)
            if eval >= maxEval:
                maxEval = eval
                bestMove = move
    else:
        minEval = float('inf')
        allMoves = []
        for moves in gameState.info.validMoves.values():
            allMoves += moves
        for move in allMoves:
            gameState.makeMove(move)
            eval = miniMax(gameState, depth - 1, float('-inf'), float('inf'), 1)
            gameState.undoMove(reCalculateMoves=False)
            if eval <= minEval:
                minEval = eval
                bestMove = move
    return bestMove