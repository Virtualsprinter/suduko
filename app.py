import io
import re
import sys
from flask import Flask, render_template, request, jsonify
from sudoko import sudoko
from image_parser import parse_sudoku_image

app = Flask(__name__)

DEFAULT_PUZZLE = [
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


@app.route("/")
def index():
    return render_template("index.html", default_puzzle=DEFAULT_PUZZLE)


@app.route("/solve", methods=["POST"])
def solve():
    puzzle = request.get_json().get("puzzle")
    s = sudoko(puzzle)
    # Capture stdout to extract the order cells were solved
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()
    try:
        s.solve()
    finally:
        sys.stdout = old_stdout
    sol = s.solution()
    solved = all(sol[r][c] != 0 for r in range(9) for c in range(9))
    # Parse lines like: "Solved row elimination : 3 7 : 5"
    order = []
    for line in captured.getvalue().splitlines():
        m = re.match(r"Solved .+ : (\d+) (\d+) : \d+", line)
        if m:
            order.append([int(m.group(1)) - 1, int(m.group(2)) - 1])
    return jsonify({"solution": sol, "solved": solved, "order": order})


@app.route("/parse-image", methods=["POST"])
def parse_image():
    f = request.files.get("image")
    if not f:
        return jsonify({"error": "No image provided"}), 400

    try:
        grid = parse_sudoku_image(f.read())
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Parsing failed: {e}"}), 500

    return jsonify({"puzzle": grid})


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
