function makeChart(id, config) {
  const element = document.getElementById(id);
  if (!element || !window.Chart) return;
  new Chart(element, config);
}

const green = "#0f7a4a";
const dark = "#042c1c";
const mint = "#9ee6bd";

makeChart("dashboardChart", {
  type: "bar",
  data: {
    labels: ["Checklists", "Hazards", "Open", "Workers"],
    datasets: [{ label: "Safety Metrics", data: window.dashboardData || [0, 0, 0, 0], backgroundColor: [green, "#d1a526", "#c9372c", dark], borderRadius: 8 }]
  },
  options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
});

makeChart("severityChart", {
  type: "doughnut",
  data: {
    labels: window.severityLabels?.length ? window.severityLabels : ["No data"],
    datasets: [{ data: window.severityValues?.length ? window.severityValues : [1], backgroundColor: [green, mint, "#d1a526", "#c9372c"] }]
  },
  options: { responsive: true, plugins: { legend: { position: "bottom" } } }
});

makeChart("zoneChart", {
  type: "line",
  data: {
    labels: window.zoneLabels?.length ? window.zoneLabels : ["No data"],
    datasets: [{ label: "Checklists", data: window.zoneValues?.length ? window.zoneValues : [0], borderColor: green, backgroundColor: "rgba(15,122,74,.14)", tension: .35, fill: true }]
  },
  options: { responsive: true, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } }
});
