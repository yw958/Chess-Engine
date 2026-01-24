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
        self.nodesSearched = 0
        self.nodesFromMemo = 0
        self.nodesQSearched = 0
        self.memo = {}

    def negamax(self, gameState: ChessBackend.GameState, depth: int, alpha: float, beta: float, color: int) -> float:
        """
        Negamax with alpha-beta pruning.
        `color` = +1 if we want evaluation from White perspective,
                -1 if from Black perspective,
        assuming gameState.info.eval is positive for White.
        """
        self.nodesSearched += 1
        boardRep = gameState.boardHistory[-1]
        if (boardRep, depth) in self.memo:
            self.nodesFromMemo += 1
            return self.memo[(boardRep, depth)]
        if depth == 0 or gameState.info.winner is not None:
            return self.qSearch(gameState, alpha, beta, color)
        allMoves = gameState.validMoves.copy()
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
                return best  # beta cutoff
        self.memo[(boardRep, depth)] = best
        return best

    def findBestMove(self, gameState: ChessBackend.GameState, depth: int) -> ChessBackend.Move:
        bestMove = None
        self.nodesSearched = 0
        self.nodesFromMemo = 0
        self.nodesQSearched = 0
        allMoves = gameState.validMoves.copy()
        self.sortMoves(allMoves)
        # color based on who's to move at root
        color = gameState.player
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
                alpha = score
        if bestMove is None and allMoves:
            bestMove = allMoves[0]
        return bestMove

    def sortMoves(self, moves: list[ChessBackend.Move]):
        # Sort moves to prioritize captures and center control
        def moveValue(move: ChessBackend.Move):
            value = 0
            if move.isCheck:
                value += 100  # High value for checks
            if move.discoveredCheck:
                value += 100  # High value for discovered checks
            if move.pieceCaptured != 0:
                value += 10 * abs(move.pieceCaptured) - abs(move.pieceMoved)
            if move.pawnPromotion != 0:
                value += 20 * abs(move.pawnPromotion)  # High value for promotion
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

    def qSearch(self, gs: ChessBackend.GameState, alpha, beta, color, qply_limit=20):
        """
        Quiescence search to extend the search in volatile positions.
        """
        self.nodesQSearched += 1
        if gs.info.winner is not None or qply_limit <= 0:
            return color * gs.info.eval
        in_check = gs.info.inCheck[color]
        stand_pat = color * gs.info.eval
        if in_check:
            best = float("-inf")
            moves = gs.validMoves.copy()
        else:
            if stand_pat >= beta:
                return stand_pat
            if stand_pat > alpha:
                alpha = stand_pat
            best = stand_pat
            moves = [m for m in gs.validMoves if (m.pieceCaptured != 0 or m.pawnPromotion != 0)]
        if not moves:
            return stand_pat
        self.sortMoves(moves)
        a = alpha
        for m in moves:
            gs.makeMove(m)
            score = -self.qSearch(gs, -beta, -a, -color, qply_limit - 1)
            gs.undoMove(reCalculateMoves=False)
            if score > best:
                best = score
            if score > a:
                a = score
            if a >= beta:
                break
        return best