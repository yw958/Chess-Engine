#pragma once
#include <array>
#include <cstdint>
#include <cmath>

namespace PieceTables {
    using Table8 = std::array<std::array<int, 8>, 8>;
    // --- Piece-square tables (your exact numbers) ---
    inline constexpr Table8 knightScores{{
        {{1,1,1,1,1,1,1,1}},
        {{1,2,2,2,2,2,2,1}},
        {{1,2,3,3,3,3,2,1}},
        {{1,2,3,4,4,3,2,1}},
        {{1,2,3,4,4,3,2,1}},
        {{1,2,3,3,3,3,2,1}},
        {{1,2,2,2,2,2,2,1}},
        {{1,1,1,1,1,1,1,1}},
    }};

    inline constexpr Table8 bishopScores{{
        {{4,3,2,1,1,2,3,4}},
        {{3,4,3,2,2,3,4,3}},
        {{2,3,4,3,3,4,3,2}},
        {{1,2,3,4,4,3,2,1}},
        {{1,2,3,4,4,3,2,1}},
        {{2,3,4,3,3,4,3,2}},
        {{3,4,3,2,2,3,4,3}},
        {{4,3,2,1,1,2,3,4}},
    }};

    inline constexpr Table8 queenScores{{
        {{1,1,1,3,1,1,1,1}},
        {{1,2,3,3,3,1,1,1}},
        {{1,4,3,3,3,4,2,1}},
        {{1,2,3,3,3,2,2,1}},
        {{1,2,3,3,3,2,2,1}},
        {{1,4,3,3,3,4,2,1}},
        {{1,1,2,3,3,1,1,1}},
        {{1,1,1,3,1,1,1,1}},
    }};

    inline constexpr Table8 rookScores{{
        {{4,3,4,4,4,4,3,4}},
        {{4,4,4,4,4,4,4,4}},
        {{1,1,2,3,3,2,1,1}},
        {{1,2,3,4,4,3,2,1}},
        {{1,2,3,4,4,3,2,1}},
        {{1,1,2,3,3,2,1,1}},
        {{4,4,4,4,4,4,4,4}},
        {{4,3,4,4,4,4,3,4}},
    }};

    inline constexpr Table8 whitePawnScores{{
        {{8,8,8,8,8,8,8,8}},
        {{8,8,8,8,8,8,8,8}},
        {{5,6,6,7,7,6,6,5}},
        {{2,3,3,5,5,3,3,2}},
        {{1,2,3,4,4,3,2,1}},
        {{1,1,2,3,3,2,1,1}},
        {{1,1,1,0,0,1,1,1}},
        {{0,0,0,0,0,0,0,0}},
    }};

    inline constexpr Table8 blackPawnScores{{
        {{0,0,0,0,0,0,0,0}},
        {{1,1,1,0,0,1,1,1}},
        {{1,1,2,3,3,2,1,1}},
        {{1,2,3,4,4,3,2,1}},
        {{2,3,3,5,5,3,3,2}},
        {{5,6,6,7,7,6,6,5}},
        {{8,8,8,8,8,8,8,8}},
        {{8,8,8,8,8,8,8,8}},
    }};
    // Index is absolute piece code (1..6);
    inline constexpr std::array<char, 13> PIECES = {
        '?', 'P', 'N', 'B', 'R', 'Q', 'K', 'k', 'q', 'r', 'b', 'n', 'p'
    };
    // ---------------- Utility API ----------------

    // piece: signed piece code (±1..±6)
    // row, col: board square
    inline int positionalScore(int piece, int row, int col) {
        if (piece == 0) return 0;
        const int absP = std::abs(piece);
        if (absP == 1) {
            return (piece > 0)
                ? whitePawnScores[row][col]
                : blackPawnScores[row][col];
        }
        switch (absP) {
            case 2: return knightScores[row][col];
            case 3: return bishopScores[row][col];
            case 4: return rookScores[row][col];
            case 5: return queenScores[row][col];
            default: return 0;
        }
    }

    // Material values
    inline constexpr std::array<int8_t, 7> VALUES = {0,1,3,3,5,9,0};

    // Piece letters
    inline constexpr std::array<char, 7> WHITE_PIECES =
        {'?', 'P', 'N', 'B', 'R', 'Q', 'K'};

    inline constexpr std::array<char, 7> BLACK_PIECES =
        {'?', 'p', 'n', 'b', 'r', 'q', 'k'};

    inline constexpr char pieceChar(int piece) {
        return (piece > 0)
            ? WHITE_PIECES[piece]
            : BLACK_PIECES[-piece];
    }

} // namespace PieceTables