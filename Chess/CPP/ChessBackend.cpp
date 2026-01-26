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
        // Your python code overwrites the capture form with the non-capture form (bug).
        // Here we implement the intended behavior:
        // capture: "exd8=Q" (using your style: startFile x endFile endRank = Q)
        // non-capture: "e7e8=Q" (your style: startFile startRank endFile endRank = Q)
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
            // Use uppercase piece letters for captures (same as your python PIECES[abs(pieceMoved)])
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
            const int sq = static_cast<int>(board_[r][c]);
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
            score += (static_cast<double>(PieceTables::VALUES[std::abs(sq)]) + posScore) * (sq > 0 ? 1.0 : -1.0);
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
                // your python passed (r,c) tuple; here it's flattened to int position
                // If you prefer, change updateValidMoves signature to (row,col).
                updateValidMoves(r * 8 + c);
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
    // --- insufficient material draw checks (same as your python) ---
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
    // Return your compact rep: "{placement} {stm} {castling} {ep}"
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