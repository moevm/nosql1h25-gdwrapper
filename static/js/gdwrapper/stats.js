document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("stats-form");
    if (form) {
        form.addEventListener("submit", handleStatsFormSubmit);
    }
});

function handleStatsFormSubmit(event) {
    event.preventDefault();

    const x = document.getElementById("x-select").value;
    const y = document.getElementById("y-select").value;

    if (x === y) {
        alert("Поля X и Y не могут совпадать");
        return;
    }

    fetchStatsData(x, y);
}

function fetchStatsData(xAttr, yAttr) {
    fetch(`/stats/data?x=${xAttr}&y=${yAttr}`)
        .then((response) => response.json())
        .then(({ type, data }) => {
            switch (type) {
                case "bar":
                    renderBarChart(data, xAttr, yAttr);
                    break;
                case "table":
                    renderStatsTable(data, xAttr, yAttr);
                    break;
                case "graph":
                    renderGraph(data, xAttr, yAttr);
                    break;
                default:
                    alert("Невозможно построить график для выбранных параметров.");
            }
        })
        .catch((error) => {
            console.error("Ошибка при получении статистики:", error);
        });
}

let chartInstance = null;

function renderBarChart(data, xAttr, yAttr) {
    const tableDiv = document.getElementById("stats-table");
    tableDiv.innerHTML = "";
    document.getElementById("stats-chart").style.display = "block";

    const labels = data.map((item) => item.x);
    const values = data.map((item) => item.y);

    const ctx = document.getElementById("stats-chart").getContext("2d");

    if (chartInstance) {
        chartInstance.destroy();
    }

    const isXAxisNumeric = typeof data[0]?.x === "number";

    chartInstance = new Chart(ctx, {
        type: isXAxisNumeric ? "line" : "bar",
        data: {
            labels: labels,
            datasets: [{
                label: `${yAttr} по ${xAttr}`,
                data: values,
                backgroundColor: "rgba(54, 162, 235, 0.6)",
                borderColor: "rgba(54, 162, 235, 1)",
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                    display: 'true'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function renderStatsTable(data, xAttr, yAttr) {
    const chart = document.getElementById("stats-chart");
    chart.style.display = "none";
    const container = document.getElementById("stats-table");
    container.innerHTML = "";

    // Соберем уникальные заголовки столбцов
    const columnHeaders = new Set();
    data.forEach(row => {
        Object.keys(row.cols).forEach(col => columnHeaders.add(col));
    });

    const sortedColumns = Array.from(columnHeaders).sort();

    const table = document.createElement("table");
    table.classList.add("table", "table-striped", "table-bordered");

    // Заголовок таблицы
    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");

    const cornerCell = document.createElement("th");
    cornerCell.textContent = xAttr + " \\ " + yAttr;
    headRow.appendChild(cornerCell);

    sortedColumns.forEach(col => {
        const th = document.createElement("th");
        th.textContent = col;
        headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    // Тело таблицы
    const tbody = document.createElement("tbody");
    data.forEach(row => {
        const tr = document.createElement("tr");
        const rowHeader = document.createElement("th");
        rowHeader.textContent = row.row;
        tr.appendChild(rowHeader);

        sortedColumns.forEach(col => {
            const td = document.createElement("td");
            td.textContent = row.cols[col] || 0;
            tr.appendChild(td);
        });

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.appendChild(table);
}