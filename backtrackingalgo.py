def backtrack(grid, r, c, end, visited, greens, path, total_greens):
    rows = len(grid)
    cols = len(grid[0])

    # Out of bounds of rood schijfje
    if r < 0 or r >= rows or c < 0 or c >= cols:
        return False
    
    if grid[r][c] == 1 or visited[r][c]:
        # =1 betekend rode schijf
        return False

    visited[r][c] = True
    path.append((r, c))

    added_green = False
    if grid[r][c] == 2 and (r, c) not in greens:
        greens.add((r, c))
        added_green = True

    #Check of het klaar is
    if (r, c) == end and len(greens) == total_greens:
        return True

    #Ga naar naburige kanten
    for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
        if backtrack(grid, r+dr, c+dc, end, visited, greens, path, total_greens):
            return True

    # Backtrack
    if added_green:
        greens.remove((r,c))
    visited[r][c] = False
    path.pop()
    return False

# Grid and setup
grid = [
    [0, 0, 0, 0, 0],
    [2, 1, 0, 1, 0],
    [0, 0, 2, 1, 0],
    [0, 1, 1, 1, 0]
]

total_greens = sum(row.count(2) for row in grid) #tel aantal groene schijfjes
start = (0,0)
end = (3,4)
visited = [[False]*len(grid[0]) for _ in range(len(grid))] #maak een 2D list even groot als grid met alles = 0
greens = set()
path = []

if backtrack(grid, start[0], start[1], end, visited, greens, path, total_greens):
    print("Path found:")
    print(path)
else:
    print("No valid path")