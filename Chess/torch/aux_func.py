import numpy as np
import chess
from chess import Board
from tqdm import tqdm


def board_to_matrix(board: Board):
    # 8x8 is a size of the chess board.
    # 12 = number of unique pieces.
    # 13th board encodes the side to move across the whole board.
    # 14th-17th boards encode castling rights.
    # 18th board encodes the en passant target square.
    matrix = np.zeros((18, 8, 8), dtype=np.float32)
    piece_map = board.piece_map()

    # Populate first 12 8x8 boards (where pieces are).
    for square, piece in piece_map.items():
        row, col = divmod(square, 8)
        piece_type = piece.piece_type - 1
        piece_color = 0 if piece.color else 6
        matrix[piece_type + piece_color, row, col] = 1

    # Fill the side-to-move board: 1 for white to move, 0 for black to move.
    if board.turn:
        matrix[12, :, :] = 1

    # Encode castling rights as full-board feature planes.
    if board.has_kingside_castling_rights(chess.WHITE):
        matrix[13, :, :] = 1
    if board.has_queenside_castling_rights(chess.WHITE):
        matrix[14, :, :] = 1
    if board.has_kingside_castling_rights(chess.BLACK):
        matrix[15, :, :] = 1
    if board.has_queenside_castling_rights(chess.BLACK):
        matrix[16, :, :] = 1

    # Encode the current en passant target square as a one-hot plane.
    if board.ep_square is not None:
        row_ep, col_ep = divmod(board.ep_square, 8)
        matrix[17, row_ep, col_ep] = 1

    return matrix


def legal_mask(board: Board):
    mask = np.zeros((64, 64), dtype=bool)

    for move in board.legal_moves:
        from_square = move.from_square
        to_square = move.to_square
        mask[from_square, to_square] = True

    return mask


def move_to_index(move):
    return move.from_square * 64 + move.to_square


def create_input_for_nn(games):
    X = []
    y = []
    legal_masks = []
    for game in tqdm(games):
        board = game.board()
        for move in game.mainline_moves():
            X.append(board_to_matrix(board))
            legal_masks.append(legal_mask(board))
            y.append(move_to_index(move))
            board.push(move)
    return (
        np.array(X, dtype=np.float32),
        np.array(y, dtype=np.int64),
        np.array(legal_masks, dtype=bool),
    )
