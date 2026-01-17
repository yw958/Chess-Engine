"""
Handles user input and displaying the current GameState object.
"""
import pygame as p
from Chess import ChessBackend
import os

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
    drawGameState(screen, gs)
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos() # (x,y) location of mouse
                col = location[0] // SQ_SIZE
                row = location[1] // SQ_SIZE                
                
                if row >= DIMENSION or col >= DIMENSION:
                    continue # click was outside the board
                if not sqSelected: 
                    if gs.board[row][col] == 0 or (gs.board[row][col] > 0) != (gs.player > 0):
                        continue # clicked on an empty square without having selected a piece
                    sqSelected = (row, col)
                    p.draw.rect(screen, p.Color("blue"), p.Rect(col*SQ_SIZE, row*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                    validMoves = gs.info.validMoves.get((row, col), [])
                    for move in validMoves:
                        p.draw.rect(screen, p.Color("yellow"), p.Rect(move.endCol*SQ_SIZE, move.endRow*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
                else:
                    if (row, col) == sqSelected: # user clicked the same square twice
                        sqSelected = () # deselect
                        validMoves = []
                        drawGameState(screen, gs)
                        continue
                    for validmove in validMoves:
                        if row == validmove.endRow and col == validmove.endCol:
                            print(validmove.getChessNotation())
                            gs.makeMove(validmove)
                            sqSelected = () # reset user clicks
                            validMoves = []
                            drawGameState(screen, gs)
                    continue
    
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z: # undo when 'z' is pressed
                    gs.undoMove()
                    sqSelected = ()
                    validMoves = []
                    drawGameState(screen, gs)
        clock.tick(MAX_FPS)
        p.display.flip()

def drawGameState(screen, gs):
    drawBoard(screen) # draw squares on the board
    drawPieces(screen, gs.board) # draw pieces on top of those squares

def drawBoard(screen):
    colors = [p.Color("white"), p.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r + c) % 2)]
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != 0: # not an empty square
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

if __name__ == "__main__":
    main()