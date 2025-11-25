// app/static/app.js
(function () {
  // --- config
  const MAX_POINTS = 60;
  const targets = window.MONITOR_TARGETS || [];

  // --- DOM refs
  const nodeSelect = document.getElementById('node-select');
  const refreshBtn = document.getElementById('refresh-btn');
  const ipEl = document.getElementById('ip');
  const gpuEl = document.getElementById('gpu');
  const memEl = document.getElementById('memory');
  const diskEl = document.getElementById('disk');
  const loadEl = document.getElementById('cpuload');

  const cpuAvgCtx = document.getElementById('cpu-avg-chart').getContext('2d');
  const memCtx = document.getElementById('mem-chart').getContext('2d');
  const loadCtx = document.getElementById('load-chart').getContext('2d');
  const coresGrid = document.getElementById('cores-grid');

  const servicesTableBody = document.querySelector('#services-table tbody');
  const svcFilter = document.getElementById('svc-filter');
  const dockerStatsEl = document.getElementById('docker-stats');
  const containersList = document.getElementById('containers-list');
  const disksTableBody = document.querySelector('#disks-table tbody');
  const certsEl = document.getElementById('certificates');
  const showCoresCheckbox = document.getElementById('show-cores');

  // --- helper charts
  function makeLine(ctx, label) {
    return new Chart(ctx, {
      type: 'line',
      data: { labels: [], datasets: [{ label, data: [], fill: true, cubicInterpolationMode: 'monotone', tension: 0.2, pointRadius: 0 }] },
      options: { animation: false, responsive: true, maintainAspectRatio: false, scales: { x: { display: false }, y: { beginAtZero: true } }, plugins: { legend: { display: false } } }
    });
  }

  const cpuAvgChart = makeLine(cpuAvgCtx, 'CPU % (avg)');
  const memChart = makeLine(memCtx, 'Memory %');
  const loadChart = makeLine(loadCtx, 'CPU Load');

  // per-core mini charts map: coreName -> {chart, el}
  const coreMini = {};

  function ensureCoreChart(name) {
    if (coreMini[name]) return coreMini[name];
    const wrapper = document.createElement('div');
    wrapper.className = 'core-mini';
    wrapper.innerHTML = `<div class="label">${name}</div><canvas width="120" height="40"></canvas><div class="value">—</div>`;
    coresGrid.appendChild(wrapper);
    const canvas = wrapper.querySelector('canvas');
    const valEl = wrapper.querySelector('.value');
    const c = new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: { labels: [], datasets: [{ label: name, data: [], fill: false, pointRadius: 0, tension: 0.2 }] },
      options: { animation: false, responsive: true, maintainAspectRatio: false, scales: { x: { display: false }, y: { display: false } }, plugins: { legend: { display: false } } }
    });
    coreMini[name] = { chart: c, el: wrapper, valEl };
    return coreMini[name];
  }

  // --- fill node dropdown
  targets.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t.base_url;
    opt.textContent = t.name || t.base_url;
    nodeSelect.appendChild(opt);
  });

  let selectedBase = nodeSelect.value || (targets[0] && targets[0].base_url);
  nodeSelect.value = selectedBase;

  nodeSelect.addEventListener('change', () => {
    selectedBase = nodeSelect.value;
    resetUI();
  });

  refreshBtn.addEventListener('click', () => {
    // ephemeral: request a reload by toggling show-cores to cause repaint, or we can reload page
    resetUI();
  });

  function resetUI() {
    // clear charts and tables
    cpuAvgChart.data.labels = []; cpuAvgChart.data.datasets[0].data = [];
    memChart.data.labels = []; memChart.data.datasets[0].data = [];
    loadChart.data.labels = []; loadChart.data.datasets[0].data = [];
    cpuAvgChart.update(); memChart.update(); loadChart.update();

    Object.values(coreMini).forEach(o => { o.chart.data.labels = []; o.chart.data.datasets[0].data = []; o.chart.update(); o.valEl.textContent = '—'; });
    servicesTableBody.innerHTML = '';
    dockerStatsEl.textContent = '—';
    containersList.innerHTML = '';
    disksTableBody.innerHTML = '';
    certsEl.textContent = '—';
    ipEl.textContent = '—';
    gpuEl.textContent = '—';
    memEl.textContent = '—';
    diskEl.textContent = '—';
    loadEl.textContent = '—';
  }

  // --- WebSocket
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${protocol}://${location.host}/ws`);

  ws.onopen = () => console.log('ws open');
  ws.onmessage = (evt) => {
    try {
      const payload = JSON.parse(evt.data);
      if (payload.type !== 'metrics') return;
      handleMetrics(payload.data);
    } catch (e) { console.error('ws parse', e); }
  };
  ws.onclose = () => console.log('ws closed');

  function pushPoint(chart, val) {
    const ts = new Date().toLocaleTimeString();
    chart.data.labels.push(ts);
    chart.data.datasets[0].data.push(isFinite(val) ? Number(val) : NaN);
    if (chart.data.labels.length > MAX_POINTS) {
      chart.data.labels.shift(); chart.data.datasets[0].data.shift();
    }
    chart.update('none');
  }

  function safeNum(x) {
    if (x == null) return null;
    const n = Number(x);
    return Number.isFinite(n) ? n : null;
  }

  function handleMetrics(hostsArray) {
    // hostsArray: [{ name, base_url, metrics: { cpu: ..., memory: ..., ... } }, ...]
    const now = new Date().toLocaleTimeString();
    hostsArray.forEach(h => {
      if (h.base_url !== selectedBase) return;
      const m = h.metrics || {};

      // IP
      const ip = m.ip ?? (typeof m.ip === 'string' ? m.ip : (m.ip && m.ip.ip) || '—');
      ipEl.textContent = ip;

      // GPU
      gpuEl.textContent = JSON.stringify(m.gpu ?? '—', null, 2);

      // Disk summary
      if (m.disk) {
        diskEl.textContent = JSON.stringify(m.disk, null, 0);
      }

      // Memory
      if (m.memory) {
        // m.memory likely is object with ram_usage or ram_used etc.
        memEl.textContent = (typeof m.memory === 'object') ? `used: ${m.memory.ram_used || m.memory.used || ''} (${m.memory.ram_usage ?? m.memory.usage ?? m.memory.percent ?? '—'}%)` : String(m.memory);
      }

      // CPU: PyNinja returns { detail: { cpu1: .. } } OR number if per_cpu=false.
      let cpuAvg = null;
      if (m.cpu) {
        const cpuDetail = (m.cpu && m.cpu.detail) ? m.cpu.detail : m.cpu;
        if (typeof cpuDetail === 'object') {
          const values = Object.values(cpuDetail).map(v => Number(v));
          const sum = values.reduce((a,b)=>a+(isFinite(b)?b:0),0);
          const count = values.length || 1;
          cpuAvg = sum / count;
          // update per-core charts
          Object.entries(cpuDetail).forEach(([core, val]) => {
            const coreObj = ensureCoreChart(core);
            const ts = now;
            coreObj.chart.data.labels.push(ts);
            coreObj.chart.data.datasets[0].data.push(Number(val));
            if (coreObj.chart.data.labels.length > MAX_POINTS) { coreObj.chart.data.labels.shift(); coreObj.chart.data.datasets[0].data.shift(); }
            coreObj.chart.update('none');
            coreObj.valEl.textContent = `${Number(val).toFixed(1)}%`;
          });
        } else if (typeof cpuDetail === 'number') {
          cpuAvg = cpuDetail;
        }
      }

      // CPU average chart
      if (cpuAvg != null) { pushPoint(cpuAvgChart, cpuAvg); }

      // CPU load (m1,m5,m15)
      if (m.cpu_load) {
        const load = (m.cpu_load && (m.cpu_load.detail || m.cpu_load)) || m.cpu_load;
        let text = '—';
        if (typeof load === 'object') {
          const m1 = load.m1 ?? load['m1'] ?? load[0];
          const m5 = load.m5 ?? load['m5'] ?? load[1];
          const m15 = load.m15 ?? load['m15'] ?? load[2];
          text = `${m1 ?? '—'} / ${m5 ?? '—'} / ${m15 ?? '—'}`;
          pushPoint(loadChart, Number(m1) || 0);
        } else if (typeof load === 'number') {
          pushPoint(loadChart, Number(load));
          text = String(load);
        }
        loadEl.textContent = text;
      }

      // Memory chart
      if (m.memory) {
        const memPerc = (m.memory.ram_usage ?? m.memory.ram_usage ?? m.memory.ram_usage) || m.memory.ram_usage || m.memory.swap_usage || m.memory.ram_usage || m.memory.ram_usage;
        // fallback heuristics:
        const percent = m.memory.ram_usage ?? m.memory.ram_usage ?? m.memory.ram_usage ?? m.memory.usage ?? m.memory.percent ?? (m.memory.ram_usage ? Number(m.memory.ram_usage) : null);
        pushPoint(memChart, safeNum(m.memory.ram_usage ?? m.memory.ram_usage ?? m.memory.ram_usage ?? m.memory.ram_usage ?? (typeof m.memory === 'number' ? m.memory : null)) || null);
      }

      // Services - m.services expected to be an array of objects (PyNinja returns detail array with service objects)
      if (Array.isArray(m.services)) {
        // render table, apply filter
        const filter = svcFilter.value.trim().toLowerCase();
        servicesTableBody.innerHTML = '';
        m.services.forEach(s => {
          const pname = s.pname || s.label || s.name || '';
          if (filter && !String(pname).toLowerCase().includes(filter)) return;
          const tr = document.createElement('tr');
          const tdPid = document.createElement('td'); tdPid.textContent = s.pid ?? s.PID ?? '';
          const tdName = document.createElement('td'); tdName.textContent = pname;
          const tdStatus = document.createElement('td'); tdStatus.textContent = s.status ?? '—';
          const tdCPU = document.createElement('td'); tdCPU.textContent = s.cpu ? JSON.stringify(s.cpu) : '—';
          const tdMem = document.createElement('td'); tdMem.textContent = s.memory ? (s.memory.rss || s.memory.pfaults || JSON.stringify(s.memory)) : '—';
          tr.append(tdPid, tdName, tdStatus, tdCPU, tdMem);
          servicesTableBody.appendChild(tr);
        });
      }

      // Docker stats and containers
      if (Array.isArray(m.docker_stats)) {
        dockerStatsEl.textContent = JSON.stringify(m.docker_stats, null, 2);
      } else if (m.docker_stats) {
        dockerStatsEl.textContent = JSON.stringify(m.docker_stats, null, 2);
      }

      if (Array.isArray(m.containers)) {
        containersList.innerHTML = '';
        m.containers.forEach(c => {
          const li = document.createElement('li');
          li.textContent = (c['Container Name'] || c.name || JSON.stringify(c));
          containersList.appendChild(li);
        });
      }

      // Disks list
      if (Array.isArray(m.disks)) {
        disksTableBody.innerHTML = '';
        m.disks.forEach(d => {
          const tr = document.createElement('tr');
          const tdName = document.createElement('td'); tdName.textContent = d.name || d.device_id || '';
          const tdSize = document.createElement('td'); tdSize.textContent = d.size || d.total || '';
          const tdMounts = document.createElement('td'); tdMounts.textContent = (d.mountpoints || []).join(', ');
          tr.append(tdName, tdSize, tdMounts);
          disksTableBody.appendChild(tr);
        });
      }

      if (m.certificates) {
        certsEl.textContent = JSON.stringify(m.certificates, null, 2);
      }
    });
  }

  // filter helper
  svcFilter.addEventListener('input', () => {
    // quick: re-render last known metrics by requesting a soft reset
    // (in this implementation we rely on incoming ws updates to call handleMetrics with same data)
  });

  // toggle per-core visibility (we always render per-core sparkline, checkbox could hide/show)
  showCoresCheckbox.addEventListener('change', () => {
    const visible = showCoresCheckbox.checked;
    Object.values(coreMini).forEach(o => {
      o.el.style.display = visible ? 'block' : 'none';
    });
  });

  // initial UI
  resetUI();
})();
