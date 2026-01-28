#include "ChessBackend.h"
#include "PieceTables.h"
#include <algorithm>
#include <cctype>
#include <sstream>

std::string Move::getChessNotation() const {
    auto fileChar = [](int col) -> char {
        return static_cast<char>('a' + col);
    };
    auto rankChar = [](int row) -> char {
        // row 0 -> '8', row 7 -> '1'
        return static_cast<char>('0' + (8 - row));
    };
    std::string s;
    if (isCastlingMove) {
        s = (endCol == 6) ? "O-O" : "O-O-O";
    }
    else if (isEnPassantMove) {
        // "e5xf6 e.p."
        s.push_back(fileChar(startCol));
        s.push_back(rankChar(startRow));
        s.push_back('x');
        s.push_back(fileChar(endCol));
        s.push_back(rankChar(endRow));
        s += " e.p.";
    }
    else if (pawnPromotion != 0) {
        const char promo = PieceTables::pieceChar(std::abs(pawnPromotion)); // typically 'Q','R','B','N' etc.
        if (pieceCaptured != 0) {
            s.push_back(fileChar(startCol));
            s.push_back('x');
            s.push_back(fileChar(endCol));
            s.push_back(rankChar(endRow));
            s.push_back('=');
            s.push_back(promo);
        } else {
            s.push_back(fileChar(startCol));
            s.push_back(rankChar(startRow));
            s.push_back(fileChar(endCol));
            s.push_back(rankChar(endRow));
            s.push_back('=');
            s.push_back(promo);
        }
    }
    else if (pieceCaptured != 0) {
        // pieceChar = '' if pawn else piece letter
        const int movedAbs = std::abs(pieceMoved);
        if (movedAbs != 1) {
            s.push_back(PieceTables::pieceChar(movedAbs)); // expects 2..6 -> 'N','B','R','Q','K'
        }
        s.push_back(fileChar(startCol));
        s.push_back('x');
        s.push_back(fileChar(endCol));
        s.push_back(rankChar(endRow));
    }
    else {
        // "e2 -> e4"
        s.push_back(fileChar(startCol));
        s.push_back(rankChar(startRow));
        s += " -> ";
        s.push_back(fileChar(endCol));
        s.push_back(rankChar(endRow));
    }
    // "+" if direct check or discovered check exists
    if (isCheck || discoveredCheck.first != -1) {
        s.push_back('+');
    }
    return s;
}

std::ostream& operator<<(std::ostream& os, const Move& m) {
    os << m.getChessNotation();
    return os;
}

//////////////////////////////////////////////////////////////
GameState::GameState(){
    // Initialize board to starting position
    board_ = {{
        {{-4,-2,-3,-5,-6,-3,-2,-4}},
        {{-1,-1,-1,-1,-1,-1,-1,-1}},
        {{ 0, 0, 0, 0, 0, 0, 0, 0}},
        {{ 0, 0, 0, 0, 0, 0, 0, 0}},
        {{ 0, 0, 0, 0, 0, 0, 0, 0}},
        {{ 0, 0, 0, 0, 0, 0, 0, 0}},
        {{ 1, 1, 1, 1, 1, 1, 1, 1}},
        {{ 4, 2, 3, 5, 6, 3, 2, 4}}
    }};
    moveLog_.reserve(256);
    boardHistory_.reserve(256);
    infoLog_.reserve(256);
    boardHistory_.push_back(this->scanAndUpdate());
    boardCounter_[boardHistory_.back()] = 1;
}
std::string GameState::scanAndUpdate() {
    std::vector<std::string> ranks_str;
    ranks_str.reserve(8);
    validMoves_.clear();
    double score = 0.0;
    std::vector<int> pieces;
    pieces.reserve(8); // usually tiny for dead-position cases
    bool possibleDead = true;
    int bishopColorBlack = -1; // unknown
    int bishopColorWhite = -1; // unknown
    const int player = player_;
    const double fac = 0.1;
    for (int r = 0; r < 8; ++r) {
        std::string parts;
        parts.reserve(16);
        int empty = 0;
        for (int c = 0; c < 8; ++c) {
            const int sq = board_[r][c];
            if (sq == 0) {
                ++empty;
                continue;
            }
            // --- FEN piece placement for this rank ---
            if (empty) {
                parts += std::to_string(empty);
                empty = 0;
            }
            parts.push_back(PieceTables::pieceChar(sq));
            // --- evaluation (material + positional, excluding king positional) ---
            double posScore = 0.0;
            if (std::abs(sq) != 6) {
                posScore = PieceTables::positionalScore(sq, r, c) * fac;
            }
            score += (PieceTables::VALUES[std::abs(sq)] + posScore) * (sq > 0 ? 1.0 : -1.0);
            // --- dead position detection (insufficient material) ---
            if (possibleDead) {
                pieces.push_back(sq);
                if (pieces.size() > 4) {
                    possibleDead = false;
                } else {
                    const int a = std::abs(sq);
                    if (a == 5 || a == 4 || a == 1) { // queen/rook/pawn present -> not dead
                        possibleDead = false;
                    } else if (sq == -3) {
                        bishopColorBlack = (r + c) & 1;
                    } else if (sq == 3) {
                        bishopColorWhite = (r + c) & 1;
                    }
                }
            }
            // --- generate moves for side to move (one-pass scan) ---
            if ((sq > 0) == (player > 0)) {
                updateValidMoves(r, c);
            }
        }
        if (empty) {
            parts += std::to_string(empty);
        }
        ranks_str.push_back(std::move(parts));
    }
    // --- finish board representation (FEN-like) ---
    std::string placement;
    placement.reserve(64);
    for (int i = 0; i < 8; ++i) {
        if (i) placement.push_back('/');
        placement += ranks_str[i];
    }
    const char stm = (player_ == 1) ? 'w' : 'b';
    // castling rights (index 1 = white, 2 = black)
    const auto [w_k, w_q] = info_.castlingRights[1];
    const auto [b_k, b_q] = info_.castlingRights[2];
    std::string castling;
    if (w_k) castling.push_back('K');
    if (w_q) castling.push_back('Q');
    if (b_k) castling.push_back('k');
    if (b_q) castling.push_back('q');
    if (castling.empty()) castling = "-";
    // en passant target square
    std::string ep = "-";
    if (info_.enPassantPossible.first != -1) {
        const int er = info_.enPassantPossible.first;
        const int ec = info_.enPassantPossible.second;
        ep.clear();
        ep.push_back(static_cast<char>('a' + ec));
        ep.push_back(static_cast<char>('0' + (8 - er)));
    }
    // Update eval (keep as int if your Info::eval is int; here we round)
    this->info_.eval = score;
    // --- insufficient material draw checks---
    if (possibleDead) {
        if (pieces.size() == 2) { // K vs K
            info_.winner = 0;
            info_.eval = 0;
            validMoves_.clear();
        } else {
            std::sort(pieces.begin(), pieces.end());
            // K vs K+N or K vs K+B
            const std::vector<int> kb1 = {-6,  3, 6};
            const std::vector<int> kb2 = {-6, -3, 6};
            const std::vector<int> kn1 = {-6,  2, 6};
            const std::vector<int> kn2 = {-6, -2, 6};
            if (pieces.size() == 3 &&
                (pieces == kb1 || pieces == kb2 || pieces == kn1 || pieces == kn2)) {
                info_.winner = 0;
                info_.eval = 0;
                validMoves_.clear();
            }
            // K+B vs K+B (bishops on same color)
            else if (pieces == std::vector<int>({-6, -3, 3, 6})) {
                if (bishopColorBlack != -1 && bishopColorWhite != -1 &&
                    bishopColorBlack == bishopColorWhite) {
                    info_.winner = 0;
                    info_.eval = 0;
                    validMoves_.clear();
                }
            }
        }
    }
    // Return a compact rep: "{placement} {stm} {castling} {ep}"
    std::string rep;
    rep.reserve(placement.size() + 1 + 1 + 1 + castling.size() + 1 + ep.size());
    rep += placement;
    rep.push_back(' ');
    rep.push_back(stm);
    rep.push_back(' ');
    rep += castling;
    rep.push_back(' ');
    rep += ep;
    return rep;
}

static inline int sideIndex(int player) {
    // Map +1 -> 1 (white), -1 -> 2 (black)
    return (player == 1) ? 1 : 2;
}

void GameState::makeMove(const Move& move) {
    // Not the player's turn?
    if ((move.pieceMoved > 0) != (player_ > 0)) {
        return;
    }
    // Save info snapshot for undo
    infoLog_.push_back(info_);
    // Move the piece
    board_[move.startRow][move.startCol] = 0;
    board_[move.endRow][move.endCol] = move.pieceMoved;
    // Log move
    moveLog_.push_back(move);
    const int usIdx = sideIndex(player_);
    const int themIdx = sideIndex(-player_);
    // ---- Handle king moves and castling rights ----
    if (std::abs(move.pieceMoved) == 6) {
        info_.kingLocations[usIdx] = {move.endRow, move.endCol};
        if (move.isCastlingMove) {
            // King-side: endCol - startCol == 2
            if (move.endCol - move.startCol == 2) {
                // rook h-file (col 7) -> f-file (endCol-1)
                board_[move.endRow][move.endCol - 1] = board_[move.endRow][7];
                board_[move.endRow][7] = 0;
            } else {
                // Queen-side: rook a-file (col 0) -> d-file (endCol+1)
                board_[move.endRow][move.endCol + 1] = board_[move.endRow][0];
                board_[move.endRow][0] = 0;
            }
        }
        info_.castlingRights[usIdx] = {false, false};
    }
    // ---- Handle rook moves and castling rights ----
    else if (std::abs(move.pieceMoved) == 4) {
        auto [kSide, qSide] = info_.castlingRights[usIdx];
        if (move.startCol == 0) {
            // moved rook from a-file => lose queen-side
            qSide = false;
        } else if (move.startCol == 7) {
            // moved rook from h-file => lose king-side
            kSide = false;
        }
        info_.castlingRights[usIdx] = {kSide, qSide};
    }
    // ---- Handle special pawn moves ----
    if (move.pawnPromotion != 0) {
        board_[move.endRow][move.endCol] = move.pawnPromotion;
    } else if (move.isEnPassantMove) {
        // Captured pawn is behind the destination square, on endRow + player_, endCol
        const int capRow = move.endRow + player_;
        if (inBounds(capRow, move.endCol)) {
            board_[capRow][move.endCol] = 0;
        }
    }
    // Reset en passant, then possibly set it
    info_.enPassantPossible = {-1, -1};
    if (std::abs(move.pieceMoved) == 1 && std::abs(move.startRow - move.endRow) == 2) {
        // Pawn double push: set EP square to the jumped-over square
        info_.enPassantPossible = {(move.startRow + move.endRow) / 2, move.startCol};
    }
    // ---- Handle rook captures and castling rights (if EP not set) ----
    else if (std::abs(move.pieceCaptured) == 4) {
        auto [kSide, qSide] = info_.castlingRights[themIdx];
        if (move.endCol == 0) {
            // captured rook on a-file => opponent loses queen-side
            qSide = false;
        } else if (move.endCol == 7) {
            // captured rook on h-file => opponent loses king-side
            kSide = false;
        }
        info_.castlingRights[themIdx] = {kSide, qSide};
    }
    // ---- Update 75-move rule counter (150 half-moves) ----
    if (std::abs(move.pieceMoved) == 1 || move.pieceCaptured != 0) {
        info_.seventyFiveMoveRuleCounter = 0;
    } else {
        info_.seventyFiveMoveRuleCounter += 1;
    }
    if (info_.seventyFiveMoveRuleCounter >= 150) {
        info_.winner = 0; // draw
        info_.eval = 0;
    }
    // Switch players
    player_ *= -1;
    // Update king safety for side to move
    updateKingSafety(move);
    // Scan board, generate moves, and get board representation
    const std::string boardRep = scanAndUpdate();
    // Update repetition table & fivefold repetition
    const int newCount = ++boardCounter_[boardRep];
    if (newCount >= 5) {
        info_.winner = 0; // draw
        info_.eval = 0;
    }
    boardHistory_.push_back(boardRep);
    const bool ongoing = (info_.winner == 2);
    if (ongoing) {
        if (validMoves_.empty()) {
            const int stmIdx = sideIndex(player_);
            if (info_.inCheck[stmIdx]) {
                info_.winner = -player_; // side who just moved delivers mate => winner is -side_to_move
                // big eval in winner direction
                info_.eval = (info_.winner > 0) ? 1000000 : -1000000;
            } else {
                info_.winner = 0; // stalemate
                info_.eval = 0;
            }
        }
    } else {
        // If already decided (draw by rules, etc.), no moves
        validMoves_.clear();
    }
}

void GameState::undoMove(bool reCalculateMoves) {
    if (moveLog_.empty()) return;
    player_ *= -1;
    // Pop board rep and decrement repetition counter
    if (!boardHistory_.empty()) {
        const std::string rep = boardHistory_.back();
        boardHistory_.pop_back();

        auto it = boardCounter_.find(rep);
        if (it != boardCounter_.end()) {
            it->second -= 1;
            if (it->second <= 0) {
                boardCounter_.erase(it);
            }
        }
    }
    // Pop last move and restore info snapshot
    const Move move = moveLog_.back();
    moveLog_.pop_back();
    if (!infoLog_.empty()) {
        info_ = infoLog_.back();
        infoLog_.pop_back();
    }
    // Restore moved piece to start square
    board_[move.startRow][move.startCol] = move.pieceMoved;
    if (move.isEnPassantMove) {
        // Restore captured pawn behind the destination square
        const int capRow = move.endRow + player_; // player_ is the mover after switching back
        if (inBounds(capRow, move.endCol)) {
            board_[capRow][move.endCol] = move.pieceCaptured;
        }
        // Destination square was empty in EP captures
        board_[move.endRow][move.endCol] = 0;
    } else {
        // Normal capture or quiet move (also covers promotions because we restore pieceMoved at start)
        board_[move.endRow][move.endCol] = move.pieceCaptured;
        // If king moved, restore king location and undo rook move if castling
        if (move.pieceMoved == 6 || move.pieceMoved == -6) {
            const int usIdx = sideIndex(player_);
            info_.kingLocations[usIdx] = {move.startRow, move.startCol};
            if (move.isCastlingMove) {
                if (move.endCol - move.startCol == 2) {
                    // King-side: rook f -> h (i.e., rook currently at endCol-1 goes back to 7)
                    board_[move.endRow][7] = board_[move.endRow][move.endCol - 1];
                    board_[move.endRow][move.endCol - 1] = 0;
                } else {
                    // Queen-side: rook d -> a (i.e., rook currently at endCol+1 goes back to 0)
                    board_[move.endRow][0] = board_[move.endRow][move.endCol + 1];
                    board_[move.endRow][move.endCol + 1] = 0;
                }
            }
        }
    }
    if (reCalculateMoves) {
        scanAndUpdate();
    }
}

void GameState::updateKingSafety(const Move& move) {
    const int idx = sideIndex(player_);
    const auto [kingRow, kingCol] = info_.kingLocations[idx];
    // reset block mask
    info_.block_mask.clear();
    bool inCheck = false;
    int attackingPiece = 0; // abs piece type; 7 => multiple attackers
    int attackingPieceRow = -1;
    int attackingPieceCol = -1;
    const bool hasDiscovered = (move.discoveredCheck.first != -1);
    if (move.isCheck) {
        inCheck = true;
        attackingPiece = std::abs(move.pieceMoved);
        attackingPieceRow = move.endRow;
        attackingPieceCol = move.endCol;
        if (hasDiscovered) {
            attackingPiece = 7; // multiple attackers
        }
    } else if (hasDiscovered) {
        inCheck = true;
        // if en passant and double discoveredCheck == (-2,-2), indicate multiple attackers
        if (move.isEnPassantMove &&
            move.discoveredCheck.first == -2) {
            attackingPiece = 7;
        } else {
            attackingPieceRow = move.discoveredCheck.first;
            attackingPieceCol = move.discoveredCheck.second;
            attackingPiece = std::abs(board_[attackingPieceRow][attackingPieceCol]);
        }
    }
    info_.inCheck[idx] = inCheck;
    // Build block mask squares if single attacker
    if (inCheck && attackingPiece != 7) {
        // Knight, pawn, king: only capturing attacker resolves (no interposition)
        if (attackingPiece == 2 || attackingPiece == 1 || attackingPiece == 6) {
            info_.block_mask.insert({attackingPieceRow, attackingPieceCol});
        } else {
            // Sliding piece: add all squares between king and attacker, plus attacker square
            const int directionRow = (attackingPieceRow > kingRow) - (attackingPieceRow < kingRow);
            const int directionCol = (attackingPieceCol > kingCol) - (attackingPieceCol < kingCol);
            int currRow = kingRow + directionRow;
            int currCol = kingCol + directionCol;
            while (!(currRow == attackingPieceRow && currCol == attackingPieceCol)) {
                info_.block_mask.insert({currRow, currCol});
                currRow += directionRow;
                currCol += directionCol;
            }
            info_.block_mask.insert({attackingPieceRow, attackingPieceCol});
        }
    }
    // Update potential pins: first friendly piece along each king ray
    static constexpr int dirs[8][2] = {
        {-1,-1}, {-1,0}, {-1,1},
        {0,-1},          {0,1},
        {1,-1},  {1,0},  {1,1}
    };
    info_.potentialPins.clear();
    for (const auto& d : dirs) {
        int currRow = kingRow;
        int currCol = kingCol;
        while (true) {
            currRow += d[0];
            currCol += d[1];
            if (!inBounds(currRow, currCol)) break;
            const int piece = board_[currRow][currCol];
            if (piece == 0) continue;
            // Friendly piece: potential pin square
            if ((piece > 0) == (player_ > 0)) {
                info_.potentialPins.insert({currRow, currCol});
                break;
            }
            // Enemy piece blocks the ray (no friendly piece before it)
            break;
        }
    }
    // Update check squares for this side
    updateCheckSquares();
}

void GameState::updateCheckSquares() {
    // reset
    for (auto& s : info_.checkSquares) s.clear();
    const int enemyIdx = sideIndex(-player_);
    const auto [enemyKingR, enemyKingC] = info_.kingLocations[enemyIdx];
    // ---- Pawns (squares from which a pawn of 'player' would attack enemy king) ----
    {
        static constexpr int dc[2] = {-1, 1};
        for (int i = 0; i < 2; ++i) {
            const int r = enemyKingR + player_;
            const int c = enemyKingC + dc[i];
            if (inBounds(r, c)) {
                info_.checkSquares[1].insert({r, c});
            }
        }
    }
    // ---- Knights ----
    {
        static constexpr int kMoves[8][2] = {
            {-2,-1}, {-2, 1}, {-1,-2}, {-1, 2},
            { 1,-2}, { 1, 2}, { 2,-1}, { 2, 1}
        };
        for (const auto& m : kMoves) {
            const int r = enemyKingR + m[0];
            const int c = enemyKingC + m[1];
            if (inBounds(r, c)) {
                info_.checkSquares[2].insert({r, c});
            }
        }
    }
    // ---- Bishops / Queens (diagonals) ----
    {
        static constexpr int dirs[4][2] = {
            {-1,-1}, {-1, 1}, { 1,-1}, { 1, 1}
        };
        for (const auto& d : dirs) {
            int r = enemyKingR;
            int c = enemyKingC;
            while (true) {
                r += d[0];
                c += d[1];
                if (!inBounds(r, c)) break;
                // Add the square whether empty or occupied; stop after first occupied.
                info_.checkSquares[3].insert({r, c}); // bishop-check squares
                info_.checkSquares[5].insert({r, c}); // queen-check squares
                if (board_[r][c] != 0) break;
            }
        }
    }
    // ---- Rooks / Queens (files & ranks) ----
    {
        static constexpr int dirs[4][2] = {
            {-1, 0}, { 1, 0}, { 0,-1}, { 0, 1}
        };
        for (const auto& d : dirs) {
            int r = enemyKingR;
            int c = enemyKingC;
            while (true) {
                r += d[0];
                c += d[1];
                if (!inBounds(r, c)) break;
                info_.checkSquares[4].insert({r, c}); // rook-check squares
                info_.checkSquares[5].insert({r, c}); // queen-check squares
                if (board_[r][c] != 0) break;
            }
        }
    }
}

// Return true if (pieceRow, pieceCol) is attacked by opponent pieces.
bool GameState::isAttacked(int pieceRow, int pieceCol) const {
    // ---- Knights ----
    static constexpr int knightMoves[8][2] = {
        {-2,-1}, {-2, 1}, {-1,-2}, {-1, 2},
        { 1,-2}, { 1, 2}, { 2,-1}, { 2, 1}
    };
    for (const auto& m : knightMoves) {
        const int r = pieceRow + m[0];
        const int c = pieceCol + m[1];
        if (inBounds(r, c) && board_[r][c] == -2 * player_) {
            return true;
        }
    }
    // ---- Bishops / Queens (diagonals) ----
    static constexpr int diagDirs[4][2] = {
        {-1,-1}, {-1, 1}, { 1,-1}, { 1, 1}
    };
    for (const auto& d : diagDirs) {
        int r = pieceRow;
        int c = pieceCol;
        while (true) {
            r += d[0];
            c += d[1];
            if (!inBounds(r, c)) break;
            const int piece = board_[r][c];
            if (piece == 0) continue;

            if (piece == -3 * player_ || piece == -5 * player_) {
                return true;
            }
            break; // blocked by some piece
        }
    }
    // ---- Rooks / Queens (orthogonal) ----
    static constexpr int orthoDirs[4][2] = {
        {-1, 0}, { 1, 0}, { 0,-1}, { 0, 1}
    };
    for (const auto& d : orthoDirs) {
        int r = pieceRow;
        int c = pieceCol;
        while (true) {
            r += d[0];
            c += d[1];
            if (!inBounds(r, c)) break;
            const int piece = board_[r][c];
            if (piece == 0) continue;
            if (piece == -4 * player_ || piece == -5 * player_) {
                return true;
            }
            break;
        }
    }
    // ---- Pawns ----
    {
        const int r = pieceRow - player_;
        if (r >= 0 && r < 8) {
            const int leftC = pieceCol - 1;
            const int rightC = pieceCol + 1;
            if (leftC >= 0 && board_[r][leftC] == -1 * player_) return true;
            if (rightC < 8 && board_[r][rightC] == -1 * player_) return true;
        }
    }
    // ---- King ----
    static constexpr int kingMoves[8][2] = {
        {-1,-1}, {-1, 0}, {-1, 1},
        { 0,-1},          { 0, 1},
        { 1,-1}, { 1, 0}, { 1, 1}
    };
    for (const auto& m : kingMoves) {
        const int r = pieceRow + m[0];
        const int c = pieceCol + m[1];
        if (inBounds(r, c) && board_[r][c] == -6 * player_) {
            return true;
        }
    }
    return false;
}

void GameState::updateValidMoves(int row, int col) {
    const int piece = board_[row][col];
    if (piece == 0) return;
    if ((piece > 0) != (player_ > 0)) return; // not our piece
    const int idx = sideIndex(player_);
    // Double check: in check AND blockMask is empty => only king moves allowed
    if (info_.inCheck[idx] && info_.block_mask.empty()) {
        if (std::abs(piece) == 6) {
        getKingMoves(row, col);
        }
        return;
    }
    if (std::abs(piece) == 1) {
        getPawnMoves(row, col);
    } else if (std::abs(piece) == 2) {
        getKnightMoves(row, col);
    } else if (std::abs(piece) == 3 || std::abs(piece) == 4 || std::abs(piece) == 5) {
        getRayMoves(row, col, piece);
    } else if (std::abs(piece) == 6) {
        getKingMoves(row, col);
    }
}

bool GameState::checkMoveSafety(const Move& move) {
    const int player = player_; // side making this move
    // Save overwritten squares
    const int startPiece = board_[move.startRow][move.startCol];
    const int endPiece   = board_[move.endRow][move.endCol];
    // Make move
    board_[move.startRow][move.startCol] = 0;
    board_[move.endRow][move.endCol]     = move.pieceMoved;
    // En passant: remove captured pawn behind destination
    int epCapRow = -1;
    if (move.isEnPassantMove) {
        epCapRow = move.endRow + player;
        if (inBounds(epCapRow, move.endCol)) {
            board_[epCapRow][move.endCol] = 0;
        }
    }
    // Find king square after move
    int kingRow, kingCol;
    if (move.pieceMoved * player == 6) {
        kingRow = move.endRow;
        kingCol = move.endCol;
    } else {
        const int idx = sideIndex(player);
        kingRow = info_.kingLocations[idx].first;
        kingCol = info_.kingLocations[idx].second;
    }
    // Determine if king is attacked by opponent
    const bool inCheck = isAttacked(kingRow, kingCol);
    // Undo move
    if (move.isEnPassantMove) {
        // Restore captured pawn and clear destination (was empty before EP)
        if (inBounds(epCapRow, move.endCol)) {
            board_[epCapRow][move.endCol] = move.pieceCaptured;
        }
        board_[move.endRow][move.endCol] = 0;
    } else {
        board_[move.endRow][move.endCol] = endPiece; // same as move.pieceCaptured
    }
    board_[move.startRow][move.startCol] = startPiece;
    return !inCheck;
}

// -----------------------------------------------------------------------------// isPinned
// Returns true if the piece being moved is pinned to our king.
// Uses player_ as the moving side.
// -----------------------------------------------------------------------------
bool GameState::isPinned(const Move& move) const {
    const int player = player_;
    const int idx = sideIndex(player);
    // Quick reject: if not marked as potentially pinned, it's not pinned.
    if (info_.potentialPins.find(Square{move.startRow, move.startCol}) == info_.potentialPins.end()) {
        return false;
    }
    const int kingRow = info_.kingLocations[idx].first;
    const int kingCol = info_.kingLocations[idx].second;
    const int pinnedDirR = (move.startRow > kingRow) - (move.startRow < kingRow);
    const int pinnedDirC = (move.startCol > kingCol) - (move.startCol < kingCol);
    const int moveDirR = (move.endRow > move.startRow) - (move.endRow < move.startRow);
    const int moveDirC = (move.endCol > move.startCol) - (move.endCol < move.startCol);
    // If move stays on the pin line (same direction or opposite), it's allowed => not "illegal by pin"
    if ((pinnedDirR == moveDirR && pinnedDirC == moveDirC) ||
        (pinnedDirR == -moveDirR && pinnedDirC == -moveDirC)) {
        return false;
    }
    // Ray from the moved piece away from king, look for an enemy slider that pins it.
    int r = move.startRow;
    int c = move.startCol;
    while (true) {
        r += pinnedDirR;
        c += pinnedDirC;
        if (!inBounds(r, c)) break;
        const int piece = board_[r][c];
        if (piece == 0) continue;
        // Friendly piece blocks the ray => no pin
        if ((piece > 0) == (player > 0)) {
            break;
        }
        // Enemy piece: check if it's the right slider to pin along this direction
        if (pinnedDirR == 0 || pinnedDirC == 0) {
            // orthogonal: rook or queen
            if (piece == -4 * player || piece == -5 * player) {
                return true;
            }
        } else {
            // diagonal: bishop or queen
            if (piece == -3 * player || piece == -5 * player) {
                return true;
            }
        }
        break;
    }
    return false;
}

inline bool inSet(const std::unordered_set<Square, SquareHash>& s,
                  int r, int c)
{
    return s.find(Square{r, c}) != s.end();
}

// Returns:
//   {-1,-1} : none
//   {r,c}   : square of the friendly checking piece causing discovered check
//   {-2,-2} : special marker for en-passant double discovery
std::pair<int,int> GameState::discoveredCheck(const Move& move) const {
    const int player = player_;           // side making the move
    const int enemyIdx = sideIndex(-player);
    // If start square isn't on queen-check rays to enemy king, no discovered check
    if (!inSet(info_.checkSquares[5], move.startRow, move.startCol)) {
        if (move.isEnPassantMove) {
            // Check for single discovered check via en passant (special case)
            const int epRow = move.endRow + player;
            const int epCol = move.endCol;
            if (inBounds(epRow, epCol) && inSet(info_.checkSquares[3], epRow, epCol)) {
                // Create a "virtual move" for the pawn that got removed by EP
                // from (epRow, epCol) to (move.endRow, epCol).
                const int moved = board_[epRow][epCol];
                const int captured = board_[move.endRow][epCol]; // usually 0
                Move virtualMove(epRow, epCol, move.endRow, epCol, moved, captured);
                return discoveredCheck(virtualMove);
            }
        }
        return {-1, -1};
    }
    const int kingRow = info_.kingLocations[enemyIdx].first;
    const int kingCol = info_.kingLocations[enemyIdx].second;
    const int dirR = (move.startRow > kingRow) - (move.startRow < kingRow);
    const int dirC = (move.startCol > kingCol) - (move.startCol < kingCol);
    const int moveDirR = (move.endRow > move.startRow) - (move.endRow < move.startRow);
    const int moveDirC = (move.endCol > move.startCol) - (move.endCol < move.startCol);
    // If non-knight moves along the king-line (away or along), no discovered check
    if (std::abs(move.pieceMoved) != 2 &&
        ((dirR == moveDirR && dirC == moveDirC) || (dirR == -moveDirR && dirC == -moveDirC))) {
        return {-1, -1};
    }
    // Ray-cast from the moved piece away from the enemy king direction
    int r = move.startRow;
    int c = move.startCol;
    while (true) {
        r += dirR;
        c += dirC;
        if (!inBounds(r, c)) break;
        const int piece = board_[r][c];
        if (piece == 0) continue;
        // Enemy piece blocks the ray
        if ((piece > 0) != (player > 0)) {
            break;
        }
        // Friendly piece behind moved piece: if slider aligned, discovered check
        const bool ortho = (dirR == 0 || dirC == 0);
        if (ortho) {
            if (piece == 4 * player || piece == 5 * player) {
                // Check for double discovered check (EP rare case)
                if (move.isEnPassantMove) {
                    const int epRow = move.endRow + player;
                    const int epCol = move.endCol;
                    if (inBounds(epRow, epCol) && inSet(info_.checkSquares[3], epRow, epCol)) {
                        const int moved = board_[epRow][epCol];
                        const int captured = board_[move.endRow][epCol];
                        Move virtualMove(epRow, epCol, move.endRow, epCol, moved, captured);
                        const auto second = discoveredCheck(virtualMove);
                        if (second.first != -1) {
                            return {-2, -2};
                        }
                    }
                }
                return {r, c};
            }
        } else {
            if (piece == 3 * player || piece == 5 * player) {
                // Check for double discovered check (EP rare case)
                if (move.isEnPassantMove) {
                    const int epRow = move.endRow + player;
                    const int epCol = move.endCol;
                    if (inBounds(epRow, epCol) && inSet(info_.checkSquares[3], epRow, epCol)) {
                        const int moved = board_[epRow][epCol];
                        const int captured = board_[move.endRow][epCol];
                        Move virtualMove(epRow, epCol, move.endRow, epCol, moved, captured);
                        const auto second = discoveredCheck(virtualMove);
                        if (second.first != -1) {
                            return {-2, -2};
                        }
                    }
                }
                return {r, c};
            }
        }
        break; // friendly but not a relevant slider -> stops the scan
    }
    // Final EP-only fallback: single discovered check via en passant
    if (move.isEnPassantMove) {
        const int epRow = move.endRow + player;
        const int epCol = move.endCol;
        if (inBounds(epRow, epCol) && inSet(info_.checkSquares[3], epRow, epCol)) {
            const int moved = board_[epRow][epCol];
            const int captured = board_[move.endRow][epCol];
            Move virtualMove(epRow, epCol, move.endRow, epCol, moved, captured);
            return discoveredCheck(virtualMove);
        }
    }
    return {-1, -1};
}

void GameState::getPawnMoves(int row, int col) {
    const int player = player_;
    const int idx = sideIndex(player);
    const bool inCheck = info_.inCheck[idx];
    const int startRow = (player == 1) ? 6 : 1;
    const int oneStepRow = row - player;
    const bool canOneStep = inBounds(oneStepRow, col) && board_[oneStepRow][col] == 0;
    // -------- Forward moves (1-step and 2-step) --------
    if (canOneStep) {
        Move m(row, col, oneStepRow, col, board_[row][col], board_[oneStepRow][col]);
        if (!isPinned(m)) {
            // Must block/capture checking piece if in check and not king move (blockMask semantics)
            if (!inCheck || inSet(info_.block_mask, oneStepRow, col)) {
                // Promotion
                if (oneStepRow == 0 || oneStepRow == 7) {
                    static constexpr int promoPieces[4] = {5, 4, 3, 2}; // Q,R,B,N
                    for (int p : promoPieces) {
                        Move pm(row, col, oneStepRow, col, board_[row][col], 0);
                        pm.pawnPromotion = p * player;
                        pm.isCheck = inSet(info_.checkSquares[p], oneStepRow, col);
                        pm.discoveredCheck = discoveredCheck(pm);
                        validMoves_.push_back(std::move(pm));
                    }
                } else {
                    m.isCheck = inSet(info_.checkSquares[1], oneStepRow, col);
                    m.discoveredCheck = discoveredCheck(m);
                    validMoves_.push_back(std::move(m));
                }
            }
            // Two-step from starting rank (only if 1-step was empty and we are on startRow)
            const int twoStepRow = row - 2 * player;
            if (row == startRow && inBounds(twoStepRow, col) && board_[twoStepRow][col] == 0) {
                Move m2(row, col, twoStepRow, col, board_[row][col], board_[twoStepRow][col]);
                if (!inCheck || inSet(info_.block_mask, twoStepRow, col)) {
                    m2.isCheck = inSet(info_.checkSquares[1], twoStepRow, col);
                    m2.discoveredCheck = discoveredCheck(m2);
                    validMoves_.push_back(std::move(m2));
                }
            }
        }
    }
    // -------- Captures (including EP) --------
    static constexpr int dcs[2] = {-1, 1};
    for (int dc : dcs) {
        const int endCol = col + dc;
        if (!inBounds(oneStepRow, endCol)) continue;
        const int target = board_[oneStepRow][endCol];
        // Normal capture
        if (target * player < 0) {
            Move m(row, col, oneStepRow, endCol, board_[row][col], target);
            if (!isPinned(m)) {
                if (!inCheck || inSet(info_.block_mask, oneStepRow, endCol)) {
                    // Promotion capture
                    if (oneStepRow == 0 || oneStepRow == 7) {
                        static constexpr int promoPieces[4] = {5, 4, 3, 2};
                        for (int p : promoPieces) {
                            Move pm(row, col, oneStepRow, endCol, board_[row][col], target);
                            pm.pawnPromotion = p * player;
                            pm.isCheck = inSet(info_.checkSquares[p], oneStepRow, endCol);
                            pm.discoveredCheck = discoveredCheck(pm);
                            validMoves_.push_back(std::move(pm));
                        }
                    } else {
                        m.isCheck = inSet(info_.checkSquares[1], oneStepRow, endCol);
                        m.discoveredCheck = discoveredCheck(m);
                        validMoves_.push_back(std::move(m));
                    }
                }
            }
        }
        // En passant capture (destination equals enPassantPossible)
        else if (info_.enPassantPossible.first == oneStepRow &&
                 info_.enPassantPossible.second == endCol) {
            Move m(row, col, oneStepRow, endCol, board_[row][col], /*captured*/ -1 * player);
            m.isEnPassantMove = true;
            if (!isPinned(m)) {
                if (!inCheck || inSet(info_.block_mask, oneStepRow, endCol)) {
                    m.isCheck = inSet(info_.checkSquares[1], oneStepRow, endCol);
                    m.discoveredCheck = discoveredCheck(m);
                    validMoves_.push_back(std::move(m));
                }
            }
        }
    }
}

void GameState::getKnightMoves(int row, int col) {
    const int player = player_;
    const int idx = sideIndex(player);
    static constexpr int knightMoves[8][2] = {
        {-2,-1}, {-2, 1}, {-1,-2}, {-1, 2},
        { 1,-2}, { 1, 2}, { 2,-1}, { 2, 1}
    };
    // Return if pinned
    Move probe(row, col, row, col, board_[row][col], board_[row][col]);
    if (isPinned(probe)) return;
    const bool inCheck = info_.inCheck[idx];
    const std::pair<int,int> disc = discoveredCheck(probe);
    for (const auto& off : knightMoves) {
        const int endRow = row + off[0];
        const int endCol = col + off[1];
        if (!inBounds(endRow, endCol)) continue;
        // can land on empty or enemy
        if (board_[endRow][endCol] * player > 0) continue;
        Move m(row, col, endRow, endCol, board_[row][col], board_[endRow][endCol]);
        // If in check, knight move must go to a square in block_mask
        if (inCheck && !inSet(info_.block_mask, endRow, endCol)) continue;
        m.isCheck = inSet(info_.checkSquares[2], endRow, endCol);
        m.discoveredCheck = disc;
        validMoves_.push_back(std::move(m));
    }
}

void GameState::getRayMoves(int row, int col, int piece) {
    const int player = player_;
    const int idx = sideIndex(player);
    const bool inCheck = info_.inCheck[idx];
    const int absPiece = std::abs(piece);
    // Choose directions
    const int (*dirs)[2] = nullptr;
    int dirCount = 0;
    static constexpr int bishopDirs[4][2] = {
        {-1,-1}, {-1, 1}, { 1,-1}, { 1, 1}
    };
    static constexpr int rookDirs[4][2] = {
        {-1, 0}, { 1, 0}, { 0,-1}, { 0, 1}
    };
    static constexpr int queenDirs[8][2] = {
        {-1,-1}, {-1, 1}, { 1,-1}, { 1, 1},
        {-1, 0}, { 1, 0}, { 0,-1}, { 0, 1}
    };
    if (absPiece == 3) { dirs = bishopDirs; dirCount = 4; }
    else if (absPiece == 4) { dirs = rookDirs; dirCount = 4; }
    else if (absPiece == 5) { dirs = queenDirs; dirCount = 8; }
    else return;
    for (int di = 0; di < dirCount; ++di) {
        const int dr = dirs[di][0];
        const int dc = dirs[di][1];
        int r = row + dr;
        int c = col + dc;
        // Step to first square in direction
        if (!inBounds(r, c)) continue;
        // Friendly piece blocks immediately
        if (board_[r][c] * player > 0) continue;
        // For each direction: first move computes pin/discovered logic
        Move firstMove(row, col, r, c, board_[row][col], board_[r][c]);
        if (isPinned(firstMove)) {
            continue;
        }
        // queen can't give discovered check (so store either {-1,-1} or computed)
        std::pair<int,int> disc = {-1, -1};
        if (absPiece != 5) {
            disc = discoveredCheck(firstMove);
        }
        // Emit first move if legal with check-block mask
        if (!inCheck || inSet(info_.block_mask, r, c)) {
            firstMove.isCheck = inSet(info_.checkSquares[absPiece], r, c);
            firstMove.discoveredCheck = disc;
            validMoves_.push_back(std::move(firstMove));
        }
        // If first square was an enemy piece, ray stops
        if (board_[r][c] * player < 0) continue;
        // Continue sliding further
        while (true) {
            r += dr;
            c += dc;
            if (!inBounds(r, c)) break;
            if (board_[r][c] * player > 0) break; // friendly blocks
            Move m(row, col, r, c, board_[row][col], board_[r][c]);
            if (!inCheck || inSet(info_.block_mask, r, c)) {
                m.isCheck = inSet(info_.checkSquares[absPiece], r, c);
                m.discoveredCheck = disc;
                validMoves_.push_back(std::move(m));
            }
            if (board_[r][c] * player < 0) break; // capture ends ray
        }
    }
}

void GameState::getKingMoves(int row, int col) {
    const int player = player_;
    const int idx = sideIndex(player);
    static constexpr int kingOffsets[8][2] = {
        {-1,-1}, {-1, 0}, {-1, 1},
        { 0,-1},          { 0, 1},
        { 1,-1}, { 1, 0}, { 1, 1}
    };
    // Normal king moves
    for (const auto& off : kingOffsets) {
        const int endRow = row + off[0];
        const int endCol = col + off[1];
        if (!inBounds(endRow, endCol)) continue;
        // can't land on friendly piece
        if (board_[endRow][endCol] * player > 0) continue;
        Move m(row, col, endRow, endCol, board_[row][col], board_[endRow][endCol]);
        if (checkMoveSafety(m)) {
            m.discoveredCheck = discoveredCheck(m); // same as python
            validMoves_.push_back(std::move(m));
        }
    }
    // Castling moves (only if not currently in check)
    if (info_.inCheck[idx]) return;
    const auto [canK, canQ] = info_.castlingRights[idx];
    // King side: (row,col)->(row,col+2)
    if (canK) {
        if (inBounds(row, col + 2) &&
            board_[row][col + 1] == 0 &&
            board_[row][col + 2] == 0) {
            // Squares king passes through must not be attacked
            const bool a1 = isAttacked(row, col + 1);
            const bool a2 = isAttacked(row, col + 2);
            if (!a1 && !a2) {
                Move castle(row, col, row, col + 2, board_[row][col], 0);
                castle.isCastlingMove = true;
                if (inSet(info_.checkSquares[4], row, col + 1)) {
                    castle.discoveredCheck = {row, col + 1};
                }
                validMoves_.push_back(std::move(castle));
            }
        }
    }
    // Queen side: (row,col)->(row,col-2)
    if (canQ) {
        if (inBounds(row, col - 3) &&
            board_[row][col - 1] == 0 &&
            board_[row][col - 2] == 0 &&
            board_[row][col - 3] == 0) {
            const bool a1 = isAttacked(row, col - 1);
            const bool a2 = isAttacked(row, col - 2);
            if (!a1 && !a2) {
                Move castle(row, col, row, col - 2, board_[row][col], 0);
                castle.isCastlingMove = true;
                if (inSet(info_.checkSquares[4], row, col - 1)) {
                    castle.discoveredCheck = {row, col - 1};
                }
                validMoves_.push_back(std::move(castle));
            }
        }
    }
}