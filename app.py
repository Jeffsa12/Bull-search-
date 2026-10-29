from flask import Flask, jsonify, render_template_string
import os, re
app = Flask(__name__)
DATA={"007HO16276":{"code":"007HO16276","name":"OCD TROOPER SHEEPSTER-ET","breed":"Holstein","metrics":{"milk":1217,"fat":130,"protein":64,"nm":1080,"reliability":99},"pedigree":{"name":"OCD TROOPER SHEEPSTER-ET","role":"Toro evaluado","sex":"M","metrics":{"milk":1217,"fat":130,"protein":64,"nm":1080},"parents":[{"name":"PLAIN-KNOLL RENEGAD TROOPER","role":"Padre","sex":"M","metrics":{"milk":666,"fat":88,"protein":51,"nm":651},"parents":[]},{"name":"OCD ACURA SOY 60075-ET","role":"Madre","sex":"F","metrics":{},"parents":[{"name":"PINE-TREE ACURA-ET","role":"Abuelo materno","sex":"M","metrics":{"milk":1669,"fat":73,"protein":58,"nm":765},"parents":[]},{"name":"OCD RESOLVE SOY 44814-ET","role":"Abuela materna","sex":"F","metrics":{},"parents":[]}]}]}}}
HTML='''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Genealogia lechera</title><style>body{margin:0;background:#07111f;color:#eef7ff;font:15px Arial}main{max-width:1400px;margin:auto;padding:25px}.search{display:flex;gap:10px}input,select,button{padding:12px;border-radius:9px}.wrap{overflow:auto;margin-top:18px}.tree{display:flex;gap:30px;min-width:1000px}.gen{width:280px}.card{background:#10243a;border-left:5px solid #25d0e8;border-radius:12px;padding:12px;margin:10px 0}.f{border-color:#bca7ff}.chips{display:grid;grid-template-columns:1fr 1fr;gap:5px}.chip{background:#071523;padding:6px}.muted{color:#9eb4c8}.error{background:#4b1d25;padding:12px;border-radius:10px}</style></head><body><main><h1>Genealogia lechera</h1><p class="muted">Estado del servidor: <a href="/health" style="color:#6eddec">/health</a></p><div class="search"><input id="code" value="007HO16276"><select id="depth"><option>4</option><option>5</option><option selected>6</option><option>7</option><option>8</option></select><button onclick="loadData()">Consultar</button></div><div id="status"></div><div id="result"></div></main><script>
const f=v=>v==null?'N/D':(v>0?'+':'')+Number(v).toLocaleString('es-CO');
function levels(root,max){let a=[[root]];for(let i=1;i<max;i++){let n=a[i-1].flatMap(x=>x.parents||[]);if(!n.length)break;a.push(n)}return a}
function card(n){let m=n.metrics||{};return `<article class="card ${n.sex==='F'?'f':''}"><b>${n.name}</b><div class="muted">${n.role||''}</div><div class="chips"><div class="chip">Leche: ${f(m.milk)}</div><div class="chip">Grasa: ${f(m.fat)}</div><div class="chip">Proteina: ${f(m.protein)}</div><div class="chip">NM$: ${f(m.nm)}</div></div></article>`}
async function loadData(){let c=code.value.trim(),d=Number(depth.value);status.textContent='Consultando...';try{let r=await fetch('/api/bull/'+encodeURIComponent(c));let x=await r.json();if(!r.ok)throw Error(x.error);let lv=levels(x.pedigree,d);result.innerHTML=`<h2>${x.name}</h2><div class="wrap"><div class="tree">${lv.map((g,i)=>`<section class="gen"><h3>Generacion ${i+1}</h3>${g.map(card).join('')}</section>`).join('')}</div></div>`;status.textContent='Consulta completada'}catch(e){status.textContent='';result.innerHTML=`<div class="error">${e.message}</div>`}}loadData();
</script></body></html>'''
@app.get('/')
def home(): return render_template_string(HTML)
@app.get('/health')
def health(): return jsonify(status='ok',service='genealogia-lechera')
@app.get('/api/bull/<code>')
def bull(code):
    safe=re.sub(r'[^0-9A-Z]','',code.upper())
    if not re.fullmatch(r'\d{3}[A-Z]{2}\d{5}',safe): return jsonify(error='Codigo NAAB invalido'),400
    if safe not in DATA: return jsonify(error='Servidor activo, pero el codigo aun no esta cargado'),404
    return jsonify(DATA[safe])
@app.errorhandler(Exception)
def fail(e):
    app.logger.exception('Unhandled error')
    return jsonify(error='Error interno. Revise los logs de Render.'),500
if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.environ.get('PORT','5000')))
