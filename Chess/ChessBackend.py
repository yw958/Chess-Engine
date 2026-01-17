"""
Responsible for storing all the information about the current state
of the chess game. Also, be responsible for determining the valid moves at
the current state. And it'll keep a move log.
"""
import numpy as np
PIECES = [None, 'P', 'N', 'B', 'R', 'Q', 'K']
VALUES = [0, 1, 3, 3, 5, 9, 1000]

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
    def getChessNotation(self):
        # Simple chess notation (e.g., "e4" for pawn move to e4)
        if self.isCastlingMove:
            if self.endCol == 6:
                return "O-O"
            else:
                return "O-O-O"
        if self.isEnPassantMove:
            return f"{chr(ord('a') + self.startCol)}{8 - self.startRow}x{chr(ord('a') + self.endCol)}{8 - self.endRow} e.p."
        if self.pawnPromotion:
            return f"{chr(ord('a') + self.startCol)}{8 - self.startRow}{chr(ord('a') + self.endCol)}{8 - self.endRow}= {PIECES[abs(self.pawnPromotion)]}"
        if self.pieceCaptured != 0:
            pieceChar = '' if abs(self.pieceMoved) == 1 else PIECES[abs(self.pieceMoved)]
            return f"{pieceChar}{chr(ord('a') + self.startCol)}x{chr(ord('a') + self.endCol)}{8 - self.endRow}"
        return f"{chr(ord('a') + self.startCol)}{8 - self.startRow} -> {chr(ord('a') + self.endCol)}{8 - self.endRow}"
    
class Info:
    def __init__(self):
        self.castlingRights = [(False,False), (True, True), (True, True)] # index 0 unused, 1 for white, -1 for black; each tuple is (king side, queen side)
        self.kingLocations = [(0,0), (7, 4), (0, 4)] # track kings' positions for check detection, index 0 unused, 1 for white, -1 for black
        self.inCheck = [False, False, False] # is white in check, is black in check
        self.block_mask = [set(),set(),set()]
        self.capture_mask = [set(),set(),set()]
        self.enPassantPossible = () # coordinates for the square where en passant capture is possible
        self.validMoves = {} 
    def copy(self):
        new = Info()
        new.castlingRights = self.castlingRights[:]     
        new.kingLocations = self.kingLocations[:]       
        new.inCheck = self.inCheck[:]
        new.block_mask = [s.copy() for s in self.block_mask]
        new.capture_mask = [s.copy() for s in self.capture_mask]
        new.enPassantPossible = self.enPassantPossible
        new.validMoves = {}
        return new
    
class GameState:
    def __init__(self):
        # We represent each piece with an integer. White pieces are positive, and black pieces are negative.
        self.board = np.array([
            [-4, -2, -3, -5, -6, -3, -2, -4],
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 1,  1,  1,  1,  1,  1,  1,  1],
            [ 4,  2,  3,  5,  6,  3,  2,  4]
        ]) # 8x8 2D numpy array
        # Piece codes: 1 = Pawn, 2 = Knight, 3 = Bishop, 4 = Rook, 5 = Queen, 6 = King
        self.player = 1 # 1 for white, -1 for black
        self.moveLog = []
        self.infoLog = []
        self.info = Info()
        self.updateAllValidMoves()
        
    def makeMove(self, move: Move):
        if (move.pieceMoved > 0) != (self.player > 0):
            return # Not the player's turn
        self.infoLog.append(self.info.copy())
        self.board[move.startRow][move.startCol] = 0
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move)
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
        elif abs(move.pieceMoved) == 4:
            if move.startCol == 0:
                self.info.castlingRights[self.player] = (self.info.castlingRights[self.player][0], False)
            elif move.startCol == 7:
                self.info.castlingRights[self.player] = (False, self.info.castlingRights[self.player][1])
        elif move.pawnPromotion:
            self.board[move.endRow][move.endCol] = move.pawnPromotion
        elif move.isEnPassantMove:
                self.board[move.endRow + self.player][move.endCol] = 0
        self.info.enPassantPossible = ()
        if abs(move.pieceMoved) == 1 and abs(move.startRow - move.endRow) == 2:
            self.info.enPassantPossible = ( (move.startRow + move.endRow)//2, move.startCol )
        elif abs(move.pieceCaptured) == 4:
            if move.endCol == 0:
                self.info.castlingRights[-self.player] = (self.info.castlingRights[-self.player][0], False)
            elif move.endCol == 7:
                self.info.castlingRights[-self.player] = (False, self.info.castlingRights[-self.player][1])
        self.player *= -1 # switch players
        self.updateKingSafety(self.player)
        self.updateAllValidMoves()
        
    def undoMove(self):
        if len(self.moveLog) == 0:
            return
        self.player *= -1 # switch players back
        move:Move = self.moveLog.pop()
        self.info:Info = self.infoLog.pop()
        self.board[move.startRow][move.startCol] = move.pieceMoved
        if move.isEnPassantMove:
            self.board[move.endRow + self.player][move.endCol] = move.pieceCaptured
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
        self.updateAllValidMoves()
    
    def isAttacked(self, pieceRow, pieceCol, player):
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
        #Check if attacked by king
        kingMoves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for move in kingMoves:
            endRow = pieceRow + move[0]
            endCol = pieceCol + move[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                if self.board[endRow][endCol] == -6 * player:
                    isAttacked = True
                    attackingPiece = 6
                    attackingPieceRow = endRow
                    attackingPieceCol = endCol
                    break
        return isAttacked, attackingPiece, attackingPieceRow, attackingPieceCol
    
    def updateKingSafety(self, player):
        kingRow, kingCol = self.info.kingLocations[player]
        inCheck, attackingPiece, attackingPieceRow, attackingPieceCol = self.isAttacked(kingRow, kingCol, player)
        self.info.inCheck[player] = inCheck
        self.info.block_mask[player] = set()
        self.info.capture_mask[player] = set()
        if inCheck and attackingPiece != 7:
            if attackingPiece in [2, 1, 6]: # knight, pawn, king
                self.info.capture_mask[player].add((attackingPieceRow, attackingPieceCol))
            else:
                directionRow = np.sign(attackingPieceRow - kingRow)
                directionCol = np.sign(attackingPieceCol - kingCol)
                currRow = kingRow + directionRow
                currCol = kingCol + directionCol
                while (currRow, currCol) != (attackingPieceRow, attackingPieceCol):
                    self.info.block_mask[player].add((currRow, currCol))
                    currRow += directionRow
                    currCol += directionCol
                self.info.capture_mask[player].add((attackingPieceRow, attackingPieceCol))
                
    def updateAllValidMoves(self):
        self.info.validMoves = {}
        for r in range(8):
            for c in range(8):
                if self.board[r][c] != 0 and (self.board[r][c] > 0) == (self.player > 0):
                    moves = self.getValidMoves((r, c))
                    if moves:
                        self.info.validMoves[(r, c)] = moves
    
    def getValidMoves(self, position):
        row, col = position
        piece = self.board[row][col]
        if piece == 0 or (piece > 0) != (self.player > 0):
            return [] # No piece or not the player's piece
        if self.info.inCheck[self.player] and not self.info.capture_mask[self.player] and not self.info.block_mask[self.player]:
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
        if move.pieceMoved == 6 or move.pieceMoved == -6:
            kingRow, kingCol = move.endRow, move.endCol
        else:
            kingRow, kingCol = self.info.kingLocations[player]
        inCheck, _, _, _ = self.isAttacked(kingRow, kingCol, player)
        if move.isEnPassantMove:
            self.board[move.endRow + player][move.endCol] = move.pieceCaptured
            self.board[move.endRow][move.endCol] = 0
        else:
            self.board[move.endRow][move.endCol] = move.pieceCaptured
        self.board[move.startRow][move.startCol] = move.pieceMoved
        return not inCheck

    def getPawnMoves(self, row, col, player):
        moves = []
        startRow = 6 if player == 1 else 1
        if self.board[row - player][col] == 0:
            move = Move((row, col), (row - player, col), self.board)
            if self.checkMoveSafety(move, player):
                if row - player == 0 or row - player == 7:
                    for promoPiece in [5,4,3,2]: # promote to queen, rook, bishop, knight
                        move = Move((row, col), (row - player, col), self.board)
                        move.pawnPromotion = promoPiece * player
                        moves.append(move)
                else:
                    moves.append(move)
            if row == startRow and self.board[row - 2 * player][col] == 0:
                move = Move((row, col), (row - 2 * player, col), self.board)
                if self.checkMoveSafety(move, player):
                    moves.append(move)
        for dc in [-1, 1]:
            if 0 <= col + dc < 8:
                if self.board[row - player][col + dc] * player < 0:
                    move = Move((row, col), (row - player, col + dc), self.board)
                    if self.checkMoveSafety(move, player):
                        if row - player == 0 or row - player == 7:
                            for promoPiece in [5,4,3,2]: # promote to queen, rook, bishop, knight
                                move = Move((row, col), (row - player, col + dc), self.board)
                                move.pawnPromotion = promoPiece * player
                                moves.append(move)
                        else:
                            moves.append(move)
                elif (row - player, col + dc) == self.info.enPassantPossible:
                    move = Move((row, col), (row - player, col + dc), self.board)
                    move.isEnPassantMove = True
                    move.pieceCaptured = -1 * player
                    if self.checkMoveSafety(move, player):
                        moves.append(move)
        return moves
    
    def getKnightMoves(self, row, col, player):
        moves = []
        knightMoves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        if self.info.inCheck[player]: #While in check skip moves that don't block or capture
            for moveOffset in knightMoves:
                endRow = row + moveOffset[0]
                endCol = col + moveOffset[1]
                if 0 <= endRow < 8 and 0 <= endCol < 8 and self.board[endRow][endCol] * player <= 0:
                    move = Move((row, col), (endRow, endCol), self.board)
                    if (endRow, endCol) in self.info.capture_mask[player] or (endRow, endCol) in self.info.block_mask[player]:
                        if self.checkMoveSafety(move, player):
                            moves.append(move)
        else: #While not in check, if one is safe (not pinned), we can skip safety checks for all moves
            checkedSafety = False
            for moveOffset in knightMoves:
                endRow = row + moveOffset[0]
                endCol = col + moveOffset[1]
                if 0 <= endRow < 8 and 0 <= endCol < 8 and self.board[endRow][endCol] * player <= 0:
                    move = Move((row, col), (endRow, endCol), self.board)
                    if not checkedSafety:
                        if self.checkMoveSafety(move, player):
                            checkedSafety = True
                            moves.append(move)
                        else: #not safe, piece is pinned, no other moves are valid
                            break
                    else:
                        moves.append(move)
        return moves
    
    def getRayMoves(self, row, col, player, piece):
        moves = []
        if abs(piece) == 3: #Bishop
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        elif abs(piece) == 4: #Rook
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        elif abs(piece) == 5: #Queen
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
        else:
            return moves
        if self.info.inCheck[player]: #While in check skip moves that don't block or capture
            for direction in directions:
                currRow, currCol = row, col
                while True:
                    currRow += direction[0]
                    currCol += direction[1]
                    if 0 <= currRow < 8 and 0 <= currCol < 8:
                        if self.board[currRow][currCol] * player > 0:
                            break
                        if (currRow, currCol) in self.info.capture_mask[player] or (currRow, currCol) in self.info.block_mask[player]:
                            move = Move((row, col), (currRow, currCol), self.board)
                            if self.checkMoveSafety(move, player):
                                moves.append(move)
                            break
                    else:
                        break
        else: #While not in check, for all directions, if the first step is safe (not pinned), we can skip safety checks for all moves in that direction
            for direction in directions:
                currRow, currCol = row + direction[0], col + direction[1]
                if 0 <= currRow < 8 and 0 <= currCol < 8:
                    if self.board[currRow][currCol] * player > 0:
                        continue
                    move = Move((row, col), (currRow, currCol), self.board)
                    if self.checkMoveSafety(move, player):
                        moves.append(move)
                        if self.board[currRow][currCol] * player < 0:
                            continue
                        while True:
                            currRow += direction[0]
                            currCol += direction[1]
                            if 0 <= currRow < 8 and 0 <= currCol < 8:
                                if self.board[currRow][currCol] * player > 0:
                                    break
                                move = Move((row, col), (currRow, currCol), self.board)
                                moves.append(move)
                                if self.board[currRow][currCol] * player < 0:
                                    break
                            else:
                                break
        return moves
    
    def getKingMoves(self, row, col, player):
        moves = []
        kingMoves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for moveOffset in kingMoves:
            endRow = row + moveOffset[0]
            endCol = col + moveOffset[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8 and self.board[endRow][endCol] * player <= 0:
                move = Move((row, col), (endRow, endCol), self.board)
                if self.checkMoveSafety(move, player):
                    moves.append(move)
        if not self.info.inCheck[player]:
            if self.info.castlingRights[player][0]: #king side
                if self.board[row][col + 1] == 0 and self.board[row][col + 2] == 0:
                    if not self.isAttacked(row, col + 1, player)[0] and not self.isAttacked(row, col + 2, player)[0]:
                        move = Move((row, col), (row, col + 2), self.board)
                        move.isCastlingMove = True
                        moves.append(move)
            if self.info.castlingRights[player][1]: #queen side
                if self.board[row][col - 1] == 0 and self.board[row][col - 2] == 0 and self.board[row][col - 3] == 0:
                    if not self.isAttacked(row, col - 1, player)[0] and not self.isAttacked(row, col - 2, player)[0]:
                        move = Move((row, col), (row, col - 2), self.board)
                        move.isCastlingMove = True
                        moves.append(move)
        return moves