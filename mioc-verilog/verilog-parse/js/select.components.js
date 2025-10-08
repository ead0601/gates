/*
File: js/select.components.js
Revision: r5 (2025-10-06)
Change Summary:
- Force pure red on selected components using high-specificity CSS + !important.
- No behavior changes (click to select; Clear Components to clear).
*/

/* === VNLT REV ===
file: js/select.components.js
rev:  2025-10-06  r5  by: ediaz  tag: gui
=== /VNLT REV === */

(function(){
  const SELECTED_NODES = new Set();   // ids
  const NODE_COLOR = new Map();       // id -> color (always red)
  const RED = '#ff0000';

  function injectStyle(){
    if (document.getElementById('comp-select-style')) return;
    const st = document.createElement('style');
    st.id = 'comp-select-style';
    st.textContent = [
      // Never let selected nodes get dimmed or filtered by masks
      'svg g[data-comp-sel="1"] { opacity: 1 !important; filter: none !important; }',
      // Force stroke to pure red on common SVG shapes inside the node group
      'svg g[data-comp-sel="1"] rect,',
      'svg g[data-comp-sel="1"] path,',
      'svg g[data-comp-sel="1"] path.round,',
      'svg g[data-comp-sel="1"] polygon,',
      'svg g[data-comp-sel="1"] ellipse,',
      'svg g[data-comp-sel="1"] circle {',
      '  stroke: #ff0000 !important;',
      '  stroke-width: 2.5 !important;',
      '}',
      // Keep label bold for visibility
      'svg g[data-comp-sel="1"] text.label { font-weight: 600 !important; }'
    ].join('\n');
    document.head.appendChild(st);
  }

  function colorFor(id){
    NODE_COLOR.set(id, RED);
    return RED;
  }

  function applyStylesToNodeG(g, id){
    const color = colorFor(id);
    g.setAttribute('data-comp-sel', '1');
    const round = g.querySelector('path.round');
    const rect  = g.querySelector('rect');
    const shape = round || rect;
    if (shape && !shape.hasAttribute('fill')) {
      shape.setAttribute('fill', '#ffffff'); // keep a light fill if none set
    }
  }

  function clearStylesFromNodeG(g){
    g.removeAttribute('data-comp-sel');
  }

  function toggleNode(id, g){
    if (SELECTED_NODES.has(id)){
      SELECTED_NODES.delete(id);
      NODE_COLOR.delete(id);
      clearStylesFromNodeG(g);
    } else {
      SELECTED_NODES.add(id);
      applyStylesToNodeG(g, id);
    }
  }

  function reapplyAll(){
    try{
      const gNodes = document.getElementById('nodes');
      if (!gNodes) return;
      SELECTED_NODES.forEach(id=>{
        const g = gNodes.querySelector('g[data-id="' + CSS.escape(id) + '"]');
        if (g) applyStylesToNodeG(g, id);
      });
    }catch{}
  }

  function onNodeClick(e){
    const gNodes = document.getElementById('nodes');
    if (!gNodes) return;
    const g = e.target.closest && e.target.closest('g');
    if (!g || !gNodes.contains(g)) return;
    const id = g.getAttribute('data-id');
    if (!id) return;
    toggleNode(id, g);
  }

  function onClearComponents(){
    const gNodes = document.getElementById('nodes');
    if (!gNodes) return;
    SELECTED_NODES.forEach(id=>{
      const g = gNodes.querySelector('g[data-id="' + CSS.escape(id) + '"]');
      if (g) clearStylesFromNodeG(g);
    });
    SELECTED_NODES.clear();
    NODE_COLOR.clear();
  }

  function init(){
    injectStyle();

    const gNodes = document.getElementById('nodes');
    if (gNodes && !gNodes.__compClickBound){
      gNodes.addEventListener('click', onNodeClick, true);
      gNodes.__compClickBound = true;
    }

    const btn = document.getElementById('btnClearComponents');
    if (btn && !btn.__compClearBound){
      btn.addEventListener('click', onClearComponents);
      btn.__compClearBound = true;
    }

    // Re-apply after each render (idempotent)
    if (typeof window.render === 'function' && !window.render.__compReapply){
      const orig = window.render;
      window.render = function(){
        const res = orig.apply(this, arguments);
        reapplyAll();
        return res;
      };
      window.render.__compReapply = true;
    }

    window.addEventListener('load', reapplyAll);
  }

  if (document.readyState === 'complete' || document.readyState === 'interactive') init();
  else document.addEventListener('DOMContentLoaded', init);
})();
