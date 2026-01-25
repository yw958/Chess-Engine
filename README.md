# Chess Engine (Python)

A Python chess framework that includes backend logic, a graphical user interface, and a negamax engine with alpha-beta pruning and quiescence search.

## Instructions
1. Clone this repository 
2. It is recommended to create a virtual environment with python 3.12 or higher:
    - `python -m venv venv`
    - On Windows: `.\venv\Scripts\activate`
    - On macOS/Linux: `source venv/bin/activate`
3. Install the required packages: `python -m pip install -r ./requirements.txt`
4. Run `python -m Chess.ChessMain` to start the game.
5. Enjoy the game!

## Keyboard Shortcuts

- **Z**: Undo the last move
- **F**: Flip the board orientation
- **E**: Enable/switch engine for the current player
- **D**: Disable engine

## Components

- **ChessMain.py**: User interface for the chess game, handling graphics and user interactions. You can adjust engine depth in this file.
- **ChessBackend.py**: Core logic for representing the chess game state, making/undoing moves, and generating valid moves.
- **ChessEngine.py**: Chess engine implementing a negamax algorithm with alpha-beta pruning and quiescence search.

## References

- Frontend interface inspired by the tutorial: <https://www.youtube.com/watch?v=EnYui0e73Rs&list=PLBwF487qi8MGU81nDGaeNE1EnNEPYWKY_>
- Reference repository: <https://github.com/BigFish2086/chess?tab=readme-ov-file#engine-improvements-todo>

The backend logic is original with a significant performance boost compared to the referenced repository. 

## Future Improvements
- Implement backend in C++ for performance enhancement, and connect via pybind11.
- Try Monte Carlo Tree Search (MCTS).
- Implement magic bitboards for faster move generation.