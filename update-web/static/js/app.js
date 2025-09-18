/* ÚNICA chamada por página ao /all-data, com cache em memória da aba */
const API_URL = "/all-data";

const SessionCache = {
  data: null,
  ts: 0,
  ttl: 55 * 1000, // segurança < 60s do backend
};

async function fetchAllData() {
  const now = Date.now();
  if (SessionCache.data && (now - SessionCache.ts) < SessionCache.ttl) {
    return SessionCache.data;
  }
  const res = await fetch(API_URL, { cache: "no-store" });
  if (!res.ok) throw new Error("Falha ao buscar /all-data");
  const json = await res.json();
  SessionCache.data = json;
  SessionCache.ts = now;
  return json;
}

function brDate(ts) {
  if (!ts) return "-";
  const d = new Date(ts);
  if (isNaN(d)) return ts;
  const dia = String(d.getDate()).padStart(2, "0");
  const mes = String(d.getMonth() + 1).padStart(2, "0");
  const ano = d.getFullYear();
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${dia}/${mes}/${ano} ${hh}:${mm}`;
}

function countBy(arr, keyFn) {
  const m = new Map();
  arr.forEach(x => {
    const k = keyFn(x);
    m.set(k, (m.get(k) || 0) + 1);
  });
  return m;
}

function filterByQuery(items, query, fields) {
  if (!query) return items;
  const q = query.trim().toLowerCase();
  return items.filter(it => fields.some(f => (it[f] || "").toString().toLowerCase().includes(q)));
}

function paginate(items, page, perPage) {
  const total = items.length;
  const pages = Math.max(1, Math.ceil(total / perPage));
  const p = Math.min(Math.max(1, page), pages);
  const start = (p - 1) * perPage;
  return { page: p, pages, total, slice: items.slice(start, start + perPage) };
}

/* ===================== */
/* CHART HELPERS COM CORES E LABELS */
/* ===================== */

// Cores principais (status e SO)
const COLORS = {
  SUCCESS: "#22c55e",           // verde
  FAILED: "#ef4444",            // vermelho
  NO_UPDATES_FOUND: "#9ca3af",  // cinza
  Windows: "#3b82f6",           // azul
  Linux: "#6366f1",             // roxo
  Default: "#60a5fa"            // azul claro
};

// Paleta para ambientes (estável por nome)
const PALETTE = [
  "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
  "#06b6d4", "#84cc16", "#ec4899", "#f97316", "#14b8a6",
  "#a855f7", "#22d3ee", "#eab308", "#64748b", "#34d399",
  "#fb7185", "#0ea5e9", "#9333ea", "#16a34a", "#2563eb"
];

function colorFor(label) {
  return COLORS[label] || COLORS.Default;
}

function hashIndex(str, mod) {
  let h = 0;
  for (let i = 0; i < String(str).length; i++) {
    h = (h * 31 + String(str).charCodeAt(i)) >>> 0;
  }
  return h % mod;
}

function colorsForLabels(labels) {
  return labels.map(l => PALETTE[hashIndex(l, PALETTE.length)]);
}

function hexToRgb(hex) {
  const h = hex.replace("#", "");
  const bigint = parseInt(h, 16);
  return { r: (bigint >> 16) & 255, g: (bigint >> 8) & 255, b: bigint & 255 };
}

function rgba(hex, a) {
  const { r, g, b } = hexToRgb(hex);
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}

function monoShades(baseHex, n) {
  // Gera variações de opacidade 1.0 -> 0.55
  const shades = [];
  for (let i = 0; i < n; i++) {
    const alpha = Math.max(0.55, 1.0 - i * 0.15);
    shades.push(rgba(baseHex, alpha));
  }
  return shades;
}

/**
 * makePie / makeBar com esquema de cor controlável
 * opts:
 *  - colorMode:
 *      'status'     => mapeia por label em COLORS (default para pie)
 *      'palette'    => paleta estável por label (ambientes)
 *      'single'     => uma cor para todas as barras/fatias (use opts.singleColor)
 *      'monochrome' => variações do opts.baseColor (pie de falhas por SO)
 *  - singleColor / baseColor
 */
function makePie(ctxId, labels, data, title, opts = {}) {
  const ctx = document.getElementById(ctxId);
  if (!ctx) return null;

  let bg;
  if (opts.colorMode === "single") {
    bg = labels.map(() => opts.singleColor || COLORS.Default);
  } else if (opts.colorMode === "palette") {
    bg = colorsForLabels(labels);
  } else if (opts.colorMode === "monochrome") {
    bg = monoShades(opts.baseColor || COLORS.Default, labels.length);
  } else { // 'status' (default)
    bg = labels.map(l => colorFor(l));
  }

  return new Chart(ctx, {
    type: "pie",
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: bg,
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: !!title,
          text: title,
          font: { size: 14, weight: "bold" }
        },
        legend: {
          position: "right",
          labels: { boxWidth: 12, font: { size: 11 } }
        }
      }
    }
  });
}

function makeBar(ctxId, labels, data, title, opts = {}) {
  const ctx = document.getElementById(ctxId);
  if (!ctx) return null;

  let bg;
  if (opts.colorMode === "single") {
    bg = labels.map(() => opts.singleColor || COLORS.Default);
  } else if (opts.colorMode === "palette") {
    bg = colorsForLabels(labels);
  } else { // fallback
    bg = labels.map(l => colorFor(l));
  }

  return new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: bg,
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: !!title,
          text: title,
          font: { size: 14, weight: "bold" }
        },
        legend: { display: false },
        datalabels: {
          anchor: "end",
          align: "top",
          formatter: v => v,
          font: { size: 11, weight: "bold" }
        }
      },
      scales: {
        x: {
          ticks: { font: { size: 11 }, autoSkip: false, maxRotation: 45 }
        },
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1, font: { size: 11 } }
        }
      }
    },
    plugins: [ChartDataLabels]
  });
}

/* KPIs */
function setKpi(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function only(arr, status) {
  return arr.filter(x => x.update_status === status);
}
