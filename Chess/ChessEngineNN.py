"""
Hybrid chess engine that combines neural-network move priors with beam-pruned
negamax and quiescence search.
"""
import importlib.util
import os
from typing import Optional

import numpy as np
import torch

import ChessBackend
import ChessEngine
from PieceTables import PieceTables

try:
    from Chess.torch.model import ChessModel
except ModuleNotFoundError:
    current_path = os.path.dirname(__file__)
    model_module_path = os.path.join(current_path, "torch", "model.py")
    model_spec = importlib.util.spec_from_file_location("chess_torch_model", model_module_path)
    if model_spec is None or model_spec.loader is None:
        raise ImportError(f"Unable to load ChessModel from {model_module_path}.")
    model_module = importlib.util.module_from_spec(model_spec)
    model_spec.loader.exec_module(model_module)
    ChessModel = model_module.ChessModel


class EngineNN(ChessEngine.Engine):
    def __init__(
        self,
        model_path: Optional[str] = None,
        beam_width: int = 8,
        beam_depth: int = 2,
        policy_weight: float = 1.0,
        heuristic_weight: float = 0.05,
        device: Optional[str] = None,
    ):
        super().__init__()
        current_path = os.path.dirname(__file__)
        default_model_path = os.path.join(current_path, "torch", "models", "TORCH_100EPOCHS.pth")

        self.beamWidth = beam_width
        self.beamDepth = beam_depth
        self.policyWeight = policy_weight
        self.heuristicWeight = heuristic_weight
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.modelPath = model_path or default_model_path

        self.nnEnabled = False
        self.nnInferences = 0
        self.beamCuts = 0
        self.policyCache = {}

        self.model = ChessModel().to(self.device)
        self.model.eval()
        self._load_model_weights()

    def _load_model_weights(self):
        if not os.path.exists(self.modelPath):
            return
        state_dict = torch.load(self.modelPath, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.eval()
        self.nnEnabled = True

    @staticmethod
    def square_to_index(row: int, col: int) -> int:
        # The training pipeline uses python-chess square numbering:
        # a1 = 0, ..., h8 = 63.
        return (7 - row) * 8 + col

    @classmethod
    def move_to_index(cls, move: ChessBackend.Move) -> int:
        from_square = cls.square_to_index(move.startRow, move.startCol)
        to_square = cls.square_to_index(move.endRow, move.endCol)
        return from_square * 64 + to_square

    def game_state_to_matrix(self, game_state: ChessBackend.GameState) -> np.ndarray:
        matrix = np.zeros((18, 8, 8), dtype=np.float32)

        for row in range(8):
            for col in range(8):
                piece = game_state.board[row][col]
                if piece == 0:
                    continue
                matrix_row = 7 - row
                piece_type = abs(piece) - 1
                piece_color = 0 if piece > 0 else 6
                matrix[piece_type + piece_color, matrix_row, col] = 1

        if game_state.player == 1:
            matrix[12, :, :] = 1

        white_king_side, white_queen_side = game_state.info.castlingRights[1]
        black_king_side, black_queen_side = game_state.info.castlingRights[2]
        if white_king_side:
            matrix[13, :, :] = 1
        if white_queen_side:
            matrix[14, :, :] = 1
        if black_king_side:
            matrix[15, :, :] = 1
        if black_queen_side:
            matrix[16, :, :] = 1

        if game_state.info.enPassantPossible:
            ep_row, ep_col = game_state.info.enPassantPossible
            matrix[17, 7 - ep_row, ep_col] = 1

        return matrix

    def legal_mask(self, game_state: ChessBackend.GameState) -> np.ndarray:
        mask = np.zeros((64, 64), dtype=bool)
        for move in game_state.validMoves:
            from_square = self.square_to_index(move.startRow, move.startCol)
            to_square = self.square_to_index(move.endRow, move.endCol)
            mask[from_square, to_square] = True
        return mask

    def heuristic_move_value(self, move: ChessBackend.Move) -> float:
        value = 0.0
        if move.isCheck:
            value += 100
        if move.discoveredCheck:
            value += 100
        if move.pieceCaptured != 0:
            value += 10 * abs(move.pieceCaptured) - abs(move.pieceMoved)
        if move.pawnPromotion != 0:
            value += 20 * abs(move.pawnPromotion)
        elif move.isCastlingMove:
            value += 5
        value += PieceTables.positionalScores[move.pieceMoved][move.endRow][move.endCol]
        return value

    def policy_logits(self, game_state: ChessBackend.GameState) -> Optional[np.ndarray]:
        if not self.nnEnabled:
            return None

        board_rep = game_state.boardHistory[-1]
        cached = self.policyCache.get(board_rep)
        if cached is not None:
            return cached

        position = torch.from_numpy(self.game_state_to_matrix(game_state)).unsqueeze(0).to(self.device)
        legal_mask = torch.from_numpy(self.legal_mask(game_state)).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(position, legal_mask=legal_mask).squeeze(0).detach().cpu().numpy()

        self.nnInferences += 1
        self.policyCache[board_rep] = logits
        return logits

    def rank_moves(self, game_state: ChessBackend.GameState, moves: list[ChessBackend.Move]) -> list[ChessBackend.Move]:
        if not moves:
            return []

        logits = self.policy_logits(game_state)
        if logits is None:
            ordered = moves.copy()
            self.sortMoves(ordered)
            return ordered

        def combined_score(move: ChessBackend.Move) -> float:
            move_index = self.move_to_index(move)
            policy_score = float(logits[move_index])
            heuristic_score = self.heuristicWeight * self.heuristic_move_value(move)
            return self.policyWeight * policy_score + heuristic_score

        return sorted(moves, key=combined_score, reverse=True)

    def beam_negamax(
        self,
        game_state: ChessBackend.GameState,
        depth: int,
        alpha: float,
        beta: float,
        color: int,
        beam_depth_left: int,
    ) -> float:
        self.nodesSearched += 1
        board_rep = game_state.boardHistory[-1]
        memo_key = (board_rep, depth, beam_depth_left)
        if memo_key in self.memo:
            self.nodesFromMemo += 1
            return self.memo[memo_key]

        if depth == 0 or game_state.info.winner is not None:
            return self.qSearch(game_state, alpha, beta, color, self.qplyLimit)

        all_moves = game_state.validMoves.copy()
        if beam_depth_left > 0:
            all_moves = self.rank_moves(game_state, all_moves)
            if len(all_moves) > self.beamWidth:
                self.beamCuts += len(all_moves) - self.beamWidth
                all_moves = all_moves[: self.beamWidth]
        else:
            self.sortMoves(all_moves)

        best = float("-inf")
        a = alpha
        next_beam_depth = max(beam_depth_left - 1, 0)
        for move in all_moves:
            game_state.makeMove(move)
            score = -self.beam_negamax(game_state, depth - 1, -beta, -a, -color, next_beam_depth)
            game_state.undoMove(reCalculateMoves=False)

            if score > best:
                best = score
            if score > a:
                a = score
            if a >= beta:
                break

        self.memo[memo_key] = best
        return best

    def findBestMove(self, gameState: ChessBackend.GameState, depth: int) -> Optional[ChessBackend.Move]:
        self.nodesSearched = 0
        self.nodesFromMemo = 0
        self.nodesQSearched = 0
        self.nnInferences = 0
        self.beamCuts = 0
        self.memo = {}
        self.policyCache = {}

        all_moves = gameState.validMoves.copy()
        if not all_moves:
            return None

        ordered_moves = self.rank_moves(gameState, all_moves)
        if self.beamDepth > 0 and len(ordered_moves) > self.beamWidth:
            self.beamCuts += len(ordered_moves) - self.beamWidth
            ordered_moves = ordered_moves[: self.beamWidth]

        color = gameState.player
        best_move = ordered_moves[0]
        best_score = float("-inf")
        alpha, beta = float("-inf"), float("inf")
        next_beam_depth = max(min(self.beamDepth, depth) - 1, 0)

        for move in ordered_moves:
            gameState.makeMove(move)
            score = -self.beam_negamax(gameState, depth - 1, -beta, -alpha, -color, next_beam_depth)
            gameState.undoMove(reCalculateMoves=False)

            if score > best_score:
                best_score = score
                best_move = move
            if score > alpha:
                alpha = score

        return best_move
