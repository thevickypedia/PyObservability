// app/static/app.js
(function () {
    // ------------------------------------------------------------
    // CONFIG
    // ------------------------------------------------------------
    const MAX_POINTS = 60;
    const targets = window.MONITOR_TARGETS || [];
    const DEFAULT_PAGE_SIZE = 10;
    const panelSpinners = {};

    // ------------------------------------------------------------
    // VISUAL SPINNERS
    // ------------------------------------------------------------
    function attachSpinners() {
        // panels (charts/tables)
        document.querySelectorAll(".panel").forEach(box => {
            const overlay = document.createElement("div");
            overlay.className = "loading-overlay";
            overlay.innerHTML = `<div class="spinner"></div>`;
            box.style.position = "relative";
            box.appendChild(overlay);
            panelSpinners[box.id || box.querySelector('table,canvas')?.id || Symbol()] = overlay;
        });

        // meta cards (system/static metrics)
        document.querySelectorAll(".meta-card").forEach(card => {
            const overlay = document.createElement("div");
            overlay.className = "loading-overlay";
            overlay.innerHTML = `<div class="spinner"></div>`;
            card.style.position = "relative";
            card.appendChild(overlay);
            panelSpinners[card.querySelector(".meta-value")?.id || Symbol()] = overlay;
        });
    }

    function showAllSpinners() {
        Object.keys(panelSpinners).forEach(id => showSpinner(id));
    }

    function hideSpinners() {
        document.querySelectorAll(".loading-overlay").forEach(x => {
            x.classList.add("hidden");
        });
    }

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

    const servicesTable = document.getElementById("services-table");
    const servicesTableBody = document.querySelector("#services-table tbody");
    const svcFilter = document.getElementById("svc-filter");
    const svcGetAll = document.getElementById("get-all-services");

    const processesTable = document.getElementById("processes-table");
    const processesTableBody = processesTable.querySelector("tbody");
    const procFilter = document.getElementById("proc-filter");

    const dockerTable = document.getElementById("docker-table");
    const dockerTableHead = dockerTable.querySelector("thead");
    const dockerTableBody = dockerTable.querySelector("tbody");

    const disksTable = document.getElementById("disks-table");
    const disksTableHead = disksTable.querySelector("thead");
    const disksTableBody = disksTable.querySelector("tbody");

    const pyudiskTable = document.getElementById("pyudisk-table");
    const pyudiskTableHead = pyudiskTable.querySelector("thead");
    const pyudiskTableBody = pyudiskTable.querySelector("tbody");

    const certsTable = document.getElementById("certificates-table");
    const certsTableHead = certsTable.querySelector("thead");
    const certsTableBody = certsTable.querySelector("tbody");

    const showCoresCheckbox = document.getElementById("show-cores");

    // ------------------------------------------------------------
    // PAGINATION HELPERS
    // ------------------------------------------------------------
    function createPaginatedTable(tableEl, headEl, bodyEl, pageSize = DEFAULT_PAGE_SIZE) {
        const info = document.createElement("div");
        info.className = "pagination-info";
        tableEl.insertAdjacentElement("beforebegin", info);

        const state = {
            data: [],
            page: 1,
            pageSize
        };

        const pagination = document.createElement("div");
        pagination.className = "pagination";
        tableEl.insertAdjacentElement("afterend", pagination);

        function render() {
            const rows = state.data;
            const pages = Math.ceil(rows.length / state.pageSize) || 1;
            state.page = Math.max(1, Math.min(state.page, pages));

            const start = (state.page - 1) * state.pageSize;
            const chunk = rows.slice(start, start + state.pageSize);

            info.textContent =
                `Showing ${rows.length ? start + 1 : 0} to ${rows.length ? Math.min(start + state.pageSize, rows.length) : 0} of ${rows.length} entries`;

            bodyEl.innerHTML = "";
            chunk.forEach(r => bodyEl.insertAdjacentHTML("beforeend", r));

            const fillerCount = Math.max(0, state.pageSize - chunk.length);
            const shouldPad = state.page > 1 && fillerCount > 0;
            if (shouldPad) {
                const colCount = state.columns?.length || headEl.querySelectorAll("th").length || 1;
                for (let i = 0; i < fillerCount; i++) {
                    const fillerRow = document.createElement("tr");
                    fillerRow.className = "placeholder-row";
                    for (let c = 0; c < colCount; c++) {
                        const cell = document.createElement("td");
                        cell.innerHTML = "&nbsp;";
                        fillerRow.appendChild(cell);
                    }
                    bodyEl.appendChild(fillerRow);
                }
            }
            renderPagination(pages);
        }

        function renderPagination(pages) {
            pagination.innerHTML = "";

            const makeBtn = (txt, cb, active = false, disabled = false) => {
                const b = document.createElement("button");
                b.textContent = txt;
                if (active) b.classList.add("active");
                if (disabled) {
                    b.disabled = true;
                    b.style.opacity = "0.5";
                    b.style.cursor = "default";
                }
                b.onclick = disabled ? null : cb;
                pagination.appendChild(b);
            };

            // --- Previous ---
            makeBtn("Previous", () => {
                state.page--;
                render();
            }, false, state.page === 1);

            const maxVisible = 5;

            if (pages <= maxVisible + 2) {
                // Show all
                for (let p = 1; p <= pages; p++) {
                    makeBtn(p, () => {
                        state.page = p;
                        render();
                    }, p === state.page);
                }
            } else {
                // Big list → use ellipsis
                const showLeft = 3;
                const showRight = 3;

                if (state.page <= showLeft) {
                    // First pages
                    for (let p = 1; p <= showLeft + 1; p++) {
                        makeBtn(p, () => {
                            state.page = p;
                            render();
                        }, p === state.page);
                    }
                    addEllipsis();
                    makeBtn(pages, () => {
                        state.page = pages;
                        render();
                    });
                } else if (state.page >= pages - showRight + 1) {
                    // Last pages
                    makeBtn(1, () => {
                        state.page = 1;
                        render();
                    });
                    addEllipsis();
                    for (let p = pages - showRight; p <= pages; p++) {
                        makeBtn(p, () => {
                            state.page = p;
                            render();
                        }, p === state.page);
                    }
                } else {
                    // Middle
                    makeBtn(1, () => {
                        state.page = 1;
                        render();
                    });
                    addEllipsis();
                    for (let p = state.page - 1; p <= state.page + 1; p++) {
                        makeBtn(p, () => {
                            state.page = p;
                            render();
                        }, p === state.page);
                    }
                    addEllipsis();
                    makeBtn(pages, () => {
                        state.page = pages;
                        render();
                    });
                }
            }

            // --- Next ---
            makeBtn("Next", () => {
                state.page++;
                render();
            }, false, state.page === pages);

            function addEllipsis() {
                const e = document.createElement("span");
                e.textContent = "…";
                e.style.padding = "4px 6px";
                pagination.appendChild(e);
            }
        }

        function setData(arr, columns) {
            headEl.innerHTML = "<tr>" + columns.map(c => `<th>${c}</th>`).join("") + "</tr>";
            state.dataRaw = arr.slice();
            state.columns = columns;
            // Sorting logic
            Array.from(headEl.querySelectorAll("th")).forEach((th, idx) => {
                th.style.cursor = "pointer";
                th.onclick = (e) => {
                    // Prevent sort if reset button was clicked
                    if (e.target.classList.contains("sort-reset")) return;
                    const col = columns[idx];
                    if (state.sortCol === col) {
                        state.sortAsc = !state.sortAsc;
                    } else {
                        state.sortCol = col;
                        state.sortAsc = true;
                    }
                    sortAndRender();
                };
            });

            function sortAndRender() {
                // Rebuild all headers with correct HTML
                headEl.querySelectorAll("th").forEach((th, idx) => {
                    const col = state.columns[idx];
                    if (state.sortCol === col) {
                        th.innerHTML = `${col} <span style="font-size:0.9em">${state.sortAsc ? "▲" : "▼"}</span>&nbsp;<span class="sort-reset" style="cursor:pointer;font-size:0.9em;color:#888;margin-left:8px;" title="Reset sort">⨯</span>`;
                        th.querySelector(".sort-reset").onclick = (e) => {
                            e.stopPropagation();
                            state.sortCol = null;
                            state.sortAsc = true;
                            state.dataRaw = arr.slice();
                            sortAndRender();
                        };
                    } else {
                        th.innerHTML = col;
                    }
                });
                if (state.sortCol) {
                    state.dataRaw.sort((a, b) => {
                        let va = a[state.sortCol], vb = b[state.sortCol];
                        let na = parseFloat(va), nb = parseFloat(vb);
                        if (!isNaN(na) && !isNaN(nb)) {
                            return state.sortAsc ? na - nb : nb - na;
                        }
                        va = (va ?? "").toString().toLowerCase();
                        vb = (vb ?? "").toString().toLowerCase();
                        if (va < vb) return state.sortAsc ? -1 : 1;
                        if (va > vb) return state.sortAsc ? 1 : -1;
                        return 0;
                    });
                }
                state.data = state.dataRaw.map(row =>
                    "<tr>" + state.columns.map(c => `<td>${row[c] ?? ""}</td>`).join("") + "</tr>"
                );
                render();
            }
            sortAndRender();
        }

        return {setData};
    }

    // Instances for each table
    const PAG_SERVICES = createPaginatedTable(
        servicesTable, servicesTable.querySelector("thead"), servicesTableBody, 5
    );
    const PAG_PROCESSES = createPaginatedTable(
        processesTable, processesTable.querySelector("thead"), processesTableBody
    );
    const PAG_DOCKER = createPaginatedTable(
        dockerTable, dockerTableHead, dockerTableBody
    );
    const PAG_DISKS = createPaginatedTable(
        disksTable, disksTableHead, disksTableBody
    );
    const PAG_PYUDISK = createPaginatedTable(
        pyudiskTable, pyudiskTableHead, pyudiskTableBody
    );
    const PAG_CERTS = createPaginatedTable(
        certsTable, certsTableHead, certsTableBody
    );

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
                animation: false, responsive: true, maintainAspectRatio: false,
                scales: {x: {display: false}, y: {beginAtZero: true, suggestedMax: 100}},
                plugins: {legend: {display: false}}
            }
        });
    }

    function makeCoreSparkline(ctx, coreName) {
        const EMPTY_LABELS = Array(MAX_POINTS).fill("");
        const EMPTY_DATA = Array(MAX_POINTS).fill(null);

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
                plugins: {legend: {display: false}},
                scales: {
                    x: {display: false},
                    y: {display: false, suggestedMax: 100}
                }
            }
        });
    }

    const cpuAvgChart = makeMainChart(cpuAvgCtx, "CPU Avg");
    const memChart = makeMainChart(memCtx, "Memory %");
    const loadChart = makeMainChart(loadCtx, "CPU Load");

    // Unified metrics: three parallel charts (memory, CPU, disk)
    const unifiedPanel = document.getElementById("unified-panel");
    const unifiedLegend = document.getElementById("unified-legend");
    const unifiedMemCtx = document.getElementById("unified-mem-chart").getContext("2d");
    const unifiedCpuCtx = document.getElementById("unified-cpu-chart").getContext("2d");
    const unifiedDiskCtx = document.getElementById("unified-disk-chart").getContext("2d");

    // Unified tables DOM references
    const unifiedServicesTable = document.getElementById("unified-services-table");
    const unifiedServicesHead = unifiedServicesTable?.querySelector("thead");
    const unifiedServicesBody = unifiedServicesTable?.querySelector("tbody");

    const unifiedProcessesTable = document.getElementById("unified-processes-table");
    const unifiedProcessesHead = unifiedProcessesTable?.querySelector("thead");
    const unifiedProcessesBody = unifiedProcessesTable?.querySelector("tbody");

    const unifiedDockerTable = document.getElementById("unified-docker-table");
    const unifiedDockerHead = unifiedDockerTable?.querySelector("thead");
    const unifiedDockerBody = unifiedDockerTable?.querySelector("tbody");

    const unifiedDisksTable = document.getElementById("unified-disks-table");
    const unifiedDisksHead = unifiedDisksTable?.querySelector("thead");
    const unifiedDisksBody = unifiedDisksTable?.querySelector("tbody");

    const unifiedPyudiskTable = document.getElementById("unified-pyudisk-table");
    const unifiedPyudiskHead = unifiedPyudiskTable?.querySelector("thead");
    const unifiedPyudiskBody = unifiedPyudiskTable?.querySelector("tbody");

    const unifiedCertsTable = document.getElementById("unified-certificates-table");
    const unifiedCertsHead = unifiedCertsTable?.querySelector("thead");
    const unifiedCertsBody = unifiedCertsTable?.querySelector("tbody");

    // Paginated unified tables
    const PAG_UNIFIED_SERVICES = unifiedServicesTable && createPaginatedTable(
        unifiedServicesTable, unifiedServicesHead, unifiedServicesBody
    );
    const PAG_UNIFIED_PROCESSES = unifiedProcessesTable && createPaginatedTable(
        unifiedProcessesTable, unifiedProcessesHead, unifiedProcessesBody
    );
    const PAG_UNIFIED_DOCKER = unifiedDockerTable && createPaginatedTable(
        unifiedDockerTable, unifiedDockerHead, unifiedDockerBody
    );
    const PAG_UNIFIED_DISKS = unifiedDisksTable && createPaginatedTable(
        unifiedDisksTable, unifiedDisksHead, unifiedDisksBody
    );
    const PAG_UNIFIED_PYUDISK = unifiedPyudiskTable && createPaginatedTable(
        unifiedPyudiskTable, unifiedPyudiskHead, unifiedPyudiskBody
    );
    const PAG_UNIFIED_CERTS = unifiedCertsTable && createPaginatedTable(
        unifiedCertsTable, unifiedCertsHead, unifiedCertsBody
    );

    let unifiedNodes = [];
    // TODO: Update colorPalette to use contrasting colors
    const colorPalette = ["#63b3ff", "#ff99c8", "#7dd3fc", "#fbbf24", "#a3e635", "#f87171", "#c084fc", "#38bdf8"];
    const nodeColor = {};
    const unifiedCharts = {memory: null, cpu: null, disk: null};

    function normalizeNodes(nodes) {
        return nodes
            .filter(node => node.base_url && node.base_url !== "*")
            .sort((a, b) => (a.name || a.base_url).localeCompare(b.name || b.base_url));
    }

    function assignColors(nodes) {
        nodes.forEach((node, idx) => {
            nodeColor[node.base_url] = colorPalette[idx % colorPalette.length];
        });
    }

    function renderLegend(nodes) {
        unifiedLegend.innerHTML = "";
        nodes.forEach(node => {
            const item = document.createElement("div");
            item.className = "unified-legend-item";
            item.innerHTML = `<span class="legend-dot" style="background:${nodeColor[node.base_url]}"></span>${node.name || node.base_url}`;
            unifiedLegend.appendChild(item);
        });
    }

    function makeUnifiedChart(ctx, nodes) {
        return new Chart(ctx, {
            type: "line",
            data: {
                labels: Array(MAX_POINTS).fill(""),
                datasets: nodes.map(node => ({
                    label: node.name || node.base_url,
                    meta: {base_url: node.base_url},
                    data: Array(MAX_POINTS).fill(null),
                    borderColor: nodeColor[node.base_url],
                    backgroundColor: `${nodeColor[node.base_url]}33`,
                    borderWidth: 2,
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0,
                }))
            },
            options: {
                animation: false,
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {display: false},
                    y: {beginAtZero: true, suggestedMax: 100}
                },
                plugins: {legend: {display: false}}
            }
        });
    }

    function setUnifiedMode(enabled) {
        document.body.classList.toggle("unified-mode", enabled);
        if (!enabled) {
            unifiedPanel.classList.add("hidden");
        }
    }

    function ensureUnifiedChart(metrics) {
        const nodes = normalizeNodes(metrics);
        if (!nodes.length) return false;
        const changed =
            nodes.length !== unifiedNodes.length ||
            nodes.some((node, idx) => unifiedNodes[idx]?.base_url !== node.base_url);

        if (changed) {
            // Destroy any existing unified charts
            Object.keys(unifiedCharts).forEach(key => {
                if (unifiedCharts[key]) {
                    unifiedCharts[key].destroy();
                    unifiedCharts[key] = null;
                }
            });
            assignColors(nodes);
            unifiedCharts.memory = makeUnifiedChart(unifiedMemCtx, nodes);
            unifiedCharts.cpu = makeUnifiedChart(unifiedCpuCtx, nodes);
            unifiedCharts.disk = makeUnifiedChart(unifiedDiskCtx, nodes);
            unifiedNodes = nodes;
        }

        unifiedPanel.classList.remove("hidden");
        renderLegend(nodes);
        return true;
    }

    function sampleForMetric(host, metric) {
        if (!host.metrics) return null;
        if (metric === "memory") return host.metrics.memory_info?.percent ?? null;
        if (metric === "cpu") {
            const values = (host.metrics.cpu_usage || [])
                .map(v => Number(v))
                .filter(Number.isFinite);
            if (!values.length) return null;
            return values.reduce((a, b) => a + b, 0) / values.length;
        }
        if (metric === "disk") {
            const m = host.metrics;
            if (m.disk_info && m.disk_info[0]) {
                const m = host.metrics;
                const agg = aggregateDiskInfo(m.disk_info);
                return agg.percent;
            }
            return host.metrics.disk_info?.[0]?.percent ?? null;
        }
        return null;
    }

    function updateUnified(metrics) {
        const ts = new Date().toLocaleTimeString();
        const metricKeys = ["memory", "cpu", "disk"];
        metricKeys.forEach(metric => {
            const chart = unifiedCharts[metric];
            if (!chart) return;

            chart.data.labels.push(ts);
            if (chart.data.labels.length > MAX_POINTS) {
                chart.data.labels.shift();
            }

            chart.data.datasets.forEach(ds => {
                const host = metrics.find(h => h.base_url === ds.meta.base_url);
                const value = host ? sampleForMetric(host, metric) : null;
                ds.data.push(value);
                if (ds.data.length > MAX_POINTS) ds.data.shift();
            });

            chart.update("none");
        });

        // --- Unified tables aggregation ---
        // Helper to get display name for node
        const getNodeLabel = (host) => host.name || host.base_url || "";

        // Services
        if (PAG_UNIFIED_SERVICES) {
            const svcRows = [];
            metrics.forEach(host => {
                if (!host.metrics) return;
                const m = host.metrics;
                const label = getNodeLabel(host);
                const services = (m.service_stats || m.services || []).filter(s =>
                    (s.pname || s.Name || "").toLowerCase().includes(
                        svcFilter.value.trim().toLowerCase()
                    )
                );
                services.forEach(s => {
                    svcRows.push({
                        Node: label,
                        PID: s.PID ?? s.pid ?? "",
                        Name: s.pname ?? s.Name ?? s.name ?? "",
                        Status: s.Status ?? s.active ?? s.status ?? s.Active ?? "4",
                        CPU: objectToString(s.CPU, s.cpu),
                        Memory: objectToString(s.Memory, s.memory),
                        Threads: s.Threads ?? s.threads ?? "4",
                        "Open Files": s["Open Files"] ?? s.open_files ?? "4"
                    });
                });
            });
            const svcCols = ["Node", "PID", "Name", "Status", "CPU", "Memory", "Threads", "Open Files"];
            PAG_UNIFIED_SERVICES.setData(svcRows, svcCols);
        }

        // Processes
        if (PAG_UNIFIED_PROCESSES) {
            const procRows = [];
            const procColsSet = new Set(["Node", "PID", "Name", "Status", "CPU", "Memory", "Uptime", "Threads", "Open Files"]);
            metrics.forEach(host => {
                if (!host.metrics) return;
                const m = host.metrics;
                const label = getNodeLabel(host);
                const processes = (m.process_stats || []).filter(p =>
                    (p.Name || "").toLowerCase().includes(
                        procFilter.value.trim().toLowerCase()
                    )
                );
                processes.forEach(p => {
                    const row = {Node: label};
                    Object.entries(p).forEach(([k, v]) => {
                        procColsSet.add(k);
                        row[k] = v;
                    });
                    procRows.push(row);
                });
            });
            const procCols = Array.from(procColsSet);
            PAG_UNIFIED_PROCESSES.setData(procRows, procCols);
        }

        // Docker
        if (PAG_UNIFIED_DOCKER) {
            const dockerRows = [];
            const dockerColsSet = new Set(["Node"]);
            metrics.forEach(host => {
                if (!host.metrics || !Array.isArray(host.metrics.docker_stats)) return;
                const label = getNodeLabel(host);
                host.metrics.docker_stats.forEach(s => {
                    const row = {Node: label};
                    Object.entries(s).forEach(([k, v]) => {
                        dockerColsSet.add(k);
                        row[k] = v;
                    });
                    dockerRows.push(row);
                });
            });
            const dockerCols = Array.from(dockerColsSet);
            PAG_UNIFIED_DOCKER.setData(dockerRows, dockerCols);
        }

        // Disks
        if (PAG_UNIFIED_DISKS) {
            const diskRows = [];
            const diskColsSet = new Set(["Node"]);
            metrics.forEach(host => {
                if (!host.metrics || !Array.isArray(host.metrics.disks_info)) return;
                const label = getNodeLabel(host);
                host.metrics.disks_info.forEach(d => {
                    const row = {Node: label};
                    Object.entries(d).forEach(([k, v]) => {
                        if (k === "Node") return;
                        diskColsSet.add(k);
                        row[k] = v;
                    });
                    diskRows.push(row);
                });
            });
            const diskCols = Array.from(diskColsSet);
            PAG_UNIFIED_DISKS.setData(diskRows, diskCols);
        }

        // PyUdisk
        if (PAG_UNIFIED_PYUDISK) {
            const pyuRows = [];
            const pyuColsSet = new Set(["Node"]);
            metrics.forEach(host => {
                if (!host.metrics || !Array.isArray(host.metrics.pyudisk_stats)) return;
                const label = getNodeLabel(host);
                host.metrics.pyudisk_stats.forEach(pyu => {
                    const row = {Node: label};
                    Object.entries(pyu).forEach(([k, v]) => {
                        if (k === "Mountpoint") return;
                        pyuColsSet.add(k);
                        row[k] = v;
                    });
                    pyuRows.push(row);
                });
            });
            const pyuCols = Array.from(pyuColsSet);
            PAG_UNIFIED_PYUDISK.setData(pyuRows, pyuCols);
        }

        // Certificates
        if (PAG_UNIFIED_CERTS) {
            const certRows = [];
            const certColsSet = new Set(["Node"]);
            metrics.forEach(host => {
                if (!host.metrics || !Array.isArray(host.metrics.certificates)) return;
                const label = getNodeLabel(host);
                host.metrics.certificates.forEach(c => {
                    const row = {Node: label};
                    Object.entries(c).forEach(([k, v]) => {
                        certColsSet.add(k);
                        row[k] = v;
                    });
                    certRows.push(row);
                });
            });
            const certCols = Array.from(certColsSet);
            PAG_UNIFIED_CERTS.setData(certRows, certCols);
        }
    }

    // ------------------------------------------------------------
    // CORE CHARTS
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
        wrapper.style.display = showCoresCheckbox.checked ? "block" : "none";
        coresGrid.appendChild(wrapper);

        const canvas = wrapper.querySelector("canvas");
        const valEl = wrapper.querySelector(".value");
        const chart = makeCoreSparkline(canvas.getContext("2d"), coreName);

        coreMini[coreName] = {chart, el: wrapper, valEl};
        return coreMini[coreName];
    }

    function getCoreChart(coreName) {
        return coreMini[coreName] || createCoreChart(coreName);
    }

    function pruneOldCores(keep) {
        for (const name of Object.keys(coreMini)) {
            if (!keep.includes(name)) {
                try {
                    coreMini[name].chart.destroy();
                } catch {
                }
                coreMini[name].el.remove();
                delete coreMini[name];
            }
        }
    }

    // ------------------------------------------------------------
    // RESET UI
    // ------------------------------------------------------------
    function resetTables() {
        // Clear all table data immediately
        PAG_SERVICES.setData([], []);
        PAG_PROCESSES.setData([], []);
        PAG_DOCKER.setData([], []);
        PAG_DISKS.setData([], []);
        PAG_PYUDISK.setData([], []);
        PAG_CERTS.setData([], []);
        if (PAG_UNIFIED_SERVICES) PAG_UNIFIED_SERVICES.setData([], []);
        if (PAG_UNIFIED_PROCESSES) PAG_UNIFIED_PROCESSES.setData([], []);
        if (PAG_UNIFIED_DOCKER) PAG_UNIFIED_DOCKER.setData([], []);
        if (PAG_UNIFIED_DISKS) PAG_UNIFIED_DISKS.setData([], []);
        if (PAG_UNIFIED_PYUDISK) PAG_UNIFIED_PYUDISK.setData([], []);
        if (PAG_UNIFIED_CERTS) PAG_UNIFIED_CERTS.setData([], []);
    }

    function resetUI() {
        firstMessage = true;
        hideSpinners();
        const EMPTY_DATA = Array(MAX_POINTS).fill(null);
        const EMPTY_LABELS = Array(MAX_POINTS).fill("");

        const resetChart = chart => {
            chart.data.labels = [...EMPTY_LABELS];
            chart.data.datasets[0].data = [...EMPTY_DATA];
            chart.update();
        };

        resetChart(cpuAvgChart);
        resetChart(memChart);
        resetChart(loadChart);

        // Reset unified charts as well
        Object.keys(unifiedCharts).forEach(key => {
            const chart = unifiedCharts[key];
            if (chart) {
                try {
                    chart.destroy();
                } catch {}
                unifiedCharts[key] = null;
            }
        });
        unifiedNodes = [];
        unifiedPanel.classList.add("hidden");

        for (const name of Object.keys(coreMini)) {
            try {
                coreMini[name].chart.destroy();
            } catch {}
            coreMini[name].el.remove();
            delete coreMini[name];
        }

        systemEl.textContent = "-";
        ipEl.textContent = "—";
        processorEl.textContent = "—";
        memEl.textContent = "—";
        diskEl.textContent = "—";
        loadEl.textContent = "—";
    }

    // ------------------------------------------------------------
    // MISC HELPERS
    // ------------------------------------------------------------
    function aggregateDiskInfo(diskInfo) {
        let totalDisk = 0;
        let usedDisk = 0;
        let freeDisk = 0;
        diskInfo.forEach(d => {
            totalDisk += num(d.total || 0);
            usedDisk += num(d.used || 0);
            freeDisk += num(d.free || 0);
        });
        let percentDisk = totalDisk > 0 ? (usedDisk / totalDisk) * 100 : 0.0;
        return {"total": totalDisk, "used": usedDisk, "free": freeDisk, "percent": percentDisk};
    }

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

    const round2 = x => Number(x).toFixed(2);
    const formatBytes = x => {
        if (x == null) return "—";
        const u = ["B", "KB", "MB", "GB", "TB"];
        let i = 0, n = Number(x);
        while (n > 1024 && i < u.length - 1) {
            n /= 1024;
            i++;
        }
        return n.toFixed(2) + " " + u[i];
    };
    const objectToString = (...vals) => {
        for (const v of vals) {
            if (v && typeof v === "object")
                return Object.entries(v).map(([a, b]) => `${a}: ${b}`).join("<br>");
            if (v != null) return v;
        }
        return "—";
    };

    function showSpinner(panelOrTableId) {
        const overlay = panelSpinners[panelOrTableId];
        if (overlay) overlay.classList.remove("hidden");
    }

    function hideSpinner(panelOrTableId) {
        const overlay = panelSpinners[panelOrTableId];
        if (overlay) overlay.classList.add("hidden");
    }

    // ------------------------------------------------------------
    // HANDLE METRICS
    // ------------------------------------------------------------
    let firstMessage = true;

    function handleMetrics(list) {
        if (firstMessage) {
            hideSpinners();
            firstMessage = false;
        }

        const now = new Date().toLocaleTimeString();

        if (selectedBase === "*") {
            if (ensureUnifiedChart(list)) {
                setUnifiedMode(true);
                updateUnified(list);
            }
            return;
        }

        setUnifiedMode(false);

        for (const host of list) {
            if (host.base_url !== selectedBase) continue;
            const m = host.metrics || {};

            // ------------ Static fields ------------
            systemEl.textContent =
                `Node: ${m.node || "-"}\n` +
                `OS: ${m.system || "-"}\n` +
                `Architecture: ${m.architecture || "-"}\n\n` +
                `CPU Cores: ${m.cores || "-"}\n` +
                `Up Time: ${m.uptime || "-"}\n`;

            if (m.ip_info)
                ipEl.textContent =
                    `Private: ${m.ip_info.private || "-"}\n\n` +
                    `Public: ${m.ip_info.public || "-"}`;

            processorEl.textContent =
                `CPU: ${m.cpu_name || "-"}\n\n` +
                `GPU: ${m.gpu_name || "-"}`;

            if (m.disk_info && m.disk_info[0]) {
                const agg = aggregateDiskInfo(m.disk_info);
                diskEl.textContent =
                    `Total: ${formatBytes(agg.total)}\n` +
                    `Used: ${formatBytes(agg.used)}\n` +
                    `Free: ${formatBytes(agg.free)}\n` +
                    `Percent: ${round2(agg.percent)}%`;
            }

            if (m.memory_info) {
                memEl.textContent =
                    `Total: ${formatBytes(m.memory_info.total)}\n` +
                    `Used: ${formatBytes(m.memory_info.used)}\n` +
                    `Free: ${formatBytes(m.memory_info.free)}\n` +
                    `Percent: ${round2(m.memory_info.percent)}%`;
                pushPoint(memChart, num(m.memory_info.percent));
            }

            // ------------ CPU ------------
            let avg = null;
            if (m.cpu_usage) {
                const values = m.cpu_usage.map(num);
                avg = values.reduce((a, b) => a + (b || 0), 0) / values.length;
                pruneOldCores(values.map((_, i) => "cpu" + (i + 1)));

                values.forEach((v, i) => {
                    const core = getCoreChart("cpu" + (i + 1));

                    core.chart.data.labels.push(now);
                    core.chart.data.datasets[0].data.push(v || 0);
                    if (core.chart.data.labels.length > MAX_POINTS) {
                        core.chart.data.labels.shift();
                        core.chart.data.datasets[0].data.shift();
                    }
                    core.chart.update({lazy: true});
                    core.valEl.textContent = `${(v || 0).toFixed(1)}%`;
                });
            }
            if (avg != null) pushPoint(cpuAvgChart, avg);

            // ------------ LOAD ------------
            if (m.load_averages) {
                const la = m.load_averages;
                loadEl.textContent =
                    `${round2(la.m1)} / ${round2(la.m5)} / ${round2(la.m15)}`;
                pushPoint(loadChart, num(la.m1));
            }

            // ------------ SERVICES (paginated) ------------
            const services = (m.service_stats || m.services || []).filter(s =>
                (s.pname || s.Name || "").toLowerCase().includes(
                    svcFilter.value.trim().toLowerCase()
                )
            );
            if (services.length) {
                const columns = ["PID", "Name", "Status", "CPU", "Memory", "Threads", "Open Files"];
                const cleaned = services.map(s => ({
                    PID: s.PID ?? s.pid ?? "",
                    Name: s.pname ?? s.Name ?? s.name ?? "",
                    Status: s.Status ?? s.active ?? s.status ?? s.Active ?? "—",
                    CPU: objectToString(s.CPU, s.cpu),
                    Memory: objectToString(s.Memory, s.memory),
                    Threads: s.Threads ?? s.threads ?? "—",
                    "Open Files": s["Open Files"] ?? s.open_files ?? "—"
                }));
                PAG_SERVICES.setData(cleaned, columns);
                hideSpinner("services-table");
            }

            // ------------ PROCESSES (paginated) ------------
            const processes = (m.process_stats || []).filter(p =>
                (p.Name || "").toLowerCase().includes(
                    procFilter.value.trim().toLowerCase()
                )
            );
            if (processes.length) {
                const columns = ["PID", "Name", "Status", "CPU", "Memory", "Uptime", "Threads", "Open Files"];
                PAG_PROCESSES.setData(processes, columns);
                hideSpinner("processes-table");
            }

            // ------------ DOCKER, DISKS, PYUDISK, CERTIFICATES ------------
            if (m.docker_stats) {
                const cols = Object.keys(m.docker_stats[0] || {});
                PAG_DOCKER.setData(m.docker_stats, cols);
                hideSpinner("docker-table");
            }

            if (m.disks_info) {
                const cols = Object.keys(m.disks_info[0] || {});
                PAG_DISKS.setData(m.disks_info, cols);
                hideSpinner("disks-table");
            }

            if (m.pyudisk_stats) {
                const cols = Object.keys(m.pyudisk_stats[0] || {});
                PAG_PYUDISK.setData(m.pyudisk_stats, cols);
                hideSpinner("pyudisk-table");
            }

            if (m.certificates) {
                const cols = Object.keys(m.certificates[0] || {});
                PAG_CERTS.setData(m.certificates, cols);
                hideSpinner("certificates-table");
            }
        }

        // When not in unified ("*") mode, ensure unified panel is hidden and charts cleared
        unifiedPanel.classList.add("hidden");
        unifiedNodes = [];
        Object.keys(unifiedCharts).forEach(key => {
            if (unifiedCharts[key]) {
                unifiedCharts[key].destroy();
                unifiedCharts[key] = null;
            }
        });
    }

    // ------------------------------------------------------------
    // EVENT BINDINGS
    // ------------------------------------------------------------
    targets.push({
        base_url: "*",
        name: "*"
    });
    targets.forEach(t => {
        const opt = document.createElement("option");
        opt.value = t.base_url;
        opt.textContent = t.name || t.base_url;
        nodeSelect.appendChild(opt);
    });

    let selectedBase = nodeSelect.value || (targets[0] && targets[0].base_url);
    nodeSelect.value = selectedBase;

    nodeSelect.addEventListener("change", () => {
        selectedBase = nodeSelect.value;
        resetUI();
        resetTables();
        showAllSpinners();
        if (selectedBase !== "*") unifiedPanel.classList.add("hidden");
        ws.send(JSON.stringify({type: "select_target", base_url: selectedBase}));
    });

    svcGetAll.addEventListener("change", () => {
        ws.send(JSON.stringify({type: "update_flags", all_services: svcGetAll.checked}));
    })

    refreshBtn.addEventListener("click", resetUI);

    showCoresCheckbox.addEventListener("change", () => {
        const visible = showCoresCheckbox.checked;
        Object.values(coreMini).forEach(c => c.el.style.display = visible ? "block" : "none");
    });

    // ------------------------------------------------------------
    // WEBSOCKET
    // ------------------------------------------------------------
    const protocol = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${protocol}://${location.host}/ws`);

    ws.onopen = () => {
        ws.send(JSON.stringify({type: "select_target", base_url: selectedBase}));
    };

    ws.onmessage = evt => {
        try {
            const msg = JSON.parse(evt.data);
            if (msg.type === "metrics") handleMetrics(msg.data);
            if (msg.type === "error") alert(msg.message);
        } catch (err) {
            console.error("WS parse error:", err);
        }
    };

    // ------------------------------------------------------------
    // INIT
    // ------------------------------------------------------------
    attachSpinners();
    resetUI();           // reset UI, keep spinners visible
    showAllSpinners();   // show spinners until first metrics arrive
})();
