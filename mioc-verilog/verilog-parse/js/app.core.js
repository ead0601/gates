/*
File: js/app.core.js
Revision: r3 (2025-10-06)
Change Summary:
- Deterministic IO port order: sort inputs/outputs at layout time and protect them from barycentric reordering.
- No other behavior changes.
*/
/*
File: js/app.core.r1.js
Revision: r1 (2025-10-05)
Change Summary:
- Extracted from graph_view_ffcenter_r8.html. No behavior changes.
*/

/* === VNLT REV ===
file: js/app.core.r1.js
rev:  2025-10-05  r1  by: ediaz  tag: gui
=== /VNLT REV === */
/* CLI replaces this at runtime */
window.VNLT_GRAPH = window.VNLT_GRAPH || {nodes:[], edges:[], io:{inputs:[], outputs:[]}, _meta:{}};

/* ==== Model ==== */
const byId = id => document.getElementById(id);
const svg = byId('svg');
const GRAW = window.VNLT_GRAPH;

const MODEL = {
  nodes: new Map(),
  inputs: new Set(GRAW.io?.inputs || []),
  outputs: new Set(GRAW.io?.outputs || []),
  succ: new Map(), pred: new Map(),
  edges: []
};

/* Build nodes */
(function initNodes(){
  const SEQ_HINTS=['dff','flop','latch','ff','seq'];
  (GRAW.nodes||[]).forEach(n=>{
    const isIO = MODEL.inputs.has(n.id) || MODEL.outputs.has(n.id) || (n.type||'').toLowerCase()==='io';
    const tstr = (n.type || n.attrs?.type || n.label || '').toLowerCase();
    MODEL.nodes.set(n.id,{ id:n.id, label:n.label||n.id, raw:n,
      type: isIO ? 'io' : (SEQ_HINTS.some(k=>tstr.includes(k))?'ff':'comb'),
      side:'io', rank:0 });
  });
  (GRAW.io?.inputs||[]).forEach(id=>{ if(!MODEL.nodes.has(id)) MODEL.nodes.set(id,{id,label:id,raw:{},type:'io',side:'io',rank:0}); });
  (GRAW.io?.outputs||[]).forEach(id=>{ if(!MODEL.nodes.has(id)) MODEL.nodes.set(id,{id,label:id,raw:{},type:'io',side:'io',rank:0}); });
})();
/* Build edges & adjacency */
(function initEdges(){
  const push=(m,k,v)=>{ if(!m.has(k)) m.set(k,new Set()); m.get(k).add(v); };
  (GRAW.edges||[]).forEach(e=>{
    const src=e.src??e.source, dst=e.dst??e.target;
    if(!MODEL.nodes.has(src) || !MODEL.nodes.has(dst)) return;
    MODEL.edges.push({src,dst,src_port:e.src_port||'',dst_port:e.dst_port||'',net:e.net||e.label||''});
    push(MODEL.succ,src,dst); push(MODEL.pred,dst,src);
  });
})();

/* ==== Layout helpers ==== */
function bfsForward(starts, stopSet=null){ const Q=[...starts], seen=new Set(Q);
  for(let i=0;i<Q.length;i++){ const u=Q[i]; if(stopSet&&stopSet.has(u)) continue;
    const ns=MODEL.succ.get(u)||[]; for(const v of ns){ if(!seen.has(v)){ seen.add(v); Q.push(v); } } } return seen; }
function bfsReverse(starts, stopSet=null){ const Q=[...starts], seen=new Set(Q);
  for(let i=0;i<Q.length;i++){ const u=Q[i]; if(stopSet&&stopSet.has(u)) continue;
    const ns=MODEL.pred.get(u)||[]; for(const v of ns){ if(!seen.has(v)){ seen.add(v); Q.push(v); } } } return seen; }

function classifySides(){
  const IO_IN=new Set(MODEL.inputs), IO_OUT=new Set(MODEL.outputs);
  const FFS=new Set([...MODEL.nodes.values()].filter(n=>n.type==='ff').map(n=>n.id));
  const COMB=new Set([...MODEL.nodes.values()].filter(n=>n.type==='comb').map(n=>n.id));
  const reachFromInputs=bfsForward([...IO_IN], FFS);
  const canReachFF=bfsReverse([...FFS]);
  const LEFT=new Set([...COMB].filter(n=>reachFromInputs.has(n)&&canReachFF.has(n)));
  const fromFF=bfsForward([...FFS]); const reachOutputs=bfsReverse([...IO_OUT]);
  const RIGHT=new Set([...COMB].filter(n=>fromFF.has(n)&&reachOutputs.has(n)));
  MODEL.nodes.forEach(n=>{
    if(MODEL.inputs.has(n.id)){ n.side='left'; n.type='io'; return; }
    if(MODEL.outputs.has(n.id)){ n.side='right'; n.type='io'; return; }
    if(n.type==='ff'){ n.side='center'; return; }
    if(RIGHT.has(n.id)){ n.side='right'; return; }
    if(LEFT.has(n.id)){ n.side='left'; return; }
    const indeg=(MODEL.pred.get(n.id)?.size||0), outdeg=(MODEL.succ.get(n.id)?.size||0);
    n.side = outdeg>=indeg ? 'right' : 'left';
  });
}

function rankSides(){
  const leftNodes=[...MODEL.nodes.values()].filter(n=>n.side==='left'&&n.type==='comb');
  const rankLeft=new Map([...MODEL.inputs].map(id=>[id,0]));
  for(let pass=0; pass<6; pass++){
    leftNodes.forEach(n=>{
      let r=1; const ps=MODEL.pred.get(n.id)||[];
      for(const p of ps){ const base=rankLeft.has(p)?rankLeft.get(p):(MODEL.inputs.has(p)?0:undefined);
        if(base!==undefined) r=Math.max(r,(base||0)+1); }
      rankLeft.set(n.id,r);
    });
  }
  const rightNodes=[...MODEL.nodes.values()].filter(n=>n.side==='right'&&n.type==='comb');
  const ffs=[...MODEL.nodes.values()].filter(n=>n.type==='ff').map(n=>n.id);
  const rankRight=new Map(ffs.map(id=>[id,0]));
  for(let pass=0; pass<8; pass++){
    rightNodes.forEach(n=>{
      let r=1; const ps=MODEL.pred.get(n.id)||[];
      for(const p of ps){ const pk=rankRight.get(p); if(pk!==undefined) r=Math.max(r,pk+1); }
      rankRight.set(n.id,r);
    });
  }
  let Lmax=0,Rmax=0; leftNodes.forEach(n=>{ n.rank=rankLeft.get(n.id)||1; Lmax=Math.max(Lmax,n.rank); });
  rightNodes.forEach(n=>{ n.rank=rankRight.get(n.id)||1; Rmax=Math.max(Rmax,n.rank); });
  return {Lmax,Rmax};
}

function buildColumns({Lmax,Rmax}){
  const cols=[];
  cols.push([...MODEL.inputs]);
  for(let i=1;i<=Math.max(Lmax,1);i++) cols.push([...MODEL.nodes.values()].filter(n=>n.side==='left'&&n.type==='comb'&&n.rank===i).map(n=>n.id));
  cols.push([...MODEL.nodes.values()].filter(n=>n.type==='ff').map(n=>n.id));
  for(let i=1;i<=Math.max(Rmax,1);i++) cols.push([...MODEL.nodes.values()].filter(n=>n.side==='right'&&n.type==='comb'&&n.rank===i).map(n=>n.id));
  cols.push([...MODEL.outputs]);
  const compact=[cols[0]]; for(let i=1;i<cols.length-1;i++){ if(cols[i].length) compact.push(cols[i]); } compact.push(cols[cols.length-1]); return compact;
}

/* Ordering */
function refineOrdering(columns, passes=2){
  const order=new Map(); columns.forEach(col=>col.forEach((id,idx)=>order.set(id,idx)));
  const med=a=>{ if(!a.length) return Infinity; a.sort((x,y)=>x-y); const m=Math.floor(a.length/2); return a.length%2?a[m]:0.5*(a[m-1]+a[m]); };
  for(let r=0;r<passes;r++){
    for(let ci=1; ci<columns.length-1; ci++){
      const prev=new Set(columns[ci-1]);
      columns[ci].sort((a,b)=> med([...(MODEL.pred.get(a)||[])].filter(p=>prev.has(p)).map(p=>order.get(p)).filter(v=>v!==undefined)) -
                               med([...(MODEL.pred.get(b)||[])].filter(p=>prev.has(p)).map(p=>order.get(p)).filter(v=>v!==undefined)));
      columns[ci].forEach((id,idx)=>order.set(id,idx));
    }
    for(let ci=columns.length-2; ci>=1; ci--){
      const next=new Set(columns[ci+1]);
      columns[ci].sort((a,b)=> med([...(MODEL.succ.get(a)||[])].filter(s=>next.has(s)).map(s=>order.get(s)).filter(v=>v!==undefined)) -
                               med([...(MODEL.succ.get(b)||[])].filter(s=>next.has(s)).map(s=>order.get(s)).filter(v=>v!==undefined)));
      columns[ci].forEach((id,idx)=>order.set(id,idx));
    }
  }
  return columns;
}

/* ==== Layout + Render ==== */
const geom={ colW:320, rowH:70, marginX:90, marginY:60, nodeW:180, nodeH:36 };
function clearChildren(n){ while(n.firstChild) n.removeChild(n.firstChild); }

function layoutAndRender(){
  classifySides(); const LR=rankSides();
  let columns=buildColumns(LR); 
// r3: FF pre-sort at layout choke point
(function(){
  const n = Array.isArray(columns) ? columns.length : 0;
  if (n >= 3) {
    const centers = (n % 2 === 1) ? [Math.floor(n/2)] : [n/2 - 1, n/2];
    const _cmp = (a,b) => {
      const L = v => (v && typeof v==='object') ? String(v.label ?? v.name ?? v.id ?? v) : String(v);
      return L(a).localeCompare(L(b), undefined, {numeric:true, sensitivity:'base'});
    };
    for (const ci of centers) {
      if (Array.isArray(columns[ci])) columns[ci] = [...columns[ci]].sort(_cmp);
    }
  }
})();
columns=refineOrdering(columns,2);
  
// r3: FF re-assert after refinement
(function(){
  const n = Array.isArray(columns) ? columns.length : 0;
  if (n >= 3) {
    const centers = (n % 2 === 1) ? [Math.floor(n/2)] : [n/2 - 1, n/2];
    const _cmp = (a,b) => {
      const L = v => (v && typeof v==='object') ? String(v.label ?? v.name ?? v.id ?? v) : String(v);
      return L(a).localeCompare(L(b), undefined, {numeric:true, sensitivity:'base'});
    };
    for (const ci of centers) {
      if (Array.isArray(columns[ci])) columns[ci] = [...columns[ci]].sort(_cmp);
    }
  }
})();
// re-assert IO alpha after refinement
if (Array.isArray(columns) && columns.length>=2){
  if (Array.isArray(columns[0])) columns[0] = [...columns[0]].sort(_ioCmp);
  if (Array.isArray(columns[columns.length-1])) columns[columns.length-1] = [...columns[columns.length-1]].sort(_ioCmp);
}
const pos=new Map(); let maxRows=Math.max(...columns.map(c=>c.length),1);
  const totalW=geom.marginX*2 + (columns.length-1)*geom.colW;
  const totalH=geom.marginY*2 + (maxRows-1)*geom.rowH;
  svg.setAttribute('viewBox', `0 0 ${Math.max(1400,totalW)} ${Math.max(900,totalH)}`);
  columns.forEach((col,ci)=>{ col.forEach((id,ri)=>{ pos.set(id,{x:geom.marginX+ci*geom.colW, y:geom.marginY+ri*geom.rowH}); }); });
  render(columns,pos); summarize();
}

/* ==== Net coloring & soloing ==== */
const PALETTE=["#60a5fa","#34d399","#f472b6","#f59e0b","#a78bfa","#f87171","#22d3ee","#e11d48","#10b981","#fb7185","#84cc16","#06b6d4"];
let netColor = new Map(); // net -> palette index
let soloNet = null;       // net name or null
let bridgedNets = new Set();

function applyNetColors(){
  const paths = byId('edges').querySelectorAll('.edge-path');
  paths.forEach((el,idx)=>{
    const net = MODEL.edges[idx].net || "";
    const idxColor = netColor.get(net);
    const color = (idxColor===undefined) ? "var(--edge)" : PALETTE[idxColor % PALETTE.length];
    el.style.color = color; el.style.stroke = color;
  });
}
function cycleNetColor(net){
  if(!net) return;
  const cur = netColor.get(net);
  if(cur===undefined) netColor.set(net, 0);
  else netColor.set(net, (cur+1) % PALETTE.length);
  applyNetColors(); saveSessionColors();
}
function resetNetColors(){ netColor.clear(); applyNetColors(); saveSessionColors(); }
function loadSessionColors(){ try{ const raw=sessionStorage.getItem("vnlt_netcolors"); if(!raw) return; netColor=new Map(Object.entries(JSON.parse(raw))); }catch{} }
function saveSessionColors(){ try{ sessionStorage.setItem("vnlt_netcolors", JSON.stringify(Object.fromEntries(netColor))); }catch{} }

function setSoloNet(net){
  soloNet = (soloNet===net) ? null : net;
  drawSoloMask();
  drawNetBadges();
  updateNetSidebar();
}
function drawSoloMask(){
  const paths = byId('edges').querySelectorAll('.edge-path');
  const nodes = byId('nodes').querySelectorAll('g');
  paths.forEach((el,idx)=>{
    const net = MODEL.edges[idx].net || "";
    const isSolo = (!soloNet || net===soloNet || bridgedNets.has(net));
    el.classList.toggle('solo-dim', !isSolo);
  });
  nodes.forEach(el=>{ el.classList.toggle('solo-dim', !!soloNet); });
  if(soloNet){
    const keep = new Set();
    MODEL.edges.forEach((e)=>{ if(e.net===soloNet || bridgedNets.has(e.net)){ keep.add(e.src); keep.add(e.dst); }});
    nodes.forEach(el=>{ if(keep.has(el.dataset.id)) el.classList.remove('solo-dim'); });
  }
}

/* ==== IOBUF detection & recursive bridging ==== */
function isIOBUF(nodeId){
  const n = MODEL.nodes.get(nodeId);
  const t = (n?.raw?.label || n?.raw?.attrs?.type || n?.label || "").toLowerCase();
  return t.includes("iobuf");
}

/* NEW: recursively collect all nets reachable through any number of IOBUFs.
   We treat nets as nodes in a meta-graph; edges exist between two nets if they
   meet at the same IOBUF instance. */
function netsAcrossIOBUFFromNet(seedNet){
  const visited = new Set([seedNet]);
  const out = new Set();
  const queue = [seedNet];

  while(queue.length){
    const net = queue.shift();

    // Find all IOBUF nodes that this net touches
    const touchingIOBUFs = new Set();
    MODEL.edges.forEach(e=>{
      if(e.net !== net) return;
      if(isIOBUF(e.src)) touchingIOBUFs.add(e.src);
      if(isIOBUF(e.dst)) touchingIOBUFs.add(e.dst);
    });

    // For each such IOBUF, add ALL nets incident to it (both directions)
    touchingIOBUFs.forEach(io=>{
      MODEL.edges.forEach(e2=>{
        if(e2.src===io || e2.dst===io){
          const n2 = e2.net;
          if(!visited.has(n2)){
            visited.add(n2);
            out.add(n2);
            queue.push(n2);
          }
        }
      });
    });
  }

  out.delete(seedNet);
  return out;
}

function styleBridgedEdges(){
  const paths = byId('edges').querySelectorAll('.edge-path');
  paths.forEach((el,idx)=>{
    const net = MODEL.edges[idx].net || "";
    el.classList.toggle('edge-bridge', bridgedNets.has(net));
  });
}

/* ==== Render ==== */
function _ioLabel(v){ if(v&&typeof v==='object') return String(v.label??v.name??v.id??v); return String(v); }
function _ioCmp(a,b){ return _ioLabel(a).localeCompare(_ioLabel(b), undefined, {numeric:true, sensitivity:'base'}); }
function render(columns,pos){
  const gNodes=byId('nodes'), gEdges=byId('edges'), gGrid=byId('grid'), gBadges=byId('badges');
  clearChildren(gNodes); clearChildren(gEdges); clearChildren(gGrid); clearChildren(gBadges);

  // Edges
  for(const e of MODEL.edges){
    const ps=pos.get(e.src), pd=pos.get(e.dst); if(!ps||!pd) continue;
    const x1=ps.x+geom.nodeW, y1=ps.y+geom.nodeH/2;
    const x2=pd.x,            y2=pd.y+geom.nodeH/2;
    const dx=Math.max(60, Math.abs(x2-x1)*0.45);
    const d=`M ${x1} ${y1} C ${x1+dx} ${y1} ${x2-dx} ${y2} ${x2} ${y2}`;

    const p=document.createElementNS('http://www.w3.org/2000/svg','path');
    p.setAttribute('d',d); p.setAttribute('class','edge-path'); p.dataset.net=e.net||'';
    gEdges.appendChild(p);

    const hit=document.createElementNS('http://www.w3.org/2000/svg','path');
    hit.setAttribute('d',d); hit.setAttribute('class','edge-hit');
    hit.addEventListener('click', ()=>{ selectEdge(e,p); cycleNetColor(e.net||''); setSoloNet(e.net||''); });
    gEdges.appendChild(hit);
  }
  loadSessionColors(); applyNetColors(); styleBridgedEdges();

  // Nodes
  for(const n of MODEL.nodes.values()){
    const p=pos.get(n.id); if(!p) continue;
    const g=document.createElementNS('http://www.w3.org/2000/svg','g');
    g.setAttribute('class',`node ${n.type}`); g.dataset.id=n.id;
    g.setAttribute('transform',`translate(${p.x},${p.y})`);
    if(n.type==='ff'){
      const path=document.createElementNS('http://www.w3.org/2000/svg','path');
      const w=geom.nodeW,h=geom.nodeH,ry=h/2;
      const d=`M 0 ${ry} A ${ry} ${ry} 0 0 1 ${ry} 0 H ${w-ry} A ${ry} ${ry} 0 0 1 ${w} ${ry} A ${ry} ${ry} 0 0 1 ${w-ry} ${h} H ${ry} A ${ry} ${ry} 0 0 1 0 ${ry} Z`;
      path.setAttribute('d',d); path.setAttribute('class','round'); g.appendChild(path);
    }else{
      const r=document.createElementNS('http://www.w3.org/2000/svg','rect');
      r.setAttribute('width',geom.nodeW); r.setAttribute('height',geom.nodeH); r.setAttribute('rx',6); g.appendChild(r);
    }
    const txt=document.createElementNS('http://www.w3.org/2000/svg','text');
    txt.setAttribute('x',10); txt.setAttribute('y',22); txt.setAttribute('class','label');
    txt.textContent = n.type==='io' ? n.label : `${n.id} (${n.raw?.label || n.raw?.attrs?.type || n.type})`;
    g.appendChild(txt);

    g.addEventListener('click',()=>selectNode(n,g));
    gNodes.appendChild(g);
  }
}

/* ==== Selection, cones & badges ==== */
let currentSelection=null;

function selectNode(n,gEl){
  currentSelection={kind:'node', id:n.id};
  document.querySelectorAll('.selected').forEach(e=>e.classList.remove('selected'));
  gEl.classList.add('selected');
  byId('sel').textContent = `${n.id} — ${n.type}`;
  byId('info').innerHTML = `<div><b>Side:</b> ${n.side}</div><div><b>Rank:</b> ${n.rank||0}</div>`;
  clearBadges();
}
function selectEdge(e,pathEl){
  currentSelection={kind:'edge', edge:e};
  document.querySelectorAll('.selected').forEach(el=>el.classList.remove('selected'));
  pathEl.classList.add('selected');
  byId('sel').textContent = `edge ${e.src}:${e.src_port||''} → ${e.dst}:${e.dst_port||''} [${e.net||''}]`;
  updateNetSidebar();
  drawNetBadges();
}

function clearBadges(){ clearChildren(byId('badges')); }

function getNodePos(id){
  const g = document.querySelector(`g.node[data-id="${id}"]`);
  if(!g) return null;
  const m = g.transform.baseVal.consolidate().matrix;
  return {x:m.e, y:m.f + geom.nodeH/2};
}
function drawNetBadges(){
  clearBadges();
  if(!soloNet) return;
  const g=byId('badges');
  const drivers=new Set(), loads=new Set();
  MODEL.edges.forEach(e=>{ if(e.net===soloNet){ drivers.add(e.src); loads.add(e.dst);} });
  drivers.forEach(id=>{
    const pos = getNodePos(id); if(!pos) return;
    const t = document.createElementNS('http://www.w3.org/2000/svg','text');
    t.setAttribute('x', pos.x - 8); t.setAttribute('y', pos.y + 9);
    t.setAttribute('class','badge badge-src');
    t.textContent='SRC';
    g.appendChild(t);
  });
  loads.forEach(id=>{
    const pos = getNodePos(id); if(!pos) return;
    const t = document.createElementNS('http://www.w3.org/2000/svg','text');
    t.setAttribute('x', pos.x + geom.nodeW + 8); t.setAttribute('y', pos.y + 9);
    t.setAttribute('class','badge badge-dst');
    t.textContent='DST';
    g.appendChild(t);
  });
}

function clearHighlight(){
  document.querySelectorAll('#nodes > g, #edges > path').forEach(el=>el.classList.remove('dim','selected','solo-dim','edge-bridge'));
  soloNet=null; bridgedNets.clear(); clearBadges();
  byId('sel').textContent='None'; byId('info').textContent='';
  currentSelection=null; styleBridgedEdges(); drawSoloMask(); updateNetSidebar();
}

/* Cones */
function cone(kind){
  if(!currentSelection || currentSelection.kind!=='node') return;
  const crossFF = byId('chkCrossFF').checked;
  const acrossIO = byId('chkFanInAcrossIO').checked;
  const start = currentSelection.id;
  const keep = new Set([start]);

  const stopUp = id => {
    const t = MODEL.nodes.get(id)?.type;
    if (!acrossIO && t==='io' && MODEL.inputs.has(id)) return true;
    if (!crossFF && t==='ff' && id!==start) return true;
    return false;
  };
  const stopDown = id => {
    const t = MODEL.nodes.get(id)?.type;
    if (t==='io' && MODEL.outputs.has(id)) return true;
    if (!crossFF && t==='ff' && id!==start) return true;
    return false;
  };

  function walkUp(ids){
    const stack=[...ids], seen=new Set(ids);
    while(stack.length){
      const u=stack.pop();
      const preds=MODEL.pred.get(u)||new Set();
      for(const p of preds){
        if(seen.has(p)) continue;
        keep.add(p); seen.add(p);
        if(!stopUp(p)) stack.push(p);
      }
    }
  }
  function walkDown(ids){
    const stack=[...ids], seen=new Set(ids);
    while(stack.length){
      const u=stack.pop();
      const succs=MODEL.succ.get(u)||new Set();
      for(const s of succs){
        if(seen.has(s)) continue;
        keep.add(s); seen.add(s);
        if(!stopDown(s)) stack.push(s);
      }
    }
  }

  if (kind==='in') walkUp([start]); else walkDown([start]);

  const keepEdges=new Set();
  MODEL.edges.forEach(e=>{ if(keep.has(e.src)&&keep.has(e.dst)) keepEdges.add(e); });

  document.querySelectorAll('#nodes > g').forEach(el=>el.classList.toggle('dim', !keep.has(el.dataset.id)));
  const paths=byId('edges').querySelectorAll('.edge-path');
  paths.forEach((el,idx)=>{ const e=MODEL.edges[idx]; el.classList.toggle('dim', !keepEdges.has(e)); });

  const ffCount=[...keep].filter(id=>MODEL.nodes.get(id)?.type==='ff').length;
  byId('info').innerHTML = `<div><b>Included nodes:</b> ${keep.size} (FFs: ${ffCount})</div>`;
}

/* ==== Search + Fit ==== */
byId('btnFanIn').addEventListener('click',()=>cone('in'));
byId('btnFanOut').addEventListener('click',()=>cone('out'));
byId('btnClearHL').addEventListener('click',clearHighlight);
byId('btnClear').addEventListener('click',()=>{byId('search').value=''; filterText('');});
byId('search').addEventListener('input',e=>filterText(e.target.value));
byId('btnFit').addEventListener('click', fitToView);

function filterText(q){
  q=(q||'').toLowerCase();
  document.querySelectorAll('#nodes > g').forEach(el=>{
    const n=MODEL.nodes.get(el.dataset.id);
    const hit = !q || n.id.toLowerCase().includes(q) || (n.label||'').toLowerCase().includes(q);
    el.classList.toggle('dim', !hit);
  });
}

/* Net color controls + Solo */
byId('btnColorNet').addEventListener('click',()=>{ if(currentSelection?.kind==='edge'){ cycleNetColor(currentSelection.edge.net||''); } });
byId('btnResetColors').addEventListener('click', resetNetColors);
byId('btnSoloNet').addEventListener('click',()=>{ if(currentSelection?.kind==='edge'){ setSoloNet(currentSelection.edge.net||''); } });

/* Follow across IOBUF toggle affects bridges */
byId('chkFollowIOBUF').addEventListener('change', ()=>{
  if(!soloNet){ bridgedNets.clear(); styleBridgedEdges(); drawSoloMask(); return; }
  updateBridgedNets(); styleBridgedEdges(); drawSoloMask(); updateNetSidebar();
});

function updateBridgedNets(){
  bridgedNets.clear();
  if(!soloNet) return;
  if(byId('chkFollowIOBUF').checked){
    // RECURSIVE bridging through any number of IOBUFs
    netsAcrossIOBUFFromNet(soloNet).forEach(n=>bridgedNets.add(n));
  }
}

/* Sidebar for selected net */
function updateNetSidebar(){
  const info = byId('info');
  if(!soloNet){ info.textContent=''; return; }
  const drivers=new Set(), loads=new Set();
  MODEL.edges.forEach(e=>{ if(e.net===soloNet){ drivers.add(e.src); loads.add(e.dst);} });

  updateBridgedNets();

  let html = `<div><b>Net:</b> ${soloNet}</div>`;
  if(drivers.size){ html += `<div style="margin-top:.25rem;"><b>Drivers (${drivers.size}):</b><ul style="margin:.25rem 0 .25rem 1rem;">${[...drivers].map(id=>`<li>${id}</li>`).join('')}</ul></div>`; }
  if(loads.size){ html += `<div><b>Loads (${loads.size}):</b><ul style="margin:.25rem 0 .25rem 1rem;">${[...loads].map(id=>`<li>${id}</li>`).join('')}</ul></div>`; }
  if(bridgedNets.size){
    html += `<div><b>Bridged nets via IOBUF (recursive, ${bridgedNets.size}):</b><ul style="margin:.25rem 0 .25rem 1rem;">${[...bridgedNets].map(n=>`<li>${n}</li>`).join('')}</ul><small>Shown dashed; not merged with the main net.</small></div>`;
  }
  info.innerHTML = html;
}

/* ==== Pan/Zoom ==== */
(function enablePanZoom(){
  let vb=svg.viewBox.baseVal; const pt=svg.createSVGPoint();
  function clientToSVG(x,y){ pt.x=x; pt.y=y; const m=svg.getScreenCTM().inverse(); const p=pt.matrixTransform(m); return {x:p.x,y:p.y}; }
  svg.addEventListener('wheel',(e)=>{ e.preventDefault();
    const scale=(e.deltaY<0)?0.9:1.1; const c=clientToSVG(e.clientX,e.clientY);
    const newW=vb.width*scale, newH=vb.height*scale;
    const kx=(c.x - vb.x)/vb.width, ky=(c.y - vb.y)/vb.height;
    vb.x=c.x - kx*newW; vb.y=c.y - ky*newH; vb.width=newW; vb.height=newH; }, {passive:false});
  let dragging=false, start={x:0,y:0}, vb0={x:0,y:0};
  svg.addEventListener('mousedown',(e)=>{ if(e.button!==0) return; dragging=true; start={x:e.clientX,y:e.clientY}; vb0={x:vb.x,y:vb.y}; });
  window.addEventListener('mousemove',(e)=>{ if(!dragging) return; const p0=clientToSVG(start.x,start.y); const p1=clientToSVG(e.clientX,e.clientY);
    vb.x=vb0.x - (p1.x - p0.x); vb.y=vb0.y - (p1.y - p0.y); });
  window.addEventListener('mouseup',()=>dragging=false);
})();
function fitToView(){ const bbox=svg.getBBox(); const pad=80; const vb=svg.viewBox.baseVal;
  vb.x=Math.max(0,bbox.x - pad); vb.y=Math.max(0,bbox.y - pad); vb.width=bbox.width+2*pad; vb.height=bbox.height+2*pad; }

function summarize(){ const n=MODEL.nodes.size, e=MODEL.edges.length; byId('stats').innerHTML = `nodes=${n} edges=${e}`; }

/* ==== Keyboard ==== */
window.addEventListener('keydown',(e)=>{
  if (e.key==='x' || e.key==='X'){ cone('in'); e.preventDefault(); }
  else if (e.key==='f' || e.key==='F'){ cone('out'); e.preventDefault(); }
  else if (e.key==='c' || e.key==='C'){ clearHighlight(); e.preventDefault(); }
  else if (e.key==='0'){ fitToView(); e.preventDefault(); }
  else if (e.key==='n' || e.key==='N'){ if(currentSelection?.kind==='edge'){ cycleNetColor(currentSelection.edge.net||''); e.preventDefault(); } }
  else if (e.key==='r' || e.key==='R'){ resetNetColors(); e.preventDefault(); }
  else if (e.key==='s' || e.key==='S'){ if(currentSelection?.kind==='edge'){ setSoloNet(currentSelection.edge.net||''); e.preventDefault(); } }
});

/* ==== Boot ==== */
layoutAndRender();
fitToView();
