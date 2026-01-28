// perft_test.cpp
// Build example (g++): g++ -O3 -std=c++17 perft_test.cpp GameState.cpp -o perft
// Run: ./perft 5

#include "ChessBackend.h"
#include <chrono>
#include <cstdint>
#include <iostream>
#include <vector>

struct PerftStats {
    std::uint64_t nodes = 0;
    std::uint64_t captures = 0;
    std::uint64_t checks = 0;
    std::uint64_t mates = 0;
    std::uint64_t discoveredChecks = 0;
    std::uint64_t enPassants = 0;
    std::uint64_t castles = 0;
    std::uint64_t promotions = 0;
    std::uint64_t doubleChecks = 0;
};

// NOTE: Your GameState currently keeps validMoves_ private.
// Add ONE small accessor in your header:
//
//   const std::vector<Move>& validMoves() const { return validMoves_; }
//
// or make perft_test a friend.
// This file assumes you added:
//   const std::vector<Move>& validMoves() const;
// and (optionally) access to info_:
//   const Info& info() const { return info_; }
//
// If you don't want to expose info, you can skip mates counting.

void perft(GameState& gs, int depth, PerftStats& total) {
    const auto moves = gs.validMoves(); // accessor needed
    if (depth == 1) { 
        total.nodes += moves.size();
        for (const Move& mv : moves) {
            if (mv.pieceCaptured != 0) total.captures++;
            if (mv.isCheck) total.checks++;
            if (mv.discoveredCheck.first != -1) total.discoveredChecks++;
            if (mv.isEnPassantMove) total.enPassants++;
            if (mv.isCastlingMove) total.castles++;
            if (mv.pawnPromotion != 0) total.promotions++;
            if (mv.isCheck && mv.discoveredCheck.first != -1) total.doubleChecks++;
            gs.makeMove(mv);
            const int w = gs.info().winner; // accessor needed
            if (w == 1 || w == -1) total.mates++;
            gs.undoMove(false);
        }
    }
    else{
        for (const Move& mv : moves) {
            gs.makeMove(mv);
            perft(gs, depth - 1, total);
            gs.undoMove(false);
        }
    }
}

int main(int argc, char** argv) {
    int depth = 5;
    if (argc >= 2) {
        depth = std::max(1, std::atoi(argv[1]));
    }
    GameState gs;
    // Ensure initial moves exist (your constructor calls scanAndUpdate already,
    // but calling it again is safe if you're unsure).
    gs.scanAndUpdate();
    const auto t0 = std::chrono::high_resolution_clock::now();
    PerftStats s{};
    perft(gs, depth, s);
    const auto t1 = std::chrono::high_resolution_clock::now();
    const std::chrono::duration<double> elapsed = t1 - t0;
    const double secs = elapsed.count();
    std::cout << "Perft to depth " << depth << ": " << s.nodes << " nodes\n";
    std::cout << "Captures: " << s.captures
              << ", Checks: " << s.checks
              << ", Checkmates: " << s.mates << "\n";
    std::cout << "Discovered Checks: " << s.discoveredChecks
              << ", En Passants: " << s.enPassants
              << ", Castles: " << s.castles << "\n";
    std::cout << "Promotions: " << s.promotions
              << ", Double Checks: " << s.doubleChecks << "\n";
    std::cout << "Time taken: " << secs << " seconds\n";
    if (secs > 0.0) {
        std::cout << "Nodes per second: " << (static_cast<double>(s.nodes) / secs) << "\n";
    }
    return 0;
}