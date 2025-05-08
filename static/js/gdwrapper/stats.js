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
        .then((json) => {
            renderStatsChart(json.data, xAttr, yAttr);
        })
        .catch((error) => {
            console.error("Ошибка при получении данных статистики:", error);
        });
}

let chartInstance = null;

function renderStatsChart(data, xAttr, yAttr) {
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