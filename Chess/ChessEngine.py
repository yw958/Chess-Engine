"""
A module containing the minimax algorithm with alpha-beta pruning for chess.
"""


from Chess import ChessBackend

# Prioritize center squares when eval is equal
SQUAREVALUES = [
    [0.5, 1, 1, 1, 1, 1, 1, 0.5],
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 2, 2, 3, 3, 2, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 2, 3, 3, 2, 2, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
    [0.5, 1, 1, 1, 1, 1, 1, 0.5],
]

def miniMax(gameState: ChessBackend.GameState, depth: int, alpha: float, beta: float, player) -> float:
    if depth == 0 or gameState.info.winner is not None:
        return gameState.info.eval
    allMoves = []
    for moves in gameState.info.validMoves.values():
        allMoves += moves
    sortMoves(allMoves)
    if player == 1:
        maxEval = float('-inf')
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
    allMoves = []
    for moves in gameState.info.validMoves.values():
        allMoves += moves
    sortMoves(allMoves)
    for move in allMoves: #debug
        print(move.getChessNotation(), end=' ')
    if gameState.player == 1:
        maxEval = float('-inf')
        for move in allMoves:
            gameState.makeMove(move)
            eval = miniMax(gameState, depth - 1, float('-inf'), float('inf'), -1)
            gameState.undoMove(reCalculateMoves=False)
            if eval > maxEval:
                maxEval = eval
                bestMove = move
    else:
        minEval = float('inf')
        for move in allMoves:
            gameState.makeMove(move)
            eval = miniMax(gameState, depth - 1, float('-inf'), float('inf'), 1)
            gameState.undoMove(reCalculateMoves=False)
            if eval < minEval:
                minEval = eval
                bestMove = move
    if bestMove is None: # Mate in a few steps
        bestMove = allMoves[0]
    return bestMove

def sortMoves(moves: list[ChessBackend.Move]):
    # Sort moves to prioritize captures and center control
    def moveValue(move: ChessBackend.Move):
        value = 0
        if move.pieceCaptured != 0:
            value += 10 * abs(move.pieceCaptured) - abs(move.pieceMoved)
        if move.pawnPromotion != 0:
            value += 10 * abs(move.pawnPromotion)  # High value for promotion
        if abs(move.pieceMoved) == 2 or abs(move.pieceMoved) == 4: # Knight or rook
            value += SQUAREVALUES[move.endRow][move.endCol] - SQUAREVALUES[move.startRow][move.startCol]
        if abs(move.pieceMoved) == 1: # Pawn
            value += SQUAREVALUES[move.endRow][move.endCol]
        if move.isCastlingMove:
            value += 5  # High value for castling
        return value
    moves.sort(key=moveValue, reverse=True)