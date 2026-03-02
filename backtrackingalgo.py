
best_path = None

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

# --- Grid setup ---
grid = [
    [0, 0, 0, 0, 0],
    [2, 1, 0, 1, 0],
    [0, 0, 2, 0, 0],
    [0, 1, 1, 1, 0]
]

total_greens = sum(row.count(2) for row in grid)
start = (0,0)
end = (3,4)

visited = [[False]*len(grid[0]) for _ in range(len(grid))]
greens = set()
path = []

backtrack(grid, start[0], start[1], end, visited, greens, path, total_greens, start)

if best_path:
    print("Shortest valid path found:")
    print(best_path)
    print("Length:", len(best_path))
else:
    print("No valid path")