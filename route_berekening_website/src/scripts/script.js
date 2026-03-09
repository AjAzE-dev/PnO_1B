const container = document.querySelector('.container');
const saveBtn = document.getElementById('saveBtn');
const rows = 5;
const cols = 7;
const bolletjes = [];

function backtrack(grid, r, c, end, visited, greens, path, totalGreens, start) {
    //het algoritme is zelf gemaakt in python en door AI omgezet in javascript
    const rows = grid.length;
    const cols = grid[0].length;

    if (r < 0 || r >= rows || c < 0 || c >= cols) return;
    if (grid[r][c] === 1 || visited[r][c]) return;
    if (bestPath !== null && path.length >= bestPath.length) return;

    visited[r][c] = true;
    path.push([r, c]);

    let addedGreen = false;
    if (grid[r][c] === 2 && !greens.has(`${r},${c}`)) {
        greens.add(`${r},${c}`);
        addedGreen = true;
    }

    if (r === end[0] && c === end[1] && greens.size === totalGreens) {
        if (bestPath === null || path.length < bestPath.length) {
            bestPath = path.slice();
        }
    } else {
        const directions = [[1,0], [-1,0], [0,1], [0,-1]];
        for (let [dr, dc] of directions) {
            backtrack(grid, r + dr, c + dc, end, visited, greens, path, totalGreens, start);
        }
    }

    if (addedGreen) {
        greens.delete(`${r},${c}`);
    }
    visited[r][c] = false;
    path.pop();
}

let bestPath = null;

for (let r = 0; r <= rows; r++) {
    const line = document.createElement('div');
    line.className = 'line horizontal';
    line.style.top = `${(r / rows) * 100}%`;
    container.appendChild(line);
}

for (let c = 0; c <= cols; c++) {
    const line = document.createElement('div');
    line.className = 'line vertical';
    line.style.left = `${(c / cols) * 100}%`;
    container.appendChild(line);
}

for (let r = 1; r < rows; r++) {
    for (let c = 1; c < cols; c++) {
        const bol = document.createElement('div');
        bol.className = 'bol';
        bol.dataset.clicks = 0;
        bol.style.left = `${(c / cols) * 100}%`;
        bol.style.top = `${(r / rows) * 100}%`;
        bol.addEventListener('click', () => {
            let clicks = (parseInt(bol.dataset.clicks) + 1) % 5;
            bol.dataset.clicks = clicks;
            bol.style.backgroundColor = ['white', 'red', 'green', 'blue', 'purple'][clicks];
        });
        container.appendChild(bol);
        bolletjes.push({ element: bol, row: r, col: c });
    }
}

saveBtn.addEventListener('click', () => {
    const grid = [];
    for (let r = 0; r < 4; r++) {
        const rowArray = [];
        for (let c = 0; c < 6; c++) {
            const b = bolletjes.find(item => item.row === r+1 && item.col === c+1);
            rowArray.push(parseInt(b.element.dataset.clicks));
        }
        grid.push(rowArray);
    }

    let start = null;
    let end = null;
    for (let r = 0; r < grid.length; r++) {
        for (let c = 0; c < grid[0].length; c++) {
            if (grid[r][c] === 3) start = [r, c];
            if (grid[r][c] === 4) end = [r, c];
        }
    }

    if (!start || !end) {
        document.getElementById('result').innerHTML = 'Please set exactly one start (blue) and one end (purple).';
        return;
    }

    const totalGreens = grid.flat().filter(cell => cell === 2).length;

    bestPath = null;
    const visited = Array.from({length: grid.length}, () => Array(grid[0].length).fill(false));
    const greens = new Set();
    const path = [];

    backtrack(grid, start[0], start[1], end, visited, greens, path, totalGreens, start);

    const resultDiv = document.getElementById('result');
    if (bestPath) {
        resultDiv.innerHTML = `Shortest valid path: ${JSON.stringify(bestPath)}<br>Length: ${bestPath.length}`;
    } else {
        resultDiv.innerHTML = 'No valid path';
    }
});