#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>


//////////////////////////////////////////////////////////////
// Move
//////////////////////////////////////////////////////////////

struct Move {
    int startRow, startCol;
    int endRow, endCol;
    int pieceMoved = 0;
    int pieceCaptured = 0;
    bool isCastlingMove = false;
    bool isEnPassantMove = false;
    int pawnPromotion = 0;
    bool isCheck = false;
    // If discovered check occurs, store square of checking piece
    // (-1,-1) means none, (-2, -2) means en passant double discovery (extremely rare)
    std::pair<int,int> discoveredCheck = {-1, -1};
    std::string getChessNotation() const;
    Move(int sRow, int sCol, int eRow, int eCol, int moved, int captured)
        : startRow(sRow), startCol(sCol), endRow(eRow), endCol(eCol),
          pieceMoved(moved), pieceCaptured(captured) {}
};

//////////////////////////////////////////////////////////////
// Info
//////////////////////////////////////////////////////////////

struct Info {
    // index: 1 = white, 2 = black (0 unused)
    std::array<std::pair<bool,bool>, 3> castlingRights{
        std::make_pair(false, false),
        std::make_pair(true,  true),
        std::make_pair(true,  true)
    };
    std::array<std::pair<int,int>, 3> kingLocations{
        std::make_pair(0,0),
        std::make_pair(7,4),
        std::make_pair(0,4)
    };
    std::array<bool, 3> inCheck{false, false, false};
    uint64_t block_mask = 0ULL;
    std::pair<int,int> enPassantPossible = {-1, -1};
    int winner = 2;  // 1 white, -1 black, 0 draw, 2 ongoing
    int seventyFiveMoveRuleCounter = 0;
    // index 1–5 correspond to piece types
    uint64_t potentialPins = 0ULL;
    std::array<uint64_t, 6> checkSquares{};
    double eval = 0.0;
};

//////////////////////////////////////////////////////////////
// GameState
//////////////////////////////////////////////////////////////

class GameState {
public:
    using Board = std::array<std::array<int, 8>, 8>;
    GameState();
    // Core update
    std::string scanAndUpdate();
    // Move handling
    void makeMove(const Move& move);
    void undoMove(bool reCalculateMoves = true);
    // Attack / legality
    bool isAttacked(int row, int col) const;
    void updateKingSafety(const Move& move);
    void updateCheckSquares();
    void updateValidMoves(int row, int col);
    bool checkMoveSafety(const Move& move);
    bool isPinned(const Move& move) const;
    std::pair<int,int> discoveredCheck(const Move& move) const;
    // Move generation
    void getPawnMoves(int row, int col);
    void getKnightMoves(int row, int col);
    void getRayMoves(int row, int col, int piece);
    void getKingMoves(int row, int col);
    // Accessors
    const Info& info() const { return info_; }
    const std::vector<Move>& validMoves() const { return validMoves_; }
private:
    static constexpr bool inBounds(int r, int c) {
        return r >= 0 && r < 8 && c >= 0 && c < 8;
    }
    std::string buildBoardRep() const;

private:
    Board board_{};
    int player_ = 1;
    std::vector<Move> moveLog_;
    std::vector<Info> infoLog_;
    Info info_;
    std::vector<std::string> boardHistory_;
    std::unordered_map<std::string, int> boardCounter_;
    std::vector<Move> validMoves_;
};
