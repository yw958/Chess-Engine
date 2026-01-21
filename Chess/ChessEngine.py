"""
A module containing the minimax algorithm with alpha-beta pruning for chess.
"""


from Chess import ChessBackend

class Engine:
    def __init__(self):
        self.knightScores = [
            [1, 1, 1, 1, 1, 1, 1, 1],
            [1, 2, 2, 2, 2, 2, 2, 1],
            [1, 2, 3, 3, 3, 3, 2, 1],
            [1, 2, 3, 4, 4, 3, 2, 1],
            [1, 2, 3, 4, 4, 3, 2, 1],
            [1, 2, 3, 3, 3, 3, 2, 1],
            [1, 2, 2, 2, 2, 2, 2, 1],
            [1, 1, 1, 1, 1, 1, 1, 1],
        ]

        self.bishopScores = [
            [4, 3, 2, 1, 1, 2, 3, 4],
            [3, 4, 3, 2, 2, 3, 4, 3],
            [2, 3, 4, 3, 3, 4, 3, 2],
            [1, 2, 3, 4, 4, 3, 2, 1],
            [1, 2, 3, 4, 4, 3, 2, 1],
            [2, 3, 4, 3, 3, 4, 3, 2],
            [3, 4, 3, 2, 2, 3, 4, 3],
            [4, 3, 2, 1, 1, 2, 3, 4],
        ]

        self.queenScores = [
            [1, 1, 1, 3, 1, 1, 1, 1],
            [1, 2, 3, 3, 3, 1, 1, 1],
            [1, 4, 3, 3, 3, 4, 2, 1],
            [1, 2, 3, 3, 3, 2, 2, 1],
            [1, 2, 3, 3, 3, 2, 2, 1],
            [1, 4, 3, 3, 3, 4, 2, 1],
            [1, 1, 2, 3, 3, 1, 1, 1],
            [1, 1, 1, 3, 1, 1, 1, 1],
        ]

        self.rookScores = [
            [4, 3, 4, 4, 4, 4, 3, 4],
            [4, 4, 4, 4, 4, 4, 4, 4],
            [1, 1, 2, 3, 3, 2, 1, 1],
            [1, 2, 3, 4, 4, 3, 2, 1],
            [1, 2, 3, 4, 4, 3, 2, 1],
            [1, 1, 2, 3, 3, 2, 1, 1],
            [4, 4, 4, 4, 4, 4, 4, 4],
            [4, 3, 4, 4, 4, 4, 3, 4],
        ]

        self.whitePawnScores = [
            [8, 8, 8, 8, 8, 8, 8, 8],
            [8, 8, 8, 8, 8, 8, 8, 8],
            [5, 6, 6, 7, 7, 6, 6, 5],
            [2, 3, 3, 5, 5, 3, 3, 2],
            [1, 2, 3, 4, 4, 3, 2, 1],
            [1, 1, 2, 3, 3, 2, 1, 1],
            [1, 1, 1, 0, 0, 1, 1, 1],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]

        self.blackPawnScores = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 2, 3, 3, 2, 1, 1],
            [1, 2, 3, 4, 4, 3, 2, 1],
            [2, 3, 3, 5, 5, 3, 3, 2],
            [5, 6, 6, 7, 7, 6, 6, 5],
            [8, 8, 8, 8, 8, 8, 8, 8],
            [8, 8, 8, 8, 8, 8, 8, 8],
        ]

        self.memo = {}

    def miniMax(self, gameState: ChessBackend.GameState, depth: int, alpha: float, beta: float, player) -> float:
        boardRep = gameState.boardHistory[-1]
        if (boardRep, depth) in self.memo:
            return self.memo[(boardRep, depth)]
        if depth == 0 or gameState.info.winner is not None:
            self.memo[(boardRep, depth)] = gameState.info.eval
            return gameState.info.eval
        allMoves = []
        pruned = False
        for moves in gameState.info.validMoves.values():
            allMoves += moves
        self.sortMoves(allMoves)
        if player == 1:
            maxEval = float('-inf')
            for move in allMoves:
                gameState.makeMove(move)
                eval = self.miniMax(gameState, depth - 1, alpha, beta, -1)
                gameState.undoMove(reCalculateMoves=False)
                maxEval = max(maxEval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    pruned = True
                    break
            if not pruned:
                self.memo[(boardRep, depth)] = maxEval
            return maxEval
        else:
            minEval = float('inf')
            for move in allMoves:
                gameState.makeMove(move)
                eval = self.miniMax(gameState, depth - 1, alpha, beta, 1)
                gameState.undoMove(reCalculateMoves=False)
                minEval = min(minEval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    pruned = True
                    break
            if not pruned:
                self.memo[(boardRep, depth)] = minEval
            return minEval
    
    def findBestMove(self,gameState: ChessBackend.GameState, depth: int) -> ChessBackend.Move:
        bestMove = None
        allMoves = []
        for moves in gameState.info.validMoves.values():
            allMoves += moves
        self.sortMoves(allMoves)
        if gameState.player == 1:
            maxEval = float('-inf')
            for move in allMoves:
                gameState.makeMove(move)
                eval = self.miniMax(gameState, depth - 1, float('-inf'), float('inf'), -1)
                gameState.undoMove(reCalculateMoves=False)
                if eval > maxEval:
                    maxEval = eval
                    bestMove = move
        else:
            minEval = float('inf')
            for move in allMoves:
                gameState.makeMove(move)
                eval = self.miniMax(gameState, depth - 1, float('-inf'), float('inf'), 1)
                gameState.undoMove(reCalculateMoves=False)
                if eval < minEval:
                    minEval = eval
                    bestMove = move
        if bestMove is None: # Mate in a few steps
            bestMove = allMoves[0]
        return bestMove

    def sortMoves(self, moves: list[ChessBackend.Move]):
        # Sort moves to prioritize captures and center control
        def moveValue(move: ChessBackend.Move):
            value = 0
            if move.pieceCaptured != 0:
                value += 10 * abs(move.pieceCaptured) - abs(move.pieceMoved)
            if move.pawnPromotion != 0:
                value += 10 * abs(move.pawnPromotion)  # High value for promotion
            if move.pieceMoved == 1:
                value += self.whitePawnScores[move.endRow][move.endCol] - self.whitePawnScores[move.startRow][move.startCol]
            elif move.pieceMoved == -1:
                value += self.blackPawnScores[move.endRow][move.endCol] - self.blackPawnScores[move.startRow][move.startCol]
            elif abs(move.pieceMoved) == 2:
                value += self.knightScores[move.endRow][move.endCol] - self.knightScores[move.startRow][move.startCol]
            elif abs(move.pieceMoved) == 3:
                value += self.bishopScores[move.endRow][move.endCol] - self.bishopScores[move.startRow][move.startCol]
            elif abs(move.pieceMoved) == 4:
                value += self.rookScores[move.endRow][move.endCol] - self.rookScores[move.startRow][move.startCol]
            elif abs(move.pieceMoved) == 5:
                value += self.queenScores[move.endRow][move.endCol] - self.queenScores[move.startRow][move.startCol]
            elif move.isCastlingMove:
                value += 5  # High value for castling
            return value
        moves.sort(key=moveValue, reverse=True)