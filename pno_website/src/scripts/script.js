const container = document.querySelector('.container');
const saveBtn = document.getElementById('saveBtn');

const rows = 5;
const cols = 7;
const bolletjes = [];

// Teken lijnen
for (let r = 0; r <= rows; r++) {
    const line = document.createElement('div');
    line.classList.add('line', 'horizontal');
    line.style.top = `${(r / rows) * 100}%`;
    container.appendChild(line);
}

for (let c = 0; c <= cols; c++) {
    const line = document.createElement('div');
    line.classList.add('line', 'vertical');
    line.style.left = `${(c / cols) * 100}%`;
    container.appendChild(line);
}

// Maak interactieve punten
for (let r = 1; r < rows; r++) {
    for (let c = 1; c < cols; c++) {
        const bol = document.createElement('div');
        bol.classList.add('bol');
        bol.dataset.clicks = 0;
        bol.style.left = `${(c / cols) * 100}%`;
        bol.style.top = `${(r / rows) * 100}%`;

        bol.addEventListener('click', () => {
            let clicks = (parseInt(bol.dataset.clicks) + 1) % 3;
            bol.dataset.clicks = clicks;
            
            const colors = ['white', 'green', 'red'];
            bol.style.backgroundColor = colors[clicks];
        });

        container.appendChild(bol);
        bolletjes.push({ element: bol, row: r, col: c });
    }
}

// Data verwerking en verzenden
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

    fetch("http://<raspberrypi_ip>/set_pions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ grid: grid })
    })
    .then(res => res.ok ? alert("Verzonden!") : Promise.reject())
    .catch(err => console.error("Fout:", err));
});