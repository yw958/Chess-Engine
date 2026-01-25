"""
Contains the core logic for representing the chess game state, making and undoing moves,
and generating valid moves.
"""
from .PieceTables import PieceTables
class Move:
    def __init__(self, startSq, endSq, board):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.isCastlingMove = False
        self.isEnPassantMove = False
        self.pawnPromotion = 0
        self.isCheck = False # True if this move gives check to opponent directly (without discovered check)
        self.discoveredCheck = None # None means no discovered check. If there is discovered check, it stores the square of the checking piece
    def getChessNotation(self):
        # Simple chess notation (e.g., "e4" for pawn move to e4)
        str_return = ""
        if self.isCastlingMove:
            if self.endCol == 6:
                str_return = "O-O"
            else:
                str_return = "O-O-O"
        elif self.isEnPassantMove:
            str_return = f"{chr(ord('a') + self.startCol)}{8 - self.startRow}x{chr(ord('a') + self.endCol)}{8 - self.endRow} e.p."
        elif self.pawnPromotion:
            if self.pieceCaptured != 0:
                str_return = f"{chr(ord('a') + self.startCol)}x{chr(ord('a') + self.endCol)}{8 - self.endRow}={PieceTables.PIECES[abs(self.pawnPromotion)]}"
            str_return = f"{chr(ord('a') + self.startCol)}{8 - self.startRow}{chr(ord('a') + self.endCol)}{8 - self.endRow}={PieceTables.PIECES[abs(self.pawnPromotion)]}"
        elif self.pieceCaptured != 0:
            pieceChar = '' if abs(self.pieceMoved) == 1 else PieceTables.PIECES[abs(self.pieceMoved)]
            str_return = f"{pieceChar}{chr(ord('a') + self.startCol)}x{chr(ord('a') + self.endCol)}{8 - self.endRow}"
        else:
            str_return = f"{chr(ord('a') + self.startCol)}{8 - self.startRow} -> {chr(ord('a') + self.endCol)}{8 - self.endRow}"
        if self.isCheck or self.discoveredCheck:
            str_return += "+"
        return str_return

    def __str__(self):
        return self.getChessNotation()
    
class Info:
    def __init__(self):
        self.castlingRights = [(False,False), (True, True), (True, True)] # index 0 unused, 1 for white, -1 for black; each tuple is (king side, queen side)
        self.kingLocations = [(0,0), (7, 4), (0, 4)] # track kings' positions for check detection, index 0 unused, 1 for white, -1 for black
        self.inCheck = [False, False, False] # is white in check, is black in check
        self.block_mask = [set(),set(),set()]
        self.enPassantPossible = () # coordinates for the square where en passant capture is possible
        self.winner = None # None, 1 for white win, -1 for black win, 0 for draw
        self.seventyFiveMoveRuleCounter = 0 # counts half-moves since last pawn move or capture for 75-move rule
        self.checkSquares = [set(),set(),set(),set(),set(),set()] # squares that put the enemy king in check. Index 0 unused, 1-5 for piece types
        self.potentialPins = set() # squares where pieces are potentially pinned
        self.eval = 0 # evaluation score of the position
    def copy(self):
        new = Info()
        new.castlingRights = self.castlingRights[:]     
        new.kingLocations = self.kingLocations[:]       
        new.inCheck = self.inCheck[:]
        new.block_mask = [s.copy() for s in self.block_mask]
        new.enPassantPossible = self.enPassantPossible
        new.winner = self.winner
        new.seventyFiveMoveRuleCounter = self.seventyFiveMoveRuleCounter
        new.checkSquares = [s.copy() for s in self.checkSquares]
        new.potentialPins = self.potentialPins.copy()
        new.eval = self.eval
        return new
    
class GameState:
    def __init__(self):
        # We represent each piece with an integer. White pieces are positive, and black pieces are negative.
        self.board = [
            [-4, -2, -3, -5, -6, -3, -2, -4],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 1,  1,  1,  1,  1,  1,  1,  1],
            [ 4,  2,  3,  5,  6,  3,  2,  4]
        ]
        # Piece codes: 1 = Pawn, 2 = Knight, 3 = Bishop, 4 = Rook, 5 = Queen, 6 = King
        self.player = 1 # 1 for white, -1 for black
        self.moveLog = []
        self.infoLog = []
        self.info = Info()
        self.boardHistory = []
        self.boardCounter = {}
        self.validMoves = []
        boardRep = self.scanAndUpdate()
        self.boardCounter[boardRep] = 1
        self.boardHistory.append(boardRep)

    def scanAndUpdate(self):
        """
        Does all the updates that require board scanning in one pass.
        Update board representation, evaluation, and valid moves. Also check for dead positions.
        Note: the score update is not final. Game status will be updated again after move generation.
        Return a string representation of the board for repetition detection.
        """
        ranks_str = []
        self.validMoves = []
        score = 0
        pieces = []
        possibleDead = True
        bishopColorBlack = None
        bishopColorWhite = None
        player = self.player
        fac = 0.1 # factor for positional score
        for r in range(8):
            parts = []
            empty = 0
            for c in range(8):
                sq = self.board[r][c]
                if sq == 0:
                    empty += 1
                else:
                    #Update parts for FEN
                    parts.append(PieceTables.PIECES[sq])
                    #Update Score
                    posScore = 0
                    if empty:
                        parts.append(str(empty))
                        empty = 0
                    if abs(sq) != 6:
                        posScore = PieceTables.positionalScores[sq][r][c] * fac
                    score += ( PieceTables.VALUES[abs(sq)] + posScore ) * (1 if sq > 0 else -1)
                    # Check for dead position
                    if possibleDead:
                        pieces.append(self.board[r][c])
                        if len(pieces) > 4:
                            possibleDead = False
                        elif abs(self.board[r][c]) == 5 or (abs(self.board[r][c]) ==4 
                        or abs(self.board[r][c]) ==1):
                            possibleDead = False
                        elif self.board[r][c] == -3:
                            bishopColorBlack = (r + c) % 2
                        elif self.board[r][c] == 3:
                            bishopColorWhite = (r + c) % 2
                    # Update valid moves for the player to move
                    if (self.board[r][c] > 0) == (player > 0):
                        self.updateValidMoves((r, c))
            #Finish board representation for the current rank
            if empty:
                parts.append(str(empty))
            ranks_str.append(''.join(parts))
        #Finish board representation
        placement = '/'.join(ranks_str)
        stm = 'w' if self.player == 1 else 'b'
        # --- castling rights ---
        # index 1 -> white, index 2 -> black (since index 0 unused)
        w_k, w_q = self.info.castlingRights[1]
        b_k, b_q = self.info.castlingRights[2]
        castle_parts = []
        if w_k: castle_parts.append('K')
        if w_q: castle_parts.append('Q')
        if b_k: castle_parts.append('k')
        if b_q: castle_parts.append('q')
        castling = ''.join(castle_parts) if castle_parts else '-'
        # --- en passant target square ---
        # enPassantPossible is () or (row, col)
        if self.info.enPassantPossible:
            r, c = self.info.enPassantPossible
            ep = f"{chr(ord('a') + c)}{8 - r}"
        else:
            ep = '-'
        #Update eval
        self.info.eval = score
        #Check for dead position (insufficient material)
        if possibleDead:
            if len(pieces) == 2: #K vs K
                self.info.winner = 0 # Draw
                self.info.eval = 0
                self.validMoves = []
            else:
                pieces.sort()
                # K vs K + N or K vs K + B
                if len(pieces) == 3 and (pieces == [-6, 3, 6] or pieces == [-6, -3, 6] 
                                         or pieces == [-6, 2, 6] or pieces == [-6, -2, 6]):
                    self.info.winner = 0 # Draw
                    self.info.eval = 0
                    self.validMoves = []
                # K + B vs K + B (both bishops on same color)
                elif pieces == [-6, -3, 3, 6]:
                    if bishopColorBlack == bishopColorWhite:
                        self.info.winner = 0 # Draw
                        self.info.eval = 0
                        self.validMoves = []
        return(f"{placement} {stm} {castling} {ep}")
        
    def makeMove(self, move: Move):
        if (move.pieceMoved > 0) != (self.player > 0):
            return # Not the player's turn
        self.infoLog.append(self.info.copy())
        self.board[move.startRow][move.startCol] = 0
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move)
        #Handle king moves and castling rights
        if abs(move.pieceMoved) == 6:
            self.info.kingLocations[self.player] = (move.endRow, move.endCol)
            if move.isCastlingMove:
                if move.endCol - move.startCol == 2: # king side
                    self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][7]
                    self.board[move.endRow][7] = 0
                else: # queen side
                    self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][0]
                    self.board[move.endRow][0] = 0
            self.info.castlingRights[self.player] = (False, False)
        #Handle rook moves and castling rights
        elif abs(move.pieceMoved) == 4:
            if move.startCol == 0:
                self.info.castlingRights[self.player] = (self.info.castlingRights[self.player][0], False)
            elif move.startCol == 7:
                self.info.castlingRights[self.player] = (False, self.info.castlingRights[self.player][1])
        #Handle special pawn moves
        elif move.pawnPromotion:
            self.board[move.endRow][move.endCol] = move.pawnPromotion
        elif move.isEnPassantMove:
            self.board[move.endRow + self.player][move.endCol] = 0
        self.info.enPassantPossible = ()
        if abs(move.pieceMoved) == 1 and abs(move.startRow - move.endRow) == 2:
            self.info.enPassantPossible = ( (move.startRow + move.endRow)//2, move.startCol )
        #Handle rook captures and castling rights
        elif abs(move.pieceCaptured) == 4:
            if move.endCol == 0:
                self.info.castlingRights[-self.player] = (self.info.castlingRights[-self.player][0], False)
            elif move.endCol == 7:
                self.info.castlingRights[-self.player] = (False, self.info.castlingRights[-self.player][1])
        # Update 75-move rule counter
        if abs(move.pieceMoved) == 1 or move.pieceCaptured != 0:
            self.info.seventyFiveMoveRuleCounter = 0
        else:
            self.info.seventyFiveMoveRuleCounter += 1
        if self.info.seventyFiveMoveRuleCounter >= 150:
            self.info.winner = 0 # Draw by 75-move rule
            self.info.eval = 0
        self.player *= -1 # switch players
        self.updateKingSafety(self.player, move)
        #Scan for all moves and get board representation
        boardRepresentation = self.scanAndUpdate()
        # Update repetition counter and check for fivefold repetition
        count = self.boardCounter.get(boardRepresentation, 0)
        count += 1
        self.boardCounter[boardRepresentation] = count
        if count >= 5:
            self.info.winner = 0 # Draw by fivefold repetition
            self.info.eval = 0
        #Update board history
        self.boardHistory.append(boardRepresentation)   

        if self.info.winner is None:
            if not self.validMoves:
                if self.info.inCheck[self.player]:
                    self.info.winner = -self.player # Checkmate
                    self.info.eval = float('inf') * (-self.player)
                else:
                    self.info.winner = 0 # Stalemate (draw)
                    self.info.eval = 0
        else:
            self.validMoves = []

        
    def undoMove(self, reCalculateMoves = True):
        if len(self.moveLog) == 0:
            return
        self.player *= -1 # switch players back
        boardRep = self.boardHistory.pop()
        count = self.boardCounter[boardRep] - 1
        if count == 0:
            del self.boardCounter[boardRep]
        else:
            self.boardCounter[boardRep] = count
        move:Move = self.moveLog.pop()
        self.info:Info = self.infoLog.pop()
        self.board[move.startRow][move.startCol] = move.pieceMoved
        if move.isEnPassantMove:
            self.board[move.endRow + self.player][move.endCol] = move.pieceCaptured
            self.board[move.endRow][move.endCol] = 0
        else:
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            if move.pieceMoved == 6 or move.pieceMoved == -6:
                self.info.kingLocations[self.player] = (move.startRow, move.startCol)
                if move.isCastlingMove:
                    if move.endCol - move.startCol == 2: # king side
                        self.board[move.endRow][7] = self.board[move.endRow][move.endCol - 1]
                        self.board[move.endRow][move.endCol - 1] = 0
                    else: # queen side
                        self.board[move.endRow][0] = self.board[move.endRow][move.endCol + 1]
                        self.board[move.endRow][move.endCol + 1] = 0
        if reCalculateMoves:
            self.scanAndUpdate()
    
    # Return True if the square is attacked by opponent pieces
    def isAttacked(self, pieceRow, pieceCol, player):
        #Check if attacked by knight
        knightMoves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for move in knightMoves:
            endRow = pieceRow + move[0]
            endCol = pieceCol + move[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                if self.board[endRow][endCol] == -2 * player:
                    return True
        #Check if attacked by bishop/queen (diagonal)
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for direction in directions:
            currRow, currCol = pieceRow, pieceCol
            while True:
                currRow += direction[0]
                currCol += direction[1]
                if 0 <= currRow < 8 and 0 <= currCol < 8:
                    piece = self.board[currRow][currCol]
                    if piece == 0:
                        continue
                    elif piece == -3 * player or piece == -5 * player:
                        return True
                    else:
                        break
                else:
                    break
        #Check if attacked by rook/queen (horizontal/vertical)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for direction in directions:
            currRow, currCol = pieceRow, pieceCol
            while True:
                currRow += direction[0]
                currCol += direction[1]
                if 0 <= currRow < 8 and 0 <= currCol < 8:
                    piece = self.board[currRow][currCol]
                    if piece == 0:
                        continue
                    elif piece == -4 * player or piece == -5 * player:
                        return True
                    else:
                        break
                else:
                    break
        #Check if attacked by pawn
        if 0 <= pieceRow - player < 8:
            if (0 <= pieceCol - 1 < 8 and self.board[pieceRow - player][pieceCol - 1] == -1 * player
                ) or (0 <= pieceCol + 1 < 8 and self.board[pieceRow - player][pieceCol + 1] == -1 * player):
                return True
        #Check if attacked by king
        kingMoves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for move in kingMoves:
            endRow = pieceRow + move[0]
            endCol = pieceCol + move[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                if self.board[endRow][endCol] == -6 * player:
                    return True
        return False
    
    def updateKingSafety(self, player, move: Move):
        kingRow, kingCol = self.info.kingLocations[player]
        self.info.block_mask[player] = set()
        inCheck = False
        attackingPiece = None
        attackingPieceRow = -1
        attackingPieceCol = -1
        if move.isCheck:
            inCheck = True
            attackingPiece = abs(move.pieceMoved)
            attackingPieceRow = move.endRow
            attackingPieceCol = move.endCol
            if move.isCheck and move.discoveredCheck:
                attackingPiece = 7 #indicate multiple attackers
        elif move.discoveredCheck:
            inCheck = True
            if move.isEnPassantMove and move.discoveredCheck == (-1,-1):
                attackingPiece = 7 #indicate multiple attackers
            else:
                attackingPieceRow = move.discoveredCheck[0]
                attackingPieceCol = move.discoveredCheck[1]
                attackingPiece = abs(self.board[attackingPieceRow][attackingPieceCol])
        self.info.inCheck[player] = inCheck
        if inCheck and attackingPiece != 7:
            if attackingPiece in [2, 1, 6]: # knight, pawn, king
                self.info.block_mask[player].add((attackingPieceRow, attackingPieceCol))
            else:
                # Compute the direction from the king to the attacking piece
                directionRow = (attackingPieceRow > kingRow) - (attackingPieceRow < kingRow)
                directionCol = (attackingPieceCol > kingCol) - (attackingPieceCol < kingCol)
                currRow = kingRow + directionRow
                currCol = kingCol + directionCol
                while (currRow, currCol) != (attackingPieceRow, attackingPieceCol):
                    self.info.block_mask[player].add((currRow, currCol))
                    currRow += directionRow
                    currCol += directionCol
                self.info.block_mask[player].add((attackingPieceRow, attackingPieceCol))
        # Update potential pins
        dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        self.info.potentialPins = set()
        for direction in dirs:
            currRow, currCol = kingRow, kingCol
            while True:
                currRow += direction[0]
                currCol += direction[1]
                if 0 <= currRow < 8 and 0 <= currCol < 8:
                    piece = self.board[currRow][currCol]
                    if piece == 0:
                        continue
                    elif (piece > 0) == (player > 0): # friendly piece
                        self.info.potentialPins.add((currRow, currCol))
                        break
                    else:  # enemy piece
                        break
                else:
                    break
        #Update Check squares
        self.updateCheckSquares(player)

    def updateCheckSquares(self, player):
        #Update check squares for the enemy king for move generation
        self.info.checkSquares = [set(),set(),set(),set(),set(),set()]
        enemyKingR, enemyKingC = self.info.kingLocations[-player]
        #Pawns
        dirs = [(player, -1), (player, 1)]
        for d in dirs:
            r = enemyKingR + d[0]
            c = enemyKingC + d[1]
            if 0 <= r < 8 and 0 <= c < 8:
                self.info.checkSquares[1].add((r, c))
        #Knights
        knightMoves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for move in knightMoves:
            r = enemyKingR + move[0]
            c = enemyKingC + move[1]
            if 0 <= r < 8 and 0 <= c < 8:
                self.info.checkSquares[2].add((r, c))
        #Bishops/Queens (diagonal)
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for direction in directions:
            currRow, currCol = enemyKingR, enemyKingC
            while True:
                currRow += direction[0]
                currCol += direction[1]
                if 0 <= currRow < 8 and 0 <= currCol < 8:
                    piece = self.board[currRow][currCol]
                    if piece == 0:
                        self.info.checkSquares[3].add((currRow, currCol))
                        self.info.checkSquares[5].add((currRow, currCol))
                    else:
                        self.info.checkSquares[3].add((currRow, currCol))
                        self.info.checkSquares[5].add((currRow, currCol))
                        break
                else:
                    break
        #Rooks/Queens (horizontal/vertical)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for direction in directions:
            currRow, currCol = enemyKingR, enemyKingC
            while True:
                currRow += direction[0]
                currCol += direction[1]
                if 0 <= currRow < 8 and 0 <= currCol < 8:
                    piece = self.board[currRow][currCol]
                    if piece == 0:
                        self.info.checkSquares[4].add((currRow, currCol))
                        self.info.checkSquares[5].add((currRow, currCol))
                    else:
                        self.info.checkSquares[4].add((currRow, currCol))
                        self.info.checkSquares[5].add((currRow, currCol))
                        break
                else:
                    break
    
    def updateValidMoves(self, position):
        row, col = position
        piece = self.board[row][col]
        if piece == 0 or (piece > 0) != (self.player > 0):
            return [] # No piece or not the player's piece
        if self.info.inCheck[self.player] and not self.info.block_mask[self.player]:
            if piece == 6 or piece == -6:
                return self.getKingMoves(row, col, self.player)
            return [] # In double check, only king moves allowed
        if abs(piece) == 1:
            return self.getPawnMoves(row, col, self.player)
        if abs(piece) == 2:
            return self.getKnightMoves(row, col, self.player)
        if abs(piece) == 3 or abs(piece) == 4 or abs(piece) == 5:
            return self.getRayMoves(row, col, self.player, piece)
        if abs(piece) == 6:
            return self.getKingMoves(row, col, self.player)
        return []
    
    def checkMoveSafety(self, move: Move, player):
        self.board[move.startRow][move.startCol] = 0
        self.board[move.endRow][move.endCol] = move.pieceMoved
        if move.isEnPassantMove:
            self.board[move.endRow + player][move.endCol] = 0
        if move.pieceMoved * player == 6:
            kingRow, kingCol = move.endRow, move.endCol
        else:
            kingRow, kingCol = self.info.kingLocations[player]
        inCheck = self.isAttacked(kingRow, kingCol, player)
        if move.isEnPassantMove:
            self.board[move.endRow + player][move.endCol] = move.pieceCaptured
            self.board[move.endRow][move.endCol] = 0
        else:
            self.board[move.endRow][move.endCol] = move.pieceCaptured
        self.board[move.startRow][move.startCol] = move.pieceMoved
        return not inCheck
    
    def isPinned(self, move: Move, player):
        """
        Return True if the piece being moved is pinned to the king
        """
        if (move.startRow, move.startCol) not in self.info.potentialPins:
            return False
        kingRow = self.info.kingLocations[player][0]
        kingCol = self.info.kingLocations[player][1]
        pinnedDirectionRow = (move.startRow > kingRow) - (move.startRow < kingRow)
        pinnedDirectionCol = (move.startCol > kingCol) - (move.startCol < kingCol)
        moveDirectionRow = (move.endRow > move.startRow) - (move.endRow < move.startRow)
        moveDirectionCol = (move.endCol > move.startCol) - (move.endCol < move.startCol)
        if (pinnedDirectionRow, pinnedDirectionCol) == (moveDirectionRow, moveDirectionCol) or (
            pinnedDirectionRow, pinnedDirectionCol) == (-moveDirectionRow, -moveDirectionCol):
            return False
        currRow, currCol = move.startRow, move.startCol
        while True:
            currRow += pinnedDirectionRow
            currCol += pinnedDirectionCol
            if 0 <= currRow < 8 and 0 <= currCol < 8:
                piece = self.board[currRow][currCol]
                if piece == 0:
                    continue
                elif (piece > 0) == (player > 0): # friendly piece
                    break
                else:  # enemy piece
                    if pinnedDirectionRow == 0 or pinnedDirectionCol == 0:
                        if piece == -4 * player or piece == -5 * player:
                            return True
                    else:
                        if piece == -3 * player or piece == -5 * player:
                            return True
                    break
            else:
                break

    def discoveredCheck(self, move: Move, player):
        if (move.startRow, move.startCol) not in self.info.checkSquares[5]:
            if move.isEnPassantMove:
                #Check for single discovered check via en passant
                enPassantRow = move.endRow + player
                enPassantCol = move.endCol
                if (enPassantRow, enPassantCol) in self.info.checkSquares[3]:
                    return self.discoveredCheck(Move((enPassantRow, enPassantCol), 
                                                     (move.endRow, enPassantCol),
                                                     self.board), player)
            return None
        kingRow, kingCol = self.info.kingLocations[-player]
        directionRow = (move.startRow > kingRow) - (move.startRow < kingRow)
        directionCol = (move.startCol > kingCol) - (move.startCol < kingCol)
        moveDirRow = (move.endRow > move.startRow) - (move.endRow < move.startRow)
        moveDirCol = (move.endCol > move.startCol) - (move.endCol < move.startCol)
        if abs(move.pieceMoved)!=2 and ((directionRow, directionCol) == (moveDirRow, moveDirCol) or (
            directionRow, directionCol) == (-moveDirRow, -moveDirCol)):
            return None # Moving away or along the line, no discovered check
        currRow, currCol = move.startRow, move.startCol
        while True:
            currRow += directionRow
            currCol += directionCol
            if 0 <= currRow < 8 and 0 <= currCol < 8:
                piece = self.board[currRow][currCol]
                if piece == 0:
                    continue
                elif (piece > 0) != (player > 0): # enemy piece
                    break
                else:  # friendly piece
                    if directionRow == 0 or directionCol == 0:
                        if piece == 4 * player or piece == 5 * player:
                            #Check for Double discovered check (extremely rare)
                            if move.isEnPassantMove:
                                enPassantRow = move.endRow + player
                                enPassantCol = move.endCol
                                if (enPassantRow, enPassantCol) in self.info.checkSquares[3]:
                                    if self.discoveredCheck(Move((enPassantRow, enPassantCol), 
                                                                     (move.endRow, enPassantCol),self.board), 
                                                                     player):
                                        return (-1,-1) 
                            return (currRow, currCol)
                    else:
                        if piece == 3 * player or piece == 5 * player:
                            #Check for Double discovered check (extremely rare)
                            if move.isEnPassantMove:
                                enPassantRow = move.endRow + player
                                enPassantCol = move.endCol
                                if (enPassantRow, enPassantCol) in self.info.checkSquares[3]:
                                    if self.discoveredCheck(Move((enPassantRow, enPassantCol), 
                                                                     (move.endRow, enPassantCol),self.board), 
                                                                     player):
                                        return (-1,-1) 
                            return (currRow, currCol)
                    break
            else:
                break
        if move.isEnPassantMove:
            #Check for single discovered check via en passant
            enPassantRow = move.endRow + player
            enPassantCol = move.endCol
            if (enPassantRow, enPassantCol) in self.info.checkSquares[3]: # Single discovered check via en passant
                return self.discoveredCheck(Move((enPassantRow, enPassantCol), (move.endRow, enPassantCol),self.board), player)
        return None

    def getPawnMoves(self, row, col, player):
        inCheck = self.info.inCheck[player]
        startRow = 6 if player == 1 else 1
        if self.board[row - player][col] == 0:
            move = Move((row, col), (row - player, col), self.board)
            if not self.isPinned(move, player):
                if not inCheck or (row - player, col) in self.info.block_mask[player]:
                    if row - player == 0 or row - player == 7:
                        for promoPiece in [5,4,3,2]: # promote to queen, rook, bishop, knight
                            move = Move((row, col), (row - player, col), self.board)
                            move.pawnPromotion = promoPiece * player
                            move.isCheck = (row - player, col) in self.info.checkSquares[promoPiece]
                            move.discoveredCheck = self.discoveredCheck(move, player)
                            self.validMoves.append(move)
                    else:
                        move.isCheck = (row - player, col) in self.info.checkSquares[1]
                        move.discoveredCheck = self.discoveredCheck(move, player)
                        self.validMoves.append(move)
                if row == startRow and self.board[row - 2 * player][col] == 0:
                    move = Move((row, col), (row - 2 * player, col), self.board)
                    if not inCheck or (row - 2 * player, col) in self.info.block_mask[player]:
                        move.isCheck = (row - 2 * player, col) in self.info.checkSquares[1]
                        move.discoveredCheck = self.discoveredCheck(move, player)
                        self.validMoves.append(move)
        for dc in [-1, 1]:
            if 0 <= col + dc < 8:
                if self.board[row - player][col + dc] * player < 0:
                    move = Move((row, col), (row - player, col + dc), self.board)
                    if not self.isPinned(move, player):
                        if not inCheck or (row - player, col + dc) in self.info.block_mask[player]:
                            if row - player == 0 or row - player == 7:
                                for promoPiece in [5,4,3,2]: # promote to queen, rook, bishop, knight
                                    move = Move((row, col), (row - player, col + dc), self.board)
                                    move.pawnPromotion = promoPiece * player
                                    move.isCheck = (row - player, col + dc) in self.info.checkSquares[promoPiece]
                                    move.discoveredCheck = self.discoveredCheck(move, player)
                                    self.validMoves.append(move)
                            else:
                                move.isCheck = (row - player, col + dc) in self.info.checkSquares[1]
                                move.discoveredCheck = self.discoveredCheck(move, player)
                                self.validMoves.append(move)
                elif (row - player, col + dc) == self.info.enPassantPossible:
                    move = Move((row, col), (row - player, col + dc), self.board)
                    move.isEnPassantMove = True
                    move.pieceCaptured = -1 * player
                    if not self.isPinned(move, player):
                        if not inCheck or (row - player, col + dc) in self.info.block_mask[player]:
                            move.isCheck = (row - player, col + dc) in self.info.checkSquares[1]
                            move.discoveredCheck = self.discoveredCheck(move, player)
                            self.validMoves.append(move)
    
    def getKnightMoves(self, row, col, player):
        knightMoves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        #Return if pinned
        if self.isPinned(Move((row, col), (row, col), self.board), player):
            return
        inCheck = self.info.inCheck[player]
        for moveOffset in knightMoves:
            endRow = row + moveOffset[0]
            endCol = col + moveOffset[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8 and self.board[endRow][endCol] * player <= 0:
                move = Move((row, col), (endRow, endCol), self.board)
                if not inCheck or (endRow, endCol) in self.info.block_mask[player]:
                    move.isCheck = (endRow, endCol) in self.info.checkSquares[2]
                    move.discoveredCheck = self.discoveredCheck(move, player)
                    self.validMoves.append(move)
    
    def getRayMoves(self, row, col, player, piece):
        if abs(piece) == 3: #Bishop
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        elif abs(piece) == 4: #Rook
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        elif abs(piece) == 5: #Queen
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
        else:
            return
        inCheck = self.info.inCheck[player]
        for direction in directions:
            currRow, currCol = row + direction[0], col + direction[1]
            if 0 <= currRow < 8 and 0 <= currCol < 8:
                if self.board[currRow][currCol] * player > 0:
                    continue
                move = Move((row, col), (currRow, currCol), self.board)
                if not self.isPinned(move, player):
                    if not inCheck or (currRow, currCol) in self.info.block_mask[player]:
                        move.isCheck = (currRow, currCol) in self.info.checkSquares[abs(piece)]
                        move.discoveredCheck = self.discoveredCheck(move, player)
                        self.validMoves.append(move)
                    if self.board[currRow][currCol] * player < 0:
                        continue
                    while True:
                        currRow += direction[0]
                        currCol += direction[1]
                        if 0 <= currRow < 8 and 0 <= currCol < 8:
                            if self.board[currRow][currCol] * player > 0:
                                break
                            move = Move((row, col), (currRow, currCol), self.board)
                            if not inCheck or (currRow, currCol) in self.info.block_mask[player]:
                                move.isCheck = (currRow, currCol) in self.info.checkSquares[abs(piece)]
                                move.discoveredCheck = self.discoveredCheck(move, player)
                                self.validMoves.append(move)
                            if self.board[currRow][currCol] * player < 0:
                                break
                        else:
                            break
    
    def getKingMoves(self, row, col, player):
        kingMoves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for moveOffset in kingMoves:
            endRow = row + moveOffset[0]
            endCol = col + moveOffset[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8 and self.board[endRow][endCol] * player <= 0:
                move = Move((row, col), (endRow, endCol), self.board)
                if self.checkMoveSafety(move, player):
                    move.discoveredCheck = self.discoveredCheck(move, player)
                    self.validMoves.append(move)
        if not self.info.inCheck[player]:
            if self.info.castlingRights[player][0]: #king side
                if self.board[row][col + 1] == 0 and self.board[row][col + 2] == 0:
                    if not self.isAttacked(row, col + 1, player) and not self.isAttacked(row, col + 2, player):
                        move = Move((row, col), (row, col + 2), self.board)
                        move.isCastlingMove = True
                        if (row, col + 1) in self.info.checkSquares[4]:
                            move.discoveredCheck = (row, col + 1)
                        self.validMoves.append(move)
            if self.info.castlingRights[player][1]: #queen side
                if self.board[row][col - 1] == 0 and self.board[row][col - 2] == 0 and self.board[row][col - 3] == 0:
                    if not self.isAttacked(row, col - 1, player) and not self.isAttacked(row, col - 2, player):
                        move = Move((row, col), (row, col - 2), self.board)
                        move.isCastlingMove = True
                        if (row, col - 1) in self.info.checkSquares[4]:
                            move.discoveredCheck = (row, col - 1)
                        self.validMoves.append(move)

    #Legacy: A more detailed version of isAttacked that also returns the attacking piece and its location
    def findAttackers(self, pieceRow, pieceCol, player):
        #Check if attacked by pawn
        isAttacked = False
        attackingPiece = None
        attackingPieceRow = -1
        attackingPieceCol = -1
        if 0 <= pieceRow - player < 8:
            if 0 <= pieceCol - 1 < 8 and self.board[pieceRow - player][pieceCol - 1] == -1 * player:
                isAttacked = True
                attackingPiece = 1
                attackingPieceRow = pieceRow - player
                attackingPieceCol = pieceCol - 1
            elif 0 <= pieceCol + 1 < 8 and self.board[pieceRow - player][pieceCol + 1] == -1 * player:
                isAttacked = True
                attackingPiece = 1
                attackingPieceRow = pieceRow - player
                attackingPieceCol = pieceCol + 1
        #Check if attacked by knight
        knightMoves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for move in knightMoves:
            endRow = pieceRow + move[0]
            endCol = pieceCol + move[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                if self.board[endRow][endCol] == -2 * player:
                    isAttacked = True
                    attackingPiece = 2
                    attackingPieceRow = endRow
                    attackingPieceCol = endCol
                    break
        #Check if attacked by rook/queen (horizontal/vertical)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for direction in directions:
            currRow, currCol = pieceRow, pieceCol
            while True:
                currRow += direction[0]
                currCol += direction[1]
                if 0 <= currRow < 8 and 0 <= currCol < 8:
                    piece = self.board[currRow][currCol]
                    if piece == 0:
                        continue
                    elif piece == -4 * player:
                        if isAttacked:
                            attackingPiece = 7 #indicate multiple attackers
                            return True, attackingPiece, attackingPieceRow, attackingPieceCol
                        isAttacked = True
                        attackingPiece = 4
                        attackingPieceRow = currRow
                        attackingPieceCol = currCol
                        break
                    elif piece == -5 * player:
                        if isAttacked:
                            attackingPiece = 7 #indicate multiple attackers
                            return True, attackingPiece, attackingPieceRow, attackingPieceCol
                        isAttacked = True
                        attackingPiece = 5
                        attackingPieceRow = currRow
                        attackingPieceCol = currCol
                        break
                    else:
                        break
                else:
                    break
        #Check if attacked by bishop/queen (diagonal)
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for direction in directions:
            currRow, currCol = pieceRow, pieceCol
            while True:
                currRow += direction[0]
                currCol += direction[1]
                if 0 <= currRow < 8 and 0 <= currCol < 8:
                    piece = self.board[currRow][currCol]
                    if piece == 0:
                        continue
                    elif piece == -3 * player:
                        if isAttacked:
                            attackingPiece = 7 #indicate multiple attackers
                            return True, attackingPiece, attackingPieceRow, attackingPieceCol
                        isAttacked = True
                        attackingPiece = 3
                        attackingPieceRow = currRow
                        attackingPieceCol = currCol
                        break
                    elif piece == -5 * player:
                        if isAttacked:
                            attackingPiece = 7 #indicate multiple attackers
                            return True, attackingPiece, attackingPieceRow, attackingPieceCol
                        isAttacked = True
                        attackingPiece = 5
                        attackingPieceRow = currRow
                        attackingPieceCol = currCol
                        break
                    else:
                        break
                else:
                    break
        return isAttacked, attackingPiece, attackingPieceRow, attackingPieceCol