"""
Handles user input and displaying the current GameState object.
"""
import pygame as p
from Chess import ChessBackend
from Chess import ChessEngine
import os
import time

BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 270
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
# the chess board is 8x8 :)
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSION
# for animation later on
MAX_FPS = 15
IMAGES = [None]
current_path = os.path.dirname(__file__)  # Where your .py file is located
image_path = os.path.join(current_path, "images")  # The image folder path

def loadImages():
    pieces = ['wp', 'wN', 'wB', 'wR', 'wQ', 'wK', 'bK', 'bQ', 'bR', 'bB', 'bN', 'bp']
    for piece in pieces:
        IMAGES.append(p.transform.scale(p.image.load(os.path.join(image_path, piece + ".png")), (SQ_SIZE, SQ_SIZE)))
        
def main():
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessBackend.GameState()
    loadImages()
    running = True
    sqSelected = () # no square is selected initially, keep track of the last click of the user (tuple: (row, col))
    validMoves = []
    flipped = False
    engine = ChessEngine.Engine()
    engineEnabled = -1
    engineDepth = 3
    moveLogFont = p.font.SysFont("Arail", 20, False, False)
    drawGameState(screen, gs, flipped, moveLogFont)
    while running:
        if engineEnabled == gs.player and gs.info.winner == None:
            makeEngineMove(gs, screen, engine, flipped, engineDepth, moveLogFont)
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos() # (x,y) location of mouse
                col = location[0] // SQ_SIZE
                row = location[1] // SQ_SIZE
                if flipped:
                    row = DIMENSION - 1 - row               
                if row >= DIMENSION or col >= DIMENSION: 
                    continue # click was outside the board
                if not sqSelected: 
                    if gs.board[row][col] == 0 or (gs.board[row][col] > 0) != (gs.player > 0):
                        continue # clicked on an empty square without having selected a piece
                    sqSelected = (row, col)
                    if not flipped:
                        p.draw.rect(screen, p.Color("blue"), p.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                    else:
                        p.draw.rect(screen, p.Color("blue"), p.Rect(col*SQ_SIZE, (DIMENSION - 1 - row)*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                    validMoves = gs.info.validMoves.get((row, col), [])
                    for move in validMoves:
                        if not flipped:
                            p.draw.rect(screen, p.Color("yellow"), p.Rect(move.endCol*SQ_SIZE, move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                        else:
                            p.draw.rect(screen, p.Color("yellow"), p.Rect(move.endCol*SQ_SIZE, (DIMENSION - 1 - move.endRow)*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                else:
                    if (row, col) == sqSelected: # user clicked the same square twice
                        sqSelected = () # deselect
                        validMoves = []
                        drawGameState(screen, gs, flipped, moveLogFont)
                        continue
                    if gs.board[row][col] != 0 and (gs.board[row][col] > 0) == (gs.player > 0):
                        sqSelected = (row, col)
                        validMoves = gs.info.validMoves.get((row, col), [])
                        drawGameState(screen, gs, flipped, moveLogFont)
                        p.draw.rect(screen, p.Color("blue"), p.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                        for move in validMoves:
                            p.draw.rect(screen, p.Color("yellow"), p.Rect(move.endCol*SQ_SIZE, move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                        continue
                    i = 0
                    promotionChosen = False
                    promotionChoice = 0
                    reselect = False
                    while i < len(validMoves):
                        validmove = validMoves[i]
                        if row == validmove.endRow and col == validmove.endCol:
                            if validmove.pawnPromotion != 0 and not promotionChosen:
                                player = gs.player
                                drawPromotionChoice(screen, gs, row, col, player, flipped)
                                choosing = True
                                while choosing:
                                    for e in p.event.get():
                                        if e.type == p.MOUSEBUTTONDOWN:
                                            location = p.mouse.get_pos() # (x,y) location of mouse
                                            r = location[1] // SQ_SIZE
                                            c = location[0] // SQ_SIZE
                                            if flipped:
                                                r = DIMENSION - 1 - r
                                            if c == col and abs(row - r) < 4:
                                                promotionChoice = abs(row - r)
                                                choosing = False
                                                i += promotionChoice
                                                promotionChosen = True
                                            else:
                                                choosing = False
                                                reselect = True
                                if reselect:
                                    drawGameState(screen, gs, flipped, moveLogFont)
                                    if not flipped:
                                        p.draw.rect(screen, p.Color("blue"), p.Rect(sqSelected[1]*SQ_SIZE, sqSelected[0]*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                                    else:
                                        p.draw.rect(screen, p.Color("blue"), p.Rect(sqSelected[1]*SQ_SIZE, (DIMENSION - 1 - sqSelected[0])*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                                    for move in validMoves:
                                        if not flipped:
                                            p.draw.rect(screen, p.Color("yellow"), p.Rect(move.endCol*SQ_SIZE, move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                                        else:
                                            p.draw.rect(screen, p.Color("yellow"), p.Rect(move.endCol*SQ_SIZE, (DIMENSION - 1 - move.endRow)*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                                    break
                                continue
                            #Make the chosen move                               
                            print(validmove.getChessNotation())
                            gs.makeMove(validmove)
                            sqSelected = ()
                            validMoves = []
                            drawGameState(screen, gs, flipped, moveLogFont)
                            if gs.info.winner != None:
                                if gs.info.winner == 0:
                                    print("Draw!")
                                elif gs.info.winner == 1:
                                    print("White wins!")
                                else:
                                    print("Black wins!")
                            break
                        i += 1
    
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z: # undo when 'z' is pressed
                    gs.undoMove()
                    if engineEnabled == gs.player:
                        gs.undoMove()
                    sqSelected = ()
                    validMoves = []
                    drawGameState(screen, gs, flipped, moveLogFont)
                    print("Undo move")
                if e.key == p.K_f: # flip board when 'f' is pressed
                    flipped = not flipped
                    drawGameState(screen, gs, flipped, moveLogFont)
                    if sqSelected:
                        if not flipped:
                            p.draw.rect(screen, p.Color("blue"), p.Rect(sqSelected[1]*SQ_SIZE, sqSelected[0]*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                        else:
                            p.draw.rect(screen, p.Color("blue"), p.Rect(sqSelected[1]*SQ_SIZE, (DIMENSION - 1 - sqSelected[0])*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                        for move in validMoves:
                            if not flipped:
                                p.draw.rect(screen, p.Color("yellow"), p.Rect(move.endCol*SQ_SIZE, move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                            else:
                                p.draw.rect(screen, p.Color("yellow"), p.Rect(move.endCol*SQ_SIZE, (DIMENSION - 1 - move.endRow)*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
        clock.tick(MAX_FPS)
        p.display.flip()

def makeEngineMove(gs: ChessBackend.GameState, screen, engine: ChessEngine.Engine, flipped = False, engineDepth = 3, moveLogFont = None):
    print("Engine is thinking...")
    statTime = time.time()
    engineMove = engine.findBestMove(gs, engineDepth)
    print("Engine move time: {:.2f} seconds".format(time.time() - statTime))
    if engineMove is not None:
        print(engineMove.getChessNotation())
        gs.makeMove(engineMove)
        drawGameState(screen, gs, flipped, moveLogFont)
        if not flipped:
            p.draw.rect(screen, p.Color("red"), p.Rect(engineMove.endCol*SQ_SIZE, engineMove.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
            p.draw.rect(screen, p.Color("red"), p.Rect(engineMove.startCol*SQ_SIZE, engineMove.startRow*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
        else:
            p.draw.rect(screen, p.Color("red"), p.Rect(engineMove.endCol*SQ_SIZE, (DIMENSION - 1 - engineMove.endRow)*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
            p.draw.rect(screen, p.Color("red"), p.Rect(engineMove.startCol*SQ_SIZE, (DIMENSION - 1 - engineMove.startRow)*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
    if gs.info.winner != None:
        if gs.info.winner == 0:
            print("Draw!")
        elif gs.info.winner == 1:
            print("White wins!")
        else:
            print("Black wins!")

def drawGameState(screen, gs, flipped = False, moveLogFont = None):
    drawBoard(screen, flipped) # draw squares on the board
    drawPieces(screen, gs.board, flipped) # draw pieces on top of those squares
    drawMoveLog(screen, gs, moveLogFont)

def drawBoard(screen, flipped=False):
    colors = [p.Color("white"), p.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r + c) % 2)]
            if flipped:
                p.draw.rect(screen, color, p.Rect((DIMENSION - 1 - c)*SQ_SIZE, (DIMENSION - 1 - r)*SQ_SIZE, SQ_SIZE, SQ_SIZE))
            else:
                p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawPieces(screen, board, flipped=False):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != 0: # not an empty square
                if not flipped:
                    screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
                else:
                    screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, (DIMENSION - 1 - r)*SQ_SIZE, SQ_SIZE, SQ_SIZE))
                
def drawPromotionChoice(screen, gs, row, col, player, flipped=False):
    color = p.Color("gray")
    promotionPieces = [5,4,3,2] # queen, rook, bishop, knight
    for i in range(4):
        if not flipped:
            p.draw.rect(screen, color, p.Rect(col*SQ_SIZE, (row+i*player)*SQ_SIZE, SQ_SIZE, SQ_SIZE))
            screen.blit(IMAGES[promotionPieces[i]*player], p.Rect(col*SQ_SIZE, (row+i*player)*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        else:
            p.draw.rect(screen, color, p.Rect(col*SQ_SIZE, (DIMENSION - 1 - (row+i*player))*SQ_SIZE, SQ_SIZE, SQ_SIZE))
            screen.blit(IMAGES[promotionPieces[i]*player], p.Rect(col*SQ_SIZE, (DIMENSION - 1 - (row+i*player))*SQ_SIZE, SQ_SIZE, SQ_SIZE))
    p.display.flip()

def drawMoveLog(screen, gs:ChessBackend.GameState, font):
    moveLogRect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color("white"), moveLogRect)
    moveLog = gs.moveLog
    moveTexts = []
    for i in range(0, len(moveLog), 2):
        moveString = str(i // 2 + 1) + ". " + str(moveLog[i]) + " "
        if i + 1 < len(moveLog):
            moveString += str(moveLog[i + 1])
        moveTexts.append(moveString)
    padding = 5
    textY = padding
    lineSpacing = 5
    movesPerRow = 2
    for i in range(0, len(moveTexts), movesPerRow):
        text = ""
        for j in range(movesPerRow):
            if i + j < len(moveTexts):
                text += moveTexts[i + j] + "  "
        textObject = font.render(text, True, p.Color("black"))
        textLocation = moveLogRect.move(padding, textY)
        screen.blit(textObject, textLocation)
        textY += textObject.get_height() + lineSpacing

if __name__ == "__main__":
    main()