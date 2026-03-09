const container = document.querySelector('.container');
const saveBtn = document.getElementById('saveBtn');
const rows = 5;
const cols = 7;
const bolletjes = [];

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
            let clicks = (parseInt(bol.dataset.clicks) + 1) % 3;
            bol.dataset.clicks = clicks;
            bol.style.backgroundColor = ['white', 'green', 'red'][clicks];
        });
        container.appendChild(bol);
        bolletjes.push({ element: bol, row: r, col: c });
    }
}

saveBtn.addEventListener('click', () => {
    const grid = [];
    for (let r = 1; r < rows; r++) {
        const rowArray = [];
        for (let c = 1; c < cols; c++) {
            const b = bolletjes.find(item => item.row === r && item.col === c);
            rowArray.push(parseInt(b.element.dataset.clicks));
        }
        grid.push(rowArray);
    }

    console.log("Grid data die verzonden wordt:");
    console.table(grid);

    fetch("http://192.168.4.1/set_pions", {
        method: "POST",
        mode: "cors", // Expliciet aangeven
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ grid: grid })
    })
    .then(res => {
        console.log("Server reageert!");
        alert("Succes!");
    })
    .catch(err => {
        console.error("CORS of Netwerkfout. Check of je Pico de juiste headers stuurt.");
    });
});