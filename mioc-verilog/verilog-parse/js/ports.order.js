/*
File: js/ports.order.js
Revision: r3 (2025-10-06)
Change Summary:
- Deterministic alphabetical I/O ordering even if core loads later.
- Protect first/last columns from barycentric reordering.
- Idempotent wrappers; multiple calls are safe.
*/

/* === VNLT REV ===
file: js/ports.order.js
rev:  2025-10-06  r3  by: ediaz  tag: gui
=== /VNLT REV === */

(function(){
  // Compare helper: case-insensitive, numeric-aware on label/name/id/string.
  function _label(v){
    if (v && typeof v === 'object') return String(v.label ?? v.name ?? v.id ?? v);
    return String(v);
  }
  function _cmp(a,b){ return _label(a).localeCompare(_label(b), undefined, {numeric:true, sensitivity:'base'}); }

  function _wrapBuildColumns(orig){
    if (!orig) return orig;
    if (orig.__ioSortWrapped) return orig;
    function wrappedBuildColumns(){
      const cols = orig.apply(this, arguments) || [];
      if (Array.isArray(cols) && cols.length >= 2){
        if (Array.isArray(cols[0])) cols[0] = [...cols[0]].sort(_cmp);
        const last = cols.length - 1;
        if (Array.isArray(cols[last])) cols[last] = [...cols[last]].sort(_cmp);
      }
      return cols;
    }
    Object.defineProperty(wrappedBuildColumns, "__ioSortWrapped", {value:true});
    return wrappedBuildColumns;
  }

  function _wrapRefineOrdering(orig){
    if (!orig) return orig;
    if (orig.__ioProtected) return orig;
    function wrappedRefineOrdering(columns, pos){
      if (!Array.isArray(columns) || columns.length < 2) return orig.apply(this, arguments);
      const left  = Array.isArray(columns[0]) ? [...columns[0]] : columns[0];
      const right = Array.isArray(columns[columns.length-1]) ? [...columns[columns.length-1]] : columns[columns.length-1];
      const res = orig.apply(this, arguments) || columns;
      if (Array.isArray(res) && res.length === columns.length){
        res[0] = left;
        res[res.length-1] = right;
      }
      return res;
    }
    Object.defineProperty(wrappedRefineOrdering, "__ioProtected", {value:true});
    return wrappedRefineOrdering;
  }

  function _ensureWrapped(){
    try {
      if (typeof window.buildColumns === 'function'){
        window.buildColumns = _wrapBuildColumns(window.buildColumns);
      }
      if (typeof window.refineOrdering === 'function'){
        window.refineOrdering = _wrapRefineOrdering(window.refineOrdering);
      }
    } catch(_) {}
  }

  // Retry strategy: run now, on DOM ready, on window load, and via timed nudges.
  function _install(){
    _ensureWrapped();
    // Timed retries to catch late-defined functions.
    let attempts = 0;
    const tm = setInterval(function(){
      _ensureWrapped();
      attempts++;
      if (attempts >= 10) clearInterval(tm);
    }, 50);

    // One-time nudge to re-render with sorted ports if globals exist
    function nudge(){
      try { if (window.ORDER && typeof window.ORDER.lockIOSort === 'function') window.ORDER.lockIOSort(); } catch(_){}
      try { if (typeof window.render === 'function' && window.columns && window.pos) window.render(window.columns, window.pos); } catch(_){}
    }
    setTimeout(nudge, 0);
    setTimeout(nudge, 100);
    window.addEventListener('load', function(){ setTimeout(nudge, 0); });
  }

  if (document.readyState === 'complete' || document.readyState === 'interactive') _install();
  else document.addEventListener('DOMContentLoaded', _install);
})();
