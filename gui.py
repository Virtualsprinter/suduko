import tkinter as tk
from tkinter import messagebox
from sudoko import sudoko

default_puzzle = [
    [6,0,0,0,0,0,0,0,0],
    [0,0,8,0,0,7,9,0,0],
    [0,1,4,0,8,5,0,0,0],
    [0,0,0,0,6,0,0,0,0],
    [0,7,0,0,0,0,1,0,2],
    [0,9,0,1,0,2,0,0,5],
    [0,0,2,0,0,9,0,3,0],
    [0,0,0,0,1,4,0,8,0],
    [0,3,0,0,0,0,0,0,1],
]

BG_GRID    = "#333333"
BG_BOX     = "#bbbbbb"
BG_GIVEN   = "#e0e0e0"
BG_EMPTY   = "#ffffff"
BG_SOLVED  = "#c8e6c9"
BG_STUCK   = "#ffcdd2"

FONT_GIVEN  = ("Helvetica", 20, "bold")
FONT_ENTRY  = ("Helvetica", 20)


class SudokuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Solver")
        self.root.resizable(False, False)
        self.cells = [[None]*9 for _ in range(9)]   # (Entry, StringVar)
        self.given  = [[False]*9 for _ in range(9)]
        self._build_grid()
        self._build_buttons()
        self._load_puzzle(default_puzzle)

    # ------------------------------------------------------------------ grid

    def _build_grid(self):
        outer = tk.Frame(self.root, bg=BG_GRID, bd=0)
        outer.pack(padx=12, pady=12)

        for box_row in range(3):
            for box_col in range(3):
                box = tk.Frame(outer, bg=BG_BOX, bd=0)
                box.grid(row=box_row, column=box_col,
                         padx=(0, 3) if box_col < 2 else 0,
                         pady=(0, 3) if box_row < 2 else 0)

                for r in range(3):
                    for c in range(3):
                        row = box_row * 3 + r
                        col = box_col * 3 + c
                        var = tk.StringVar()
                        entry = tk.Entry(
                            box,
                            textvariable=var,
                            width=2,
                            font=FONT_ENTRY,
                            justify="center",
                            bd=0,
                            highlightthickness=1,
                            highlightbackground="#aaaaaa",
                            bg=BG_EMPTY,
                        )
                        entry.grid(row=r, column=c,
                                   padx=(0, 1) if c < 2 else 0,
                                   pady=(0, 1) if r < 2 else 0,
                                   ipady=6)
                        self.cells[row][col] = (entry, var)

    # --------------------------------------------------------------- buttons

    def _build_buttons(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=(0, 12))
        btn = dict(width=12, font=("Helvetica", 12))
        tk.Button(frame, text="Solve",        command=self._solve,        **btn).pack(side=tk.LEFT, padx=6)
        tk.Button(frame, text="Load Default", command=self._load_default, **btn).pack(side=tk.LEFT, padx=6)
        tk.Button(frame, text="Clear",        command=self._clear,        **btn).pack(side=tk.LEFT, padx=6)

    # --------------------------------------------------------------- actions

    def _load_default(self):
        self._load_puzzle(default_puzzle)

    def _load_puzzle(self, puzzle):
        for row in range(9):
            for col in range(9):
                entry, var = self.cells[row][col]
                val = puzzle[row][col]
                entry.config(state=tk.NORMAL)
                var.set(str(val) if val else "")
                if val:
                    entry.config(state=tk.DISABLED,
                                 disabledforeground="#111111",
                                 font=FONT_GIVEN,
                                 bg=BG_GIVEN)
                    self.given[row][col] = True
                else:
                    entry.config(font=FONT_ENTRY, bg=BG_EMPTY)
                    self.given[row][col] = False

    def _get_matrix(self):
        m = []
        for row in range(9):
            r = []
            for col in range(9):
                raw = self.cells[row][col][1].get().strip()
                try:
                    r.append(int(raw) if raw else 0)
                except ValueError:
                    r.append(0)
            m.append(r)
        return m

    def _solve(self):
        m = self._get_matrix()
        s = sudoko(m)
        s.solve()
        sol = s.solution()

        for row in range(9):
            for col in range(9):
                if self.given[row][col]:
                    continue
                entry, var = self.cells[row][col]
                val = sol[row][col]
                entry.config(state=tk.NORMAL)
                var.set(str(val) if val else "")
                entry.config(bg=BG_SOLVED if val else BG_STUCK)

        unsolved = any(sol[r][c] == 0 for r in range(9) for c in range(9))
        if unsolved:
            messagebox.showwarning("Incomplete", "Could not fully solve the puzzle.")
        else:
            messagebox.showinfo("Solved!", "Puzzle solved successfully!")

    def _clear(self):
        for row in range(9):
            for col in range(9):
                entry, var = self.cells[row][col]
                entry.config(state=tk.NORMAL, font=FONT_ENTRY, bg=BG_EMPTY)
                var.set("")
                self.given[row][col] = False


if __name__ == "__main__":
    root = tk.Tk()
    SudokuGUI(root)
    root.mainloop()
