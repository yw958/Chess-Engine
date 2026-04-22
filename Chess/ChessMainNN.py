"""
User interface for the chess game, using the hybrid neural-network engine.
"""
import pygame as p

import ChessBackend
import ChessEngineNN
from ChessMain import (
    MAX_FPS,
    DIMENSION,
    SQ_SIZE,
    loadImages,
    drawEndGameText,
    drawGameState,
    drawHighlightedSquares,
    drawPromotionChoice,
    drawSelectedSquare,
    getValidMovesList,
    makeEngineMove,
)


def main():
    p.init()
    screen = p.display.set_mode((512 + 270, 512))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessBackend.GameState()
    loadImages()
    running = True
    sqSelected = ()
    validMoves = []
    flipped = False

    engine = ChessEngineNN.EngineNN()
    engineEnabled = 0
    engineDepth = 4
    qplyLimit = 8
    engine.qplyLimit = qplyLimit

    moveLogFont = p.font.SysFont("", 20, False, False)
    drawGameState(screen, gs, flipped, moveLogFont, engineEnabled)

    while running:
        if engineEnabled == gs.player and gs.info.winner is None:
            makeEngineMove(gs, screen, engine, flipped, engineDepth, moveLogFont, engineEnabled)
            if gs.info.winner is not None:
                text = ""
                if gs.info.winner == 0:
                    text = "Draw!"
                elif gs.info.winner == 1:
                    text = "White wins!"
                else:
                    text = "Black wins!"
                print(text)
                drawEndGameText(screen, text)

        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos()
                col = location[0] // SQ_SIZE
                row = location[1] // SQ_SIZE
                if flipped:
                    row = DIMENSION - 1 - row
                    col = DIMENSION - 1 - col
                if row >= DIMENSION or col >= DIMENSION:
                    continue
                if not sqSelected:
                    if gs.board[row][col] == 0 or (gs.board[row][col] > 0) != (gs.player > 0):
                        continue
                    sqSelected = (row, col)
                    drawSelectedSquare(screen, row, col, flipped)
                    validMoves = getValidMovesList(gs, row, col)
                    drawHighlightedSquares(screen, validMoves, flipped)
                else:
                    if (row, col) == sqSelected:
                        sqSelected = ()
                        validMoves = []
                        drawGameState(screen, gs, flipped, moveLogFont, engineEnabled)
                        continue
                    if gs.board[row][col] != 0 and (gs.board[row][col] > 0) == (gs.player > 0):
                        sqSelected = (row, col)
                        validMoves = getValidMovesList(gs, row, col)
                        drawGameState(screen, gs, flipped, moveLogFont, engineEnabled)
                        drawSelectedSquare(screen, row, col, flipped)
                        drawHighlightedSquares(screen, validMoves, flipped)
                        continue

                    i = 0
                    promotionChosen = False
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
                                            location = p.mouse.get_pos()
                                            r = location[1] // SQ_SIZE
                                            c = location[0] // SQ_SIZE
                                            if flipped:
                                                r = DIMENSION - 1 - r
                                                c = DIMENSION - 1 - c
                                            if c == col and abs(row - r) < 4:
                                                promotionChoice = abs(row - r)
                                                choosing = False
                                                i += promotionChoice
                                                promotionChosen = True
                                            else:
                                                choosing = False
                                                reselect = True
                                if reselect:
                                    drawGameState(screen, gs, flipped, moveLogFont, engineEnabled)
                                    drawSelectedSquare(screen, sqSelected[0], sqSelected[1], flipped)
                                    drawHighlightedSquares(screen, validMoves, flipped)
                                    break
                                continue

                            print(validmove.getChessNotation())
                            gs.makeMove(validmove)
                            sqSelected = ()
                            validMoves = []
                            drawGameState(screen, gs, flipped, moveLogFont, engineEnabled)
                            if gs.info.winner is not None:
                                text = ""
                                if gs.info.winner == 0:
                                    text = "Draw!"
                                elif gs.info.winner == 1:
                                    text = "White wins!"
                                else:
                                    text = "Black wins!"
                                print(text)
                                drawEndGameText(screen, text)
                            break
                        i += 1

            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.undoMove()
                    if engineEnabled == gs.player:
                        gs.undoMove()
                    sqSelected = ()
                    validMoves = []
                    drawGameState(screen, gs, flipped, moveLogFont, engineEnabled)
                    print("Undo move")
                if e.key == p.K_f:
                    flipped = not flipped
                    drawGameState(screen, gs, flipped, moveLogFont, engineEnabled)
                    if sqSelected:
                        drawSelectedSquare(screen, sqSelected[0], sqSelected[1], flipped)
                        drawHighlightedSquares(screen, validMoves, flipped)
                if e.key == p.K_e:
                    engineEnabled = gs.player
                    drawGameState(screen, gs, flipped, moveLogFont, engineEnabled)
                    print("NN engine enabled for player {}".format("White" if engineEnabled == 1 else "Black"))
                if e.key == p.K_d:
                    engineEnabled = 0
                    drawGameState(screen, gs, flipped, moveLogFont, engineEnabled)
                    print("NN engine disabled")

        clock.tick(MAX_FPS)
        p.display.flip()


if __name__ == "__main__":
    main()
