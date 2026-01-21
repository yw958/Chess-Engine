"""
Contains the chess engine implementing a negamax algorithm with alpha-beta pruning
"""
import ChessBackend

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

    def negamax(self, gameState: ChessBackend.GameState, depth: int, alpha: float, beta: float, color: int) -> float:
        """
        Negamax with alpha-beta pruning.
        `color` = +1 if we want evaluation from White perspective,
                -1 if from Black perspective,
        assuming gameState.info.eval is positive for White.
        """
        boardRep = gameState.boardHistory[-1]
        pruned = False
        if (boardRep, depth) in self.memo:
            return self.memo[(boardRep, depth)]
        if depth == 0 or gameState.info.winner is not None:
            val = color * gameState.info.eval
            self.memo[(boardRep, depth)] = val
            return val
        allMoves = []
        for moves in gameState.info.validMoves.values():
            allMoves += moves
        self.sortMoves(allMoves)
        best = float("-inf")
        a = alpha
        for move in allMoves:
            gameState.makeMove(move)
            score = -self.negamax(gameState, depth - 1, -beta, -a, -color)
            gameState.undoMove(reCalculateMoves=False)
            if score > best:
                best = score
            if score > a:
                a = score
            if a >= beta:
                pruned = True
                break  # prune
        if not pruned:
            self.memo[(boardRep, depth)] = best
        return best

    def findBestMove(self, gameState: ChessBackend.GameState, depth: int) -> ChessBackend.Move:
        bestMove = None
        allMoves = []
        for moves in gameState.info.validMoves.values():
            allMoves += moves
        self.sortMoves(allMoves)
        # color based on who's to move at root
        color = 1 if gameState.player == 1 else -1
        bestScore = float("-inf")
        alpha, beta = float("-inf"), float("inf")
        for move in allMoves:
            gameState.makeMove(move)
            score = -self.negamax(gameState, depth - 1, -beta, -alpha, -color)
            gameState.undoMove(reCalculateMoves=False)
            if score > bestScore:
                bestScore = score
                bestMove = move
            if score > alpha:
                alpha = score  # root alpha update (optional but helps)
        if bestMove is None and allMoves:
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