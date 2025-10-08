// === VNLT REV ===
// file: js/placement.apply.js
// rev:  2025-10-07  r1  by: ediaz  tag: gui
// note: Apply deterministic file-driven placement. Exposes
//       window.applyPlacementFromCSV(graph, csvPath).
//       CSV headers: id,col,row (or ID,col,row).
//
// Usage from HTML (after graph is built, before any auto-layout):
//   <script src="../js/placement.apply.js"
//       onload="window.applyPlacementFromCSV && window.applyPlacementFromCSV(window.vnltGraph, '../data-in/placement.csv');"></script>
//
(function(){
  const GRID_W = 180;
  const GRID_H = 110;
  const MARGIN_X = 40;
  const MARGIN_Y = 40;

  function parseCSV(text) {
    const lines = text.replace(/\r/g,'').trim().split('\n');
    if (!lines.length) return [];
    const header = lines[0].split(',').map(s => s.trim());
    const idKey = header.includes('id') ? 'id' : (header.includes('ID') ? 'ID' : null);
    const colIdx = header.findIndex(h => h.toLowerCase() === 'col');
    const rowIdx = header.findIndex(h => h.toLowerCase() === 'row');
    const idIdx  = idKey ? header.findIndex(h => h === idKey) : -1;
    if (idIdx < 0 || colIdx < 0 || rowIdx < 0) {
      console.warn('[placement.apply] Bad CSV header, expected id,col,row or ID,col,row ->', header);
      return [];
    }
    const out = [];
    for (let i=1;i<lines.length;i++) {
      const cols = lines[i].split(',').map(s => s.trim());
      if (!cols.length || cols.every(c => c==='')) continue;
      const id  = cols[idIdx];
      const col = Number(cols[colIdx]);
      const row = Number(cols[rowIdx]);
      if (!id || Number.isNaN(col) || Number.isNaN(row)) continue;
      out.push({ id, col, row });
    }
    return out;
  }

  function toXY(col, row) {
    return {
      x: MARGIN_X + col * GRID_W,
      y: MARGIN_Y + row * GRID_H
    };
  }

  function applyToGraph(graph, place) {
    let applied = 0;
    const byId = new Map(place.map(p => [String(p.id), p]));

    // Strategy A: cytoscape.js instance
    if (graph && typeof graph === 'object' && typeof graph.$id === 'function') {
      byId.forEach((p, id) => {
        const n = graph.$id(id);
        if (n && n.nonempty) {
          const xy = toXY(p.col, p.row);
          try { n.position({x: xy.x, y: xy.y}); applied++; } catch {}
        }
      });
      try { graph.resize(); graph.fit(); } catch {}
      return applied;
    }

    // Strategy B: explicit API: setNodePosition(id,x,y)
    if (graph && typeof graph.setNodePosition === 'function') {
      byId.forEach((p, id) => {
        const xy = toXY(p.col, p.row);
        try { graph.setNodePosition(id, xy.x, xy.y); applied++; } catch {}
      });
      if (typeof graph.refresh === 'function') try { graph.refresh(); } catch {}
      return applied;
    }

    // Strategy C: nodes array with {id,x,y}
    if (graph && Array.isArray(graph.nodes)) {
      for (const n of graph.nodes) {
        const p = byId.get(String(n.id));
        if (!p) continue;
        const xy = toXY(p.col, p.row);
        try { n.x = xy.x; n.y = xy.y; applied++; } catch {}
      }
      if (typeof graph.refresh === 'function') try { graph.refresh(); } catch {}
      return applied;
    }

    // Strategy D: object with getNodes()
    if (graph && typeof graph.getNodes === 'function') {
      const nodes = graph.getNodes();
      for (const n of nodes) {
        const id = String(n.id ?? n.get?.('id') ?? '');
        const p = byId.get(id);
        if (!p) continue;
        const xy = toXY(p.col, p.row);
        if (typeof n.setPosition === 'function') {
          try { n.setPosition(xy.x, xy.y); applied++; } catch {}
        } else {
          try { n.x = xy.x; n.y = xy.y; applied++; } catch {}
        }
      }
      if (typeof graph.refresh === 'function') try { graph.refresh(); } catch {}
      return applied;
    }

    // Strategy E: fallback DOM mark (for D3 renderers reading data on next tick)
    byId.forEach((p, id) => {
      const el = document.querySelector(`[data-id="${CSS.escape(id)}"]`);
      if (!el) return;
      const xy = toXY(p.col, p.row);
      el.setAttribute('data-x', String(xy.x));
      el.setAttribute('data-y', String(xy.y));
      applied++;
    });
    return applied;
  }

  async function fetchCSV(url) {
    const res = await fetch(url, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`fetch failed (${res.status}) for ${url}`);
    return await res.text();
  }

  async function applyPlacementFromCSV(graph, csvPath) {
    try {
      const txt = await fetchCSV(csvPath);
      const rows = parseCSV(txt);
      if (!rows.length) {
        console.warn('[placement.apply] No rows parsed from CSV:', csvPath);
        return 0;
      }
      const count = applyToGraph(graph, rows);
      // Optional hook for renderers that need a fit after position changes
      if (typeof window.onPlacementApplied === 'function') {
        try { window.onPlacementApplied(count); } catch {}
      }
      // Prevent accidental force layout tick
      if (graph && typeof graph.stop === 'function') { try { graph.stop(); } catch {} }
      if (typeof window.requestAnimationFrame === 'function') {
        requestAnimationFrame(() => {
          if (graph && typeof graph.stop === 'function') { try { graph.stop(); } catch {} }
        });
      }
      console.log(`[placement.apply] Applied ${count} nodes from ${csvPath}`);
      return count;
    } catch (e) {
      console.error('[placement.apply] ERROR:', e);
      return 0;
    }
  }

  // expose
  window.applyPlacementFromCSV = applyPlacementFromCSV;
})();