const container = document.querySelector('.container');
const saveBtn = document.getElementById('saveBtn');
const clearBtn = document.getElementById('clearBtn');
const sendBtn = document.getElementById('sendBtn');
const connectBtn = document.getElementById('connectBtn');
const resultDiv = document.getElementById('result');
const picoIPInput = document.getElementById('picoIP');

const rows = 5;
const cols = 7;
const bolletjes = [];

let bestPath = null;
let lastPath = null;
let socket = undefined;
let grid = null;
let klokInterval = null;
let startTijd = null;

// --- KLOK LOGICA ---

function startKlok() {
    startTijd = Date.now();
    if (klokInterval) clearInterval(klokInterval);
    klokInterval = setInterval(() => {
        const verstreken = Date.now() - startTijd;
        const seconden = Math.floor(verstreken / 1000);
        const ms = Math.floor((verstreken % 1000) / 10);
        document.getElementById('klok').textContent =
            `${seconden}.${ms.toString().padStart(2, '0')}s`;
    }, 50);
}

function stopKlok() {
    if (klokInterval) {
        clearInterval(klokInterval);
        klokInterval = null;
    }
}

// --- WEBSOCKET LOGICA ---

function getPicoIP() {
    return picoIPInput.value.trim() || "192.168.4.1";
}

connectBtn.addEventListener('click', () => {
    connectBtn.textContent = 'Connecting…';
    connectBtn.disabled = true;

    const ip = getPicoIP();
    socket = new WebSocket(`ws://${ip}:80/connect-websocket`);

    socket.onopen = () => {
        console.log("Connected to Pico");
        connectBtn.textContent = '✓ Connected';
        connectBtn.style.backgroundColor = 'rgb(34, 197, 94)';
        connectBtn.style.color = 'white';
        connectBtn.style.borderColor = 'rgb(34, 197, 94)';
        connectBtn.disabled = false;
    };

    socket.onmessage = (event) => {
        console.log("Pico response:", event.data);
        if (event.data.includes("Pad voltooid")) {
            stopKlok();
        }
    };

    socket.onerror = (error) => {
        console.error("WebSocket Error:", error);
        resultDiv.innerHTML = `<span style="color:red">Verbindingsfout met ${ip}</span>`;
        connectBtn.textContent = 'Connect';
        connectBtn.style.backgroundColor = '';
        connectBtn.style.color = '';
        connectBtn.style.borderColor = '';
        connectBtn.disabled = false;
    };

    socket.onclose = () => {
        socket = undefined;
        console.log("WebSocket closed");
        connectBtn.textContent = 'Connect';
        connectBtn.style.backgroundColor = '';
        connectBtn.style.color = '';
        connectBtn.style.borderColor = '';
        connectBtn.disabled = false;
    };
});

function sendCommand(command) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(command);
        console.log("Verstuurd:", command);
    } else {
        resultDiv.innerHTML = `<span style="color:red">Niet verbonden. Druk eerst op Connect.</span>`;
    }
}

document.querySelector('.stopBtn').addEventListener('click', () => {
    sendCommand('stop');
});

// --- GRID & PAD LOGICA ---

// Richtingen: 0=omhoog, 1=rechts, 2=omlaag, 3=links
const DIRS = [[-1, 0], [0, 1], [1, 0], [0, -1]];

// State: (r, c, richting) — richting = aankomstrichting (4 = geen/start)
// Dit laat de auto toe om 180° te draaien: dezelfde cel is bereikbaar
// vanuit elke richting onafhankelijk, maar nooit tweemaal vanuit dezelfde richting.

function backtrack(grid, r, c, dir, end, visited, greens, path, totalGreens, start) {
    const rows = grid.length;
    const cols = grid[0].length;

    if (r < 0 || r >= rows || c < 0 || c >= cols) return;
    if (grid[r][c] === 1) return; // obstakel

    const isLoop = end[0] === start[0] && end[1] === start[1];
    const isEnd = r === end[0] && c === end[1];

    // Bezoek-check op (cel, richting): elke aankomstrichting telt apart
    const stateKey = `${r},${c},${dir}`;
    if (visited.has(stateKey)) return;

    // Snoei: pad is al langer dan beste gevonden pad
    if (bestPath !== null && path.length >= bestPath.length) return;

    visited.add(stateKey);
    path.push([r, c]);

    let addedGreen = false;
    const cellKey = `${r},${c}`;
    if (grid[r][c] === 2 && !greens.has(cellKey)) {
        greens.add(cellKey);
        addedGreen = true;
    }

    const allGreens = greens.size === totalGreens;

    if (isEnd && allGreens && (!isLoop || path.length > 1)) {
        if (bestPath === null || path.length < bestPath.length) {
            bestPath = path.slice();
        }
    } else {
        for (let d = 0; d < 4; d++) {
            const [dr, dc] = DIRS[d];
            backtrack(grid, r + dr, c + dc, d, end, visited, greens, path, totalGreens, start);
        }
    }

    if (addedGreen) greens.delete(cellKey);
    visited.delete(stateKey);
    path.pop();
}

// Teken Grid Lijnen
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

// Maak Bolletjes
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

// Herstel Grid uit LocalStorage
const savedGridStr = localStorage.getItem('savedGrid');
if (savedGridStr) {
    grid = JSON.parse(savedGridStr);
    grid.forEach((rowArr, r) => {
        rowArr.forEach((clicks, c) => {
            const b = bolletjes.find(item => item.row === r + 1 && item.col === c + 1);
            if (b) {
                b.element.dataset.clicks = clicks;
                b.element.style.backgroundColor = ['white', 'red', 'green', 'blue', 'purple'][clicks];
            }
        });
    });
}

// Bereken Pad Knop
saveBtn.addEventListener('click', () => {
    grid = [];
    for (let r = 0; r < 4; r++) {
        const rowArray = [];
        for (let c = 0; c < 6; c++) {
            const b = bolletjes.find(item => item.row === r + 1 && item.col === c + 1);
            rowArray.push(parseInt(b.element.dataset.clicks));
        }
        grid.push(rowArray);
    }

    localStorage.setItem('savedGrid', JSON.stringify(grid));

    let start = null, end = null;
    for (let r = 0; r < grid.length; r++) {
        for (let c = 0; c < grid[0].length; c++) {
            if (grid[r][c] === 3) start = [r, c];
            if (grid[r][c] === 4) end = [r, c];
        }
    }

    if (!start) {
        resultDiv.innerHTML = 'Stel een startpunt in (blauw).';
        lastPath = null;
        return;
    }
    if (!end) end = start;

    const totalGreens = grid.flat().filter(cell => cell === 2).length;
    bestPath = null;

    // Start met richting 4 (geen richting = startpositie)
    backtrack(grid, start[0], start[1], 4, end, new Set(), new Set(), [], totalGreens, start);

    if (bestPath) {
        lastPath = bestPath;
        resultDiv.innerHTML = `Pad gevonden! Lengte: ${bestPath.length}`;
        console.log("Kortste pad:", JSON.stringify(lastPath));
    } else {
        lastPath = null;
        resultDiv.innerHTML = 'Geen geldig pad mogelijk.';
    }
});

// Clear Grid Knop
clearBtn.addEventListener('click', () => {
    bolletjes.forEach(b => {
        b.element.dataset.clicks = 0;
        b.element.style.backgroundColor = 'white';
    });
    localStorage.removeItem('savedGrid');
    lastPath = null;
    resultDiv.innerHTML = 'Grid leeggemaakt.';
});

// Verzend Pad Knop
sendBtn.addEventListener('click', () => {
    if (!lastPath || !grid) {
        resultDiv.innerHTML = '<span style="color:red">Bereken eerst een pad.</span>';
        return;
    }

    const groeneStops = lastPath.filter(([r, c]) => grid[r][c] === 2);
    const message = JSON.stringify({ pad: lastPath, groen: groeneStops });

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(message);
        resultDiv.innerHTML = `Pad verstuurd naar Pico!`;
        startKlok();
    } else {
        resultDiv.innerHTML = '<span style="color:red">Niet verbonden. Druk eerst op Connect.</span>';
    }
});