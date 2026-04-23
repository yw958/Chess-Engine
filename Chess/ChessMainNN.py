"""
User interface for the chess game, using the hybrid neural-network engine.
"""
import os
import time

import pygame as p

import ChessBackend
import ChessEngineNN
from ChessMain import (
    BOARD_WIDTH,
    MOVE_LOG_PANEL_WIDTH,
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
)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "torch", "models", "TORCH_EPOCH__50.pth")
DEFAULT_ENGINE_DEPTH = 8
DEFAULT_BEAM_WIDTH = 3
DEFAULT_FULL_WIDTH_DEPTH = 1
DEFAULT_QPLY_LIMIT = 8


def print_nn_controls():
    print("NN engine controls:")
    print("  E/D: enable or disable engine")
    print("  Z/F: undo or flip board")
    print("  Up/Down: increase or decrease search depth")
    print("  Right/Left: increase or decrease beam width")
    print("  PageUp/PageDown: increase or decrease full-width depth before beam search")
    print("  = / -: increase or decrease q-search ply limit")


def update_window_caption(engineDepth: int, engine: ChessEngineNN.EngineNN):
    p.display.set_caption(
        "ChessMainNN | "
        f"depth={engineDepth} | "
        f"full={engine.fullWidthDepth} | "
        f"beam={engine.beamWidth} | "
        f"qply={engine.qplyLimit} | "
        f"nn={'on' if engine.nnEnabled else 'fallback'}"
    )


def print_nn_settings(engineDepth: int, engine: ChessEngineNN.EngineNN):
    print(f"NN engine settings -> search depth: {engineDepth}, {engine.search_settings()}")


def makeNNEngineMove(
    gs: ChessBackend.GameState,
    screen,
    engine: ChessEngineNN.EngineNN,
    flipped=False,
    engineDepth=3,
    moveLogFont=None,
    engineEnabled=0,
):
    print("NN engine is thinking...")
    statTime = time.time()
    engineMove = engine.findBestMove(gs, engineDepth)
    elapsed = time.time() - statTime
    print("Engine move time: {:.2f} seconds".format(elapsed))
    print(
        f"Nodes searched: {engine.nodesSearched}, from memo: {engine.nodesFromMemo}, "
        f"QSearched: {engine.nodesQSearched}, NN inferences: {engine.nnInferences}, "
        f"beam cuts: {engine.beamCuts}"
    )
    print(
        f"Nodes per second: "
        f"{(engine.nodesSearched + engine.nodesFromMemo + engine.nodesQSearched) / (elapsed + 1e-9):.2f}"
    )
    print(engine.search_settings())
    if engineMove is not None:
        print(engineMove.getChessNotation())
        gs.makeMove(engineMove)
        drawGameState(screen, gs, flipped, moveLogFont, engineEnabled)
        if not flipped:
            p.draw.rect(screen, p.Color("red"), p.Rect(engineMove.endCol * SQ_SIZE, engineMove.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
            p.draw.rect(screen, p.Color("red"), p.Rect(engineMove.startCol * SQ_SIZE, engineMove.startRow * SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
        else:
            p.draw.rect(screen, p.Color("red"), p.Rect((DIMENSION - 1 - engineMove.endCol) * SQ_SIZE, (DIMENSION - 1 - engineMove.endRow) * SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
            p.draw.rect(screen, p.Color("red"), p.Rect((DIMENSION - 1 - engineMove.startCol) * SQ_SIZE, (DIMENSION - 1 - engineMove.startRow) * SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)
    else:
        print("No valid moves found by engine!")


def main():
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_WIDTH))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessBackend.GameState()
    loadImages()
    running = True
    sqSelected = ()
    validMoves = []
    flipped = False

    engine = ChessEngineNN.EngineNN(
        model_path=MODEL_PATH,
        beam_width=DEFAULT_BEAM_WIDTH,
        full_width_depth=DEFAULT_FULL_WIDTH_DEPTH,
    )
    engineEnabled = 0
    engineDepth = DEFAULT_ENGINE_DEPTH
    qplyLimit = DEFAULT_QPLY_LIMIT
    engine.qplyLimit = qplyLimit

    moveLogFont = p.font.SysFont("", 20, False, False)
    drawGameState(screen, gs, flipped, moveLogFont, engineEnabled)
    print_nn_controls()
    print_nn_settings(engineDepth, engine)
    update_window_caption(engineDepth, engine)

    while running:
        if engineEnabled == gs.player and gs.info.winner is None:
            makeNNEngineMove(gs, screen, engine, flipped, engineDepth, moveLogFont, engineEnabled)
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
                if e.key == p.K_UP:
                    engineDepth += 1
                    print_nn_settings(engineDepth, engine)
                if e.key == p.K_DOWN:
                    engineDepth = max(1, engineDepth - 1)
                    print_nn_settings(engineDepth, engine)
                if e.key == p.K_RIGHT:
                    engine.set_search_options(beam_width=engine.beamWidth + 1)
                    print_nn_settings(engineDepth, engine)
                if e.key == p.K_LEFT:
                    engine.set_search_options(beam_width=engine.beamWidth - 1)
                    print_nn_settings(engineDepth, engine)
                if e.key == p.K_PAGEUP:
                    engine.set_search_options(full_width_depth=engine.fullWidthDepth + 1)
                    print_nn_settings(engineDepth, engine)
                if e.key == p.K_PAGEDOWN:
                    engine.set_search_options(full_width_depth=engine.fullWidthDepth - 1)
                    print_nn_settings(engineDepth, engine)
                if e.key == p.K_EQUALS or e.key == p.K_KP_PLUS:
                    engine.set_search_options(qply_limit=engine.qplyLimit + 1)
                    print_nn_settings(engineDepth, engine)
                if e.key == p.K_MINUS or e.key == p.K_KP_MINUS:
                    engine.set_search_options(qply_limit=engine.qplyLimit - 1)
                    print_nn_settings(engineDepth, engine)
                update_window_caption(engineDepth, engine)
                drawGameState(screen, gs, flipped, moveLogFont, engineEnabled)

        clock.tick(MAX_FPS)
        p.display.flip()


if __name__ == "__main__":
    main()
