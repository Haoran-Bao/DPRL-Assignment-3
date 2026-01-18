import numpy as np
from copy import deepcopy
import random
from math import log, sqrt
import tkinter as tk
from functools import partial
class leaf:
    def __init__(self, board, player, game, parent=None, move=None):
        self.board = board
        self.player = player
        self.game = game
        self.parent = parent
        self.move = move

        self.children = []
        self.untried_moves = game.possible_moves(board)

        self.wins = 0
        self.visits = 0

    def is_terminal(self):
        return self.game.check_winner(self.board) != 0

    def best_child_uct(self, c=sqrt(2)):
        best_score = -float("inf")
        best_child = None
        for child in self.children:
            if child.visits == 0:
                return child
            exploit = child.wins / child.visits
            explore = c * sqrt(log(self.visits) / child.visits)
            score = exploit + explore
            if score > best_score:
                best_score = score
                best_child = child
        return best_child

    def expand(self):
        move = random.choice(self.untried_moves)
        new_board = self.board.copy()
        new_board[move] = self.player
        child = leaf(
            board=new_board,
            player=-self.player,
            game=self.game,
            parent=self,
            move=move
        )
        self.untried_moves.remove(move)
        self.children.append(child)
        return child

class TicTacToe:
    def __init__(self):
        self.debug = False
        self.board = np.zeros((3, 3), dtype=int)  # 0=empty, -1=O (player), 1=X (AI)
        self.board[1,1]= 1
        self.current_player = 1  # Starts with X (1)
        self.root_player = self.current_player

    def reset(self):
        self.board = np.zeros((3, 3), dtype=int)
        self.current_player = 1
    def print_board(self, board):
        symbols = {1: 'X', -1: 'O', 0: ' '}
        for row in board:
            print(' | '.join(symbols[c] for c in row))
            print('-' * 10)
    def possible_moves(self,board):
        return [(i, j) for i in range(3) for j in range(3) if board[i, j] == 0]
    def check_winner(self, board):
            # rows, cols
            for i in range(3):
                if abs(sum(board[i, :])) == 3:
                    return int(np.sign(sum(board[i, :])))
                if abs(sum(board[:, i])) == 3:
                    return int(np.sign(sum(board[:, i])))
            # diags
            if abs(sum(board.diagonal())) == 3:
                return int(np.sign(sum(board.diagonal())))
            if abs(sum(np.fliplr(board).diagonal())) == 3:
                return int(np.sign(sum(np.fliplr(board).diagonal())))
            if not self.possible_moves(board):
                return 2  # draw
            return 0
    
    def rollout(self, node: leaf):
        board = node.board.copy()
        current_player = node.player
        game = node.game

        while True:
            result = game.check_winner(board)
            if result != 0:
                break
            moves = game.possible_moves(board)
            if not moves:
                result = 2
                break
            move = random.choice(moves)
            board[move] = current_player
            current_player *= -1

        return result
        
    

    def MCTS(self, root:leaf, iterations=10000):
        root_player = root.player  

        for _ in range(iterations):
            node = root

            # Selection
            while not node.untried_moves and not node.is_terminal():
                node = node.best_child_uct()

            # Expansion
            if node.untried_moves and not node.is_terminal():
                node = node.expand()

            # Simulation
            result = self.rollout(node)

            # Backpropagation 
            if result == 2:
                reward = 0
            elif result == root_player:
                reward = 1.0
            else:
                reward = 0.0

            while node is not None:
                node.visits += 1
                node.wins += reward
                node = node.parent

        #Actual decision -> no UTC but most visited child
        best_child = max(root.children, key=lambda ch: ch.visits)
        return best_child.move, best_child


class TicTacToeGUI:
    def __init__(self):
        self.game = TicTacToe()
        self.human_player = -1
        self.ai_player = 1

        self.window = tk.Tk()
        self.window.title("Tic-Tac-Toe MCTS")

        self.buttons = [[None for _ in range(3)] for _ in range(3)]
        
        self.status_label = tk.Label(self.window, text="Your turn (O)", font=("Arial", 14))
        self.status_label.grid(row=0, column=0, columnspan=3, pady=10)

        # 3x3 grid of buttons
        for i in range(3):
            for j in range(3):
                btn = tk.Button(
                    self.window,
                    text=" ",
                    font=("Arial", 24),
                    width=3,
                    height=1,
                    command=partial(self.on_click, i, j)
                )
                btn.grid(row=i+1, column=j, padx=5, pady=5)
                self.buttons[i][j] = btn
        self.game.board[1,1]= 1
        self.buttons[1][1].config(text="X")
        # Reset button
        self.reset_button = tk.Button(self.window, text="Reset", command=self.reset_game)
        self.reset_button.grid(row=4, column=0, columnspan=3, pady=10)

        self.game_over = False

    def reset_game(self):
        self.game.board[:] = 0
        self.game_over = False
        self.status_label.config(text="Your turn (O)")
        for i in range(3):
            for j in range(3):
                self.buttons[i][j].config(text=" ", state=tk.NORMAL)
        self.game.board[1,1]= 1
        self.buttons[1][1].config(text="X")

    def on_click(self, i, j):
        if self.game_over:
            return
        if self.game.board[i, j] != 0:
            return  # already occupied

        
        self.game.board[i, j] = self.human_player
        self.buttons[i][j].config(text="O")

        result = self.game.check_winner(self.game.board)
        if result != 0:
            self.end_game(result)
            return

        
        self.status_label.config(text="Loading...")
        self.window.update_idletasks()

        root = leaf(board=self.game.board.copy(), player=self.ai_player, game=self.game)
        best_move, best_child = self.game.MCTS(root, iterations=500)

        if best_move is not None:
            r, c = best_move
            self.game.board[r, c] = self.ai_player
            self.buttons[r][c].config(text="X")

        result = self.game.check_winner(self.game.board)
        if result != 0:
            self.end_game(result)
        else:
            self.status_label.config(text="Your turn (O)")

    def end_game(self, result):
        self.game_over = True
        for i in range(3):
            for j in range(3):
                self.buttons[i][j].config(state=tk.DISABLED)

        if result == 1:
            self.status_label.config(text="X wins!")
        elif result == -1:
            self.status_label.config(text="O wins!")
        elif result == 2:
            self.status_label.config(text="Draw!")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    gui = TicTacToeGUI()
    gui.run()
