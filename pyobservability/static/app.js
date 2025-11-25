// app/static/app.js
(function () {
  // ------------------------------------------------------------
  // CONFIG
  // ------------------------------------------------------------
  const MAX_POINTS = 60;
  const targets = window.MONITOR_TARGETS || [];

  // ------------------------------------------------------------
  // DOM REFERENCES
  // ------------------------------------------------------------
  const nodeSelect = document.getElementById("node-select");
  const refreshBtn = document.getElementById("refresh-btn");

  const ipEl = document.getElementById("ip");
  const gpuEl = document.getElementById("gpu");
  const memEl = document.getElementById("memory");
  const diskEl = document.getElementById("disk");
  const loadEl = document.getElementById("cpuload");

  const cpuAvgCtx = document.getElementById("cpu-avg-chart").getContext("2d");
  const memCtx = document.getElementById("mem-chart").getContext("2d");
  const loadCtx = document.getElementById("load-chart").getContext("2d");

  const coresGrid = document.getElementById("cores-grid");

  const servicesTableBody = document.querySelector("#services-table tbody");
  const svcFilter = document.getElementById("svc-filter");

  const dockerStatsEl = document.getElementById("docker-stats");
  const containersList = document.getElementById("containers-list");

  const disksTableBody = document.querySelector("#disks-table tbody");
  const certsEl = document.getElementById("certificates");

  const showCoresCheckbox = document.getElementById("show-cores");

  // ------------------------------------------------------------
  // CHART HELPERS
  // ------------------------------------------------------------
  function makeMainChart(ctx, label) {
    const EMPTY = Array(MAX_POINTS).fill(null);
    const LABELS = Array(MAX_POINTS).fill("");

    return new Chart(ctx, {
      type: "line",
      data: {
        labels: [...LABELS],
        datasets: [
          {
            label,
            data: [...EMPTY],
            fill: true,
            tension: 0.2,
            cubicInterpolationMode: "monotone",
            pointRadius: 0
          }
        ]
      },
      options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        spanGaps: false,
        scales: {
          x: { display: false },
          y: {
            beginAtZero: true,
            suggestedMax: 100
          }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }

  function makeCoreSparkline(ctx, coreName) {
    const EMPTY_LABELS = Array(MAX_POINTS).fill("");
    const EMPTY_DATA   = Array(MAX_POINTS).fill(null);

    return new Chart(ctx, {
      type: "line",
      data: {
        labels: [...EMPTY_LABELS],
        datasets: [{
          label: coreName,
          data: [...EMPTY_DATA],
          fill: false,
          tension: 0.2,
          pointRadius: 0
        }]
      },
      options: {
        animation: false,
        responsive: false,
        interaction: false,
        events: [],
        spanGaps: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { display: false },
          y: { display: false, suggestedMax: 100 }
        }
      }
    });
  }

  const cpuAvgChart = makeMainChart(cpuAvgCtx, "CPU Avg");
  const memChart    = makeMainChart(memCtx,    "Memory %");
  const loadChart   = makeMainChart(loadCtx,   "CPU Load");

  // ------------------------------------------------------------
  // CORE SPARKLINE STATE
  // ------------------------------------------------------------
  const coreMini = {};

  function createCoreChart(coreName) {
    const wrapper = document.createElement("div");
    wrapper.className = "core-mini";
    wrapper.innerHTML = `
      <div class="label">${coreName}</div>
      <canvas width="120" height="40"></canvas>
      <div class="value">—</div>
    `;
    coresGrid.appendChild(wrapper);

    const canvas = wrapper.querySelector("canvas");
    const valEl = wrapper.querySelector(".value");
    const chart = makeCoreSparkline(canvas.getContext("2d"), coreName);

    coreMini[coreName] = { chart, el: wrapper, valEl };
    return coreMini[coreName];
  }

  function getCoreChart(coreName) {
    return coreMini[coreName] || createCoreChart(coreName);
  }

  function pruneOldCores(latest) {
    for (const name of Object.keys(coreMini)) {
      if (!latest.includes(name)) {
        try { coreMini[name].chart.destroy(); } catch {}
        coreMini[name].el.remove();
        delete coreMini[name];
      }
    }
  }

  // ------------------------------------------------------------
  // RESET UI
  // ------------------------------------------------------------
  function resetUI() {
    // Pre-fill charts with right-anchored null buffers
    const EMPTY_DATA = Array(MAX_POINTS).fill(null);
    const EMPTY_LABELS = Array(MAX_POINTS).fill("");

    function resetChart(chart) {
      chart.data.labels = [...EMPTY_LABELS];
      chart.data.datasets[0].data = [...EMPTY_DATA];
      chart.update();
    }

    // Reset main charts (CPU Avg, Memory %, CPU Load)
    resetChart(cpuAvgChart);
    resetChart(memChart);
    resetChart(loadChart);

    // Remove all per-core mini charts
    for (const name of Object.keys(coreMini)) {
      try { coreMini[name].chart.destroy(); } catch {}
      coreMini[name].el.remove();
      delete coreMini[name];
    }

    // Reset static UI fields
    ipEl.textContent = "—";
    gpuEl.textContent = "—";
    memEl.textContent = "—";
    diskEl.textContent = "—";
    loadEl.textContent = "—";

    servicesTableBody.innerHTML = "";
    dockerStatsEl.textContent = "—";
    containersList.innerHTML = "";
    disksTableBody.innerHTML = "";
    certsEl.textContent = "—";
  }

  // ------------------------------------------------------------
  // HELPERS
  // ------------------------------------------------------------
  function pushPoint(chart, value) {
    const ts = new Date().toLocaleTimeString();
    chart.data.labels.push(ts);
    chart.data.datasets[0].data.push(isFinite(value) ? Number(value) : NaN);

    if (chart.data.labels.length > MAX_POINTS) {
      chart.data.labels.shift();
      chart.data.datasets[0].data.shift();
    }

    chart.update("none");
  }

  function num(x) {
    const n = Number(x);
    return Number.isFinite(n) ? n : null;
  }

  // ------------------------------------------------------------
  // METRICS HANDLER
  // ------------------------------------------------------------
  function handleMetrics(list) {
    const now = new Date().toLocaleTimeString();

    for (const host of list) {
      if (host.base_url !== selectedBase) continue;
      const m = host.metrics || {};

      // ------------------- BASIC INFO -------------------
      ipEl.textContent = m.ip?.ip || m.ip || "—";
      gpuEl.textContent = JSON.stringify(m.gpu ?? "—", null, 2);
      diskEl.textContent = m.disk ? JSON.stringify(m.disk, null, 0) : "—";

      // ------------------- MEMORY -------------------
      if (m.memory) {
        const used = m.memory.ram_used || m.memory.used || "";
        const percent = m.memory.ram_usage ?? m.memory.usage ?? m.memory.percent ?? "—";
        memEl.textContent = `used: ${used} (${percent}%)`;
        pushPoint(memChart, num(percent));
      }

      // ------------------- CPU -------------------
      let avg = null;

      if (m.cpu) {
        const detail = m.cpu.detail || m.cpu;

        if (typeof detail === "object") {
          const names = Object.keys(detail);
          pruneOldCores(names);

          const values = [];

          for (const [core, val] of Object.entries(detail)) {
            const v = num(val);
            values.push(v);

            const c = getCoreChart(core);
            c.chart.data.labels.push(now);
            c.chart.data.datasets[0].data.push(v ?? 0);

            if (c.chart.data.labels.length > MAX_POINTS) {
              c.chart.data.labels.shift();
              c.chart.data.datasets[0].data.shift();
            }

            c.chart.update("none");
            c.valEl.textContent = `${(v ?? 0).toFixed(1)}%`;
          }

          avg = values.reduce((a, b) => a + (b ?? 0), 0) / values.length;
        }
        else if (typeof detail === "number") {
          avg = detail;
        }
      }

      if (avg != null) pushPoint(cpuAvgChart, avg);

      // ------------------- CPU LOAD -------------------
      if (m.cpu_load) {
        const load = m.cpu_load.detail || m.cpu_load;
        if (typeof load === "object") {
          const m1  = load.m1 ?? load[0];
          const m5  = load.m5 ?? load[1];
          const m15 = load.m15 ?? load[2];

          loadEl.textContent = `${m1} / ${m5} / ${m15}`;
          pushPoint(loadChart, num(m1) ?? 0);
        } else {
          loadEl.textContent = load;
          pushPoint(loadChart, num(load));
        }
      }

      // ------------------- SERVICES -------------------
      if (Array.isArray(m.services)) {
        const filter = svcFilter.value.trim().toLowerCase();
        servicesTableBody.innerHTML = "";

        for (const s of m.services) {
          const name = s.pname || s.label || s.name || "";

          if (filter && !name.toLowerCase().includes(filter)) continue;

          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${s.pid ?? s.PID ?? ""}</td>
            <td>${name}</td>
            <td>${s.status ?? "—"}</td>
            <td>${s.cpu ? JSON.stringify(s.cpu) : "—"}</td>
            <td>${s.memory ? (s.memory.rss || s.memory.pfaults || JSON.stringify(s.memory)) : "—"}</td>
          `;
          servicesTableBody.appendChild(tr);
        }
      }

      // ------------------- DOCKER -------------------
      if (m.docker_stats)
        dockerStatsEl.textContent = JSON.stringify(m.docker_stats, null, 2);

      if (Array.isArray(m.containers)) {
        containersList.innerHTML = "";
        for (const c of m.containers) {
          const li = document.createElement("li");
          li.textContent = c["Container Name"] || c.name || JSON.stringify(c);
          containersList.appendChild(li);
        }
      }

      // ------------------- DISKS -------------------
      if (Array.isArray(m.disks)) {
        disksTableBody.innerHTML = "";
        for (const d of m.disks) {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${d.name || d.device_id || ""}</td>
            <td>${d.size || d.total || ""}</td>
            <td>${(d.mountpoints || []).join(", ")}</td>
          `;
          disksTableBody.appendChild(tr);
        }
      }

      // ------------------- CERTIFICATES -------------------
      if (m.certificates) {
        certsEl.textContent = JSON.stringify(m.certificates, null, 2);
      }
    }
  }

  // ------------------------------------------------------------
  // EVENT BINDINGS
  // ------------------------------------------------------------
  targets.forEach(t => {
    const opt = document.createElement("option");
    opt.value = t.base_url;
    opt.textContent = t.name || t.base_url;
    nodeSelect.appendChild(opt);
  });

  let selectedBase =
    nodeSelect.value || (targets[0] && targets[0].base_url);
  nodeSelect.value = selectedBase;

  nodeSelect.addEventListener("change", () => {
    selectedBase = nodeSelect.value;
    resetUI();
  });

  refreshBtn.addEventListener("click", resetUI);

  showCoresCheckbox.addEventListener("change", () => {
    const visible = showCoresCheckbox.checked;
    Object.values(coreMini).forEach(c => {
      c.el.style.display = visible ? "block" : "none";
    });
  });

  // ------------------------------------------------------------
  // WEBSOCKET
  // ------------------------------------------------------------
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${protocol}://${location.host}/ws`);

  ws.onmessage = evt => {
    try {
      const msg = JSON.parse(evt.data);
      if (msg.type === "metrics") handleMetrics(msg.data);
    } catch (err) {
      console.error("WS parse error:", err);
    }
  };

  // ------------------------------------------------------------
  // INIT
  // ------------------------------------------------------------
  resetUI();
})();
