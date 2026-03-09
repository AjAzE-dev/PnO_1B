import matplotlib.pyplot as plt
import numpy as np

best_path = None  # globale variabele

def visualize(grid, path, start, end):
    global best_path

    arr = np.zeros((len(grid), len(grid[0]), 3))

    # Base grid
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 1:
                arr[r,c] = [1,0,0]          # red
            elif grid[r][c] == 2:
                arr[r,c] = [0,1,0]          # green
            else:
                arr[r,c] = [1,1,1]          # white

    # Draw best path with low opacity (light purple)
    if best_path is not None:
        for r, c in best_path:
            base = arr[r,c]
            overlay = np.array([0.6, 0.3, 1.0])  # soft purple
            alpha = 0.35
            arr[r,c] = (1 - alpha) * base + alpha * overlay

    # Draw current exploration path (solid blue)
    for r, c in path:
        arr[r,c] = [0,0,1]

    # Start and end on top
    sr, sc = start
    er, ec = end
    arr[sr,sc] = [1,1,0]
    arr[er,ec] = [1,0,1]

    plt.imshow(arr, interpolation='none')
    plt.xticks(range(len(grid[0])))
    plt.yticks(range(len(grid)))
    plt.pause(0.1)
    plt.clf()


def backtrack(grid, r, c, end, visited, greens, path, total_greens, start):
    global best_path

    rows = len(grid)
    cols = len(grid[0])

    if r < 0 or r >= rows or c < 0 or c >= cols:
        return

    if grid[r][c] == 1 or visited[r][c]:
        return

    # pruning: stop als pad al slechter is
    if best_path is not None and len(path) >= len(best_path):
        return

    visited[r][c] = True
    path.append((r, c))

    added_green = False
    if grid[r][c] == 2 and (r, c) not in greens:
        greens.add((r, c))
        added_green = True

    visualize(grid, path, start, end)

    # geldige oplossing gevonden
    if (r, c) == end and len(greens) == total_greens:
        if best_path is None or len(path) < len(best_path):
            best_path = path.copy()

    else:
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
            backtrack(grid, r+dr, c+dc, end, visited, greens, path, total_greens, start)

    if added_green:
        greens.remove((r,c))

    visited[r][c] = False
    path.pop()

    visualize(grid, path, start, end)


# --- Grid setup ---
grid = [
    [0, 0, 0, 0, 0],
    [2, 1, 0, 1, 0],
    [0, 0, 2, 0, 0],
    [0, 1, 1, 1, 0]
]

total_greens = sum(row.count(2) for row in grid)
start = (0,0)
end = (0,3)

visited = [[False]*len(grid[0]) for _ in range(len(grid))]
greens = set()
path = []

plt.ion()
fig = plt.figure(figsize=(6,6))

backtrack(grid, start[0], start[1], end, visited, greens, path, total_greens, start)

plt.ioff()
plt.show()

if best_path:
    print("Shortest valid path found:")
    print(best_path)
    print("Length:", len(best_path))
else:
    print("No valid path")