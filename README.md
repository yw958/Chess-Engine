# Chess Engine (Python)

A Python chess framework that includes backend logic, a graphical user interface, and a negamax engine with alpha-beta pruning.

## Components

- **ChessBackend.py**: Core logic for representing the chess game state, making/undoing moves, and generating valid moves.
- **ChessMain.py**: User interface for the chess game, handling graphics and user interactions.
- **ChessEngine.py**: Chess engine implementing a negamax algorithm with alpha-beta pruning.

## Keyboard Shortcuts

- **Z**: Undo the last move
- **F**: Flip the board orientation
- **E**: Enable engine for the current player
- **D**: Disable engine

## References

- Frontend interface inspired by the tutorial: <https://www.youtube.com/watch?v=EnYui0e73Rs&list=PLBwF487qi8MGU81nDGaeNE1EnNEPYWKY_>
- Reference repository: <https://github.com/BigFish2086/chess?tab=readme-ov-file#engine-improvements-todo>

The backend logic is original with a significant performance boost compared to the referenced repository. 

## Future Improvements
- Implement engine in C++ for performance enhancement, and connect via pybind11.
- Try Monte Carlo Tree Search (MCTS) for move selection.