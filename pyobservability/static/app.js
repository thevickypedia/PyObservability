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

  const systemEl = document.getElementById("system");
  const ipEl = document.getElementById("ip-info");
  const processorEl = document.getElementById("processor");

  const memEl = document.getElementById("memory");
  const diskEl = document.getElementById("disk");
  const loadEl = document.getElementById("cpuload");

  const cpuAvgCtx = document.getElementById("cpu-avg-chart").getContext("2d");
  const memCtx = document.getElementById("mem-chart").getContext("2d");
  const loadCtx = document.getElementById("load-chart").getContext("2d");

  const coresGrid = document.getElementById("cores-grid");

  const servicesTableBody = document.querySelector("#services-table tbody");
  const svcFilter = document.getElementById("svc-filter");

  const processesTableBody = document.querySelector("#processes-table tbody");
  const procFilter = document.getElementById("proc-filter");

  const dockerTable = document.getElementById("docker-table");
  const dockerTableHead = dockerTable.querySelector("thead");
  const dockerTableBody = dockerTable.querySelector("tbody");

  const disksTable = document.getElementById("disks-table");
  const disksTableHead = disksTable.querySelector("thead")
  const disksTableBody = disksTable.querySelector("tbody");

  const pyudiskTable = document.getElementById("pyudisk-table")
  const pyudiskTableHead = pyudiskTable.querySelector("thead")
  const pyudiskTableBody = pyudiskTable.querySelector("tbody")

  const certsTable = document.getElementById("certificates-table")
  const certsTableHead = certsTable.querySelector("thead");
  const certsTableBody = certsTable.querySelector("tbody");

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
    systemEl.textContent = "-";
    ipEl.textContent = "—";
    processorEl.textContent = "—";
    memEl.textContent = "—";
    diskEl.textContent = "—";
    loadEl.textContent = "—";

    servicesTableBody.innerHTML = "";
    processesTableBody.innerHTML = "";

    dockerTableHead.innerHTML = "";
    dockerTableBody.innerHTML = "";

    disksTableHead.innerHTML = "";
    disksTableBody.innerHTML = "";

    pyudiskTableHead.innerHTML = "";
    pyudiskTableBody.innerHTML = "";

    certsTableHead.innerHTML = "";
    certsTableBody.innerHTML = "";
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

  function round2(x) {
    const n = Number(x);
    return Number.isFinite(n) ? n.toFixed(2) : "—";
  }

  function formatBytes(x) {
    if (x == null) return "—";
    const units = ["B","KB","MB","GB","TB"];
    let i = 0;
    let n = Number(x);
    while (n > 1024 && i < units.length-1) {
      n /= 1024;
      i++;
    }
    return n.toFixed(2) + " " + units[i];
  }

  function tableConstructor(dataList, tableHead, tableBody) {
    tableHead.innerHTML = "";
    tableBody.innerHTML = "";

    if (!Array.isArray(dataList) || dataList.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="10">NO DATA</td></tr>`;
    } else {
      const columns = Object.keys(dataList[0]);
      tableHead.innerHTML =
        "<tr>" + columns.map(c => `<th>${c}</th>`).join("") + "</tr>";
      dataList.forEach(c => {
        const row = "<tr>" +
          columns.map(col => `<td>${c[col] ?? ""}</td>`).join("") +
          "</tr>";
        tableBody.insertAdjacentHTML("beforeend", row);
      });
    }
  }

  function objectToString(...vals) {
    for (const v of vals) {
      if (v !== undefined && v !== null) {
        if (typeof v === "object") {
          return Object.entries(v)
            .map(([k, val]) => `${k}: ${val}`)
            .join("<br>");
        }
        return String(v);
      }
    }
    return "—";
  }

  // ------------------------------------------------------------
  // METRICS HANDLER
  // ------------------------------------------------------------
  function handleMetrics(list) {
    const now = new Date().toLocaleTimeString();

    for (const host of list) {
      if (host.base_url !== selectedBase) continue;
      const m = host.metrics || {};

      // ------------------- System -------------------
      systemEl.textContent =
        `Node: ${m.node || "-"}\n` +
        `OS: ${m.system || "-"}\n` +
        `Architecture: ${m.architecture || "-"}\n\n` +
        `CPU Cores: ${m.cores || "-"}\n` +
        `Up Time: ${m.uptime || "-"}\n`;

      // ------------------- IP -------------------
      if (m.ip_info) {
        ipEl.textContent =
          `Private: ${m.ip_info.private || "-"}\n\n` +
          `Public: ${m.ip_info.public || "-"}`;
      } else {
        ipEl.textContent = "-";
      }

      // ------------------- CPU / GPU -------------------
      processorEl.textContent =
        `CPU: ${m.cpu_name || "-"}\n\n` +
        `GPU: ${m.gpu_name || "-"}`;

      // ------------------- DISKS (OLD “disk” card) -------------------
      if (Array.isArray(m.disk_info) && m.disk_info.length > 0) {
        const d = m.disk_info[0];
        diskEl.textContent =
          `Total: ${formatBytes(d.total)}\n` +
          `Used: ${formatBytes(d.used)}\n` +
          `Free: ${formatBytes(d.free)}`;
      } else if (m.disk) {
        diskEl.textContent =
          `Total: ${m.disk.total}\nUsed: ${m.disk.used}\nFree: ${m.disk.free}`;
      } else {
        diskEl.textContent = "NO DATA";
      }

      // ------------------- MEMORY -------------------
      if (m.memory_info) {
        const total = formatBytes(m.memory_info.total);
        const used  = formatBytes(m.memory_info.used);
        const percent = round2(m.memory_info.percent);

        memEl.textContent = `Total: ${total}\nUsed: ${used}\nPercent: ${percent}%`;
        pushPoint(memChart, num(m.memory_info.percent));

      } else if (m.memory) {
        // fallback to old
        const used = m.memory.ram_used || "";
        const percent = m.memory.ram_usage ?? m.memory.percent ?? "—";
        const totalMem = m.memory.ram_total ?? m.memory.total ?? "—";
        memEl.textContent = `Total: ${totalMem}\nUsed: ${used}\nPercent: ${percent}%`;
        pushPoint(memChart, num(percent));
      } else {
        memEl.textContent = "NO DATA";
      }

      // ------------------- CPU (NEW — cpu_usage[]) -------------------
      let avg = null;

      if (Array.isArray(m.cpu_usage)) {
        const values = m.cpu_usage.map(num);
        avg = values.reduce((a, b) => a + (b ?? 0), 0) / values.length;

        pruneOldCores(values.map((_, i) => "cpu" + (i + 1)));

        values.forEach((v, i) => {
          const coreName = "cpu" + (i + 1);
          const c = getCoreChart(coreName);

          c.chart.data.labels.push(now);
          c.chart.data.datasets[0].data.push(v ?? 0);

          if (c.chart.data.labels.length > MAX_POINTS) {
            c.chart.data.labels.shift();
            c.chart.data.datasets[0].data.shift();
          }

          c.chart.update("none");
          c.valEl.textContent = `${(v ?? 0).toFixed(1)}%`;
        });

      } else if (m.cpu) {
        // fallback to old
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
      }

      if (avg != null) pushPoint(cpuAvgChart, avg);

      // ------------------- CPU LOAD -------------------
      if (m.load_averages) {
        const la = m.load_averages;
        loadEl.textContent =
          `${round2(la.m1)} / ${round2(la.m5)} / ${round2(la.m15)}`;
        pushPoint(loadChart, num(la.m1));
      } else if (m.cpu_load) {
        const load = m.cpu_load.detail || m.cpu_load;
        const m1 = load.m1 ?? load[0];
        const m5 = load.m5 ?? load[1];
        const m15 = load.m15 ?? load[2];
        loadEl.textContent = `${round2(m1)} / ${round2(m5)} / ${round2(m15)}`;
        pushPoint(loadChart, num(m1));
      } else {
        loadEl.textContent = "NO DATA";
      }

      // ------------------- SERVICES (NEW → OLD) -------------------
      const services = m.service_stats || m.services || [];
      servicesTableBody.innerHTML = "";
      if (Array.isArray(services)) {
        const filter = svcFilter.value.trim().toLowerCase();
        for (const s of services) {
          const name = s.pname || s.Name || "";

          if (filter && !name.toLowerCase().includes(filter)) continue;

          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${s.PID ?? ""}</td>
            <td>${name}</td>
            <td>${s.Status ?? s.status ?? "—"}</td>
            <td>${objectToString(s.CPU, s.cpu)}</td>
            <td>${objectToString(s.Memory, s.memory)}</td>
            <td>${s.Threads ?? s.threads ?? "—"}</td>
            <td>${s["Open Files"] ?? s.open_files ?? "—"}</td>
          `;
          servicesTableBody.appendChild(tr);
        }
      }

      // ------------------- PROCESSES (NEW → OLD) -------------------
      const processes = m.process_stats || [];
      processesTableBody.innerHTML = "";
      if (Array.isArray(processes)) {
        const filter = procFilter.value.trim().toLowerCase();
        for (const p of processes) {
          const name = p.Name || "";

          if (filter && !name.toLowerCase().includes(filter)) continue;

          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${p.PID ?? ""}</td>
            <td>${name}</td>
            <td>${p.Status ?? p.status ?? "—"}</td>
            <td>${p.CPU ?? p.cpu ?? "—"}</td>
            <td>${p.Memory ?? p.memory ?? "—"}</td>
            <td>${p.Uptime ?? p.uptime ?? "—"}</td>
            <td>${p.Threads ?? p.threads ?? "—"}</td>
            <td>${p["Open Files"] ?? p.open_files ?? "—"}</td>
          `;
          processesTableBody.appendChild(tr);
        }
      }

      // ------------------- DOCKER -------------------
      const dockerList = m.docker_stats || [];
      tableConstructor(dockerList, dockerTableHead, dockerTableBody);

      // ------------------- DISKS (Tables) -------------------
      // TOOD: Remove disk list when pyudisk is available
      const diskList = m.disks_info || [];
      tableConstructor(diskList, disksTableHead, disksTableBody);

      // ------------------- PyUdisk (Tables) -------------------
      const pyudiskList = m.pyudisk_stats || [];
      tableConstructor(pyudiskList, pyudiskTableHead, pyudiskTableBody);

      // ------------------- CERTIFICATES -------------------
      const certsList = m.certificates || [];
      tableConstructor(certsList, certsTableHead, certsTableBody);
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
    ws.send(JSON.stringify({ type: "select_target", base_url: selectedBase }));
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

  ws.onopen = () => {
    ws.send(JSON.stringify({ type: "select_target", base_url: selectedBase }));
  };

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
