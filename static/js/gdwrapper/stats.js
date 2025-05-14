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

    if (x === "mimeType" && y === "modifiedTime" || y === "mimeType" && x === "modifiedTime" ||
        x === "modifiedTime" && y === "ownerEmail" || y === "modifiedTime" && x === "ownerEmail"
    ) {
        alert("Недопустимая комбинация параметров для отображения статистики");
        return;
    }

    if (x === "size" && y === "modifiedTime") {
        alert("Время изменения будет отображено по оси Х, средний размер файлов по оси Y");
    }

    fetchStatsData(x, y);
}

function fetchStatsData(xAttr, yAttr) {
    fetch(`/stats/data?x=${xAttr}&y=${yAttr}`)
        .then((response) => response.json())
        .then(({ type, data, horizontal }) => {
            switch (type) {
                case "bar":
                    renderBarChart(data, horizontal, xAttr, yAttr);
                    break;
                case "table":
                    renderStatsTable(data, xAttr, yAttr);
                    break;
                case "graph":
                    renderGraph(data, horizontal, xAttr, yAttr);
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

// Функция отображения столбчатых диаграмм
function renderBarChart(data, horizontal, xAttr, yAttr) {
    const tableDiv = document.getElementById("stats-table");
    tableDiv.innerHTML = "";
    document.getElementById("stats-chart").style.display = "block";

    const labels = data.map((item) => item.x);
    const values = data.map((item) => item.y);

    const ctx = document.getElementById("stats-chart").getContext("2d");

    if (chartInstance) {
        chartInstance.destroy();
    }

    const sizeOnYAxis = yAttr === "size";
    const sizeOnXAxis = xAttr === "size";

    chartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: `${yAttr === "size" ? "Размер (КБ)" : yAttr}`,
                data: values,
                backgroundColor: "rgba(54, 162, 235, 0.6)",
                borderColor: "rgba(54, 162, 235, 1)",
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: horizontal ? 'y' : 'x',
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function (context) {
                            let value = context.raw;
                            if (sizeOnYAxis || sizeOnXAxis) {
                                value = value + " КБ";
                            }
                            return `${context.dataset.label}: ${value}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        callback: function (value, index) {
                            if (sizeOnXAxis) {
                                return value + " КБ";
                            }
                            return labels[value];
                        }
                    }
                },
                y: {
                    ticks: {
                        callback: function (value, index) {
                            if (sizeOnYAxis) {
                                return value + " КБ";
                            }
                            return labels[value];
                        }
                    }
                }
            }
        }
    });
}

// Функция отображения таблиц
function renderStatsTable(data, xAttr, yAttr) {
    const chart = document.getElementById("stats-chart");
    chart.style.display = "none";
    const container = document.getElementById("stats-table");
    container.innerHTML = "";

    const columnHeaders = new Set();
    data.forEach(row => {
        Object.keys(row.cols).forEach(col => columnHeaders.add(col));
    });

    const sortedColumns = Array.from(columnHeaders).sort();

    const table = document.createElement("table");
    table.classList.add("table", "table-striped", "table-bordered");

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

// Функция отображения графиков
function renderGraph(data, horizontal, xAttr, yAttr) {
    const tableDiv = document.getElementById("stats-table");
    tableDiv.innerHTML = "";
    document.getElementById("stats-chart").style.display = "block";

    const labels = data.map(item => item.x);
    const values = data.map(item => item.y);

    const ctx = document.getElementById("stats-chart").getContext("2d");

    if (chartInstance) {
        chartInstance.destroy();
    }

    const sizeOnYAxis = yAttr === "size";
    const sizeOnXAxis = xAttr === "size";

    chartInstance = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Размер (КБ)",
                data: values,
                backgroundColor: "rgba(75, 192, 192, 0.4)",
                borderColor: "rgba(75, 192, 192, 1)",
                borderWidth: 2,
                fill: false,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function (context) {
                            let value = context.raw;
                            if (sizeOnYAxis || sizeOnXAxis) {
                                value = value + " КБ";
                            }
                            return `${context.dataset.label}: ${value}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        callback: function (value, index) {
                            if (!horizontal) {
                                if (sizeOnXAxis) {
                                    return value + " КБ";
                                }
                                return labels[value];
                            } else {
                                if (sizeOnYAxis) {
                                    return value + " КБ";
                                }
                                return labels[value];
                            }
                        }
                    }
                },
                y: {
                    ticks: {
                        callback: function (value, index) {
                            if (!horizontal) {
                                if (sizeOnYAxis) {
                                    return value + " КБ";
                                }
                                return labels[value];
                            } else {
                                if (sizeOnXAxis) {
                                    return value + " КБ";
                                }
                                return labels[value];
                            }
                        }
                    }
                }
            }
        }
    });
}