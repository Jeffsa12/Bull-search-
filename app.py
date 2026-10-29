from flask import Flask, render_template, jsonify, request
import requests, re, time
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse, parse_qs

app=Flask(__name__)
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; GenealogiaLechera/2.0; educational research)"}
CACHE={}; TTL=86400

# Demo verificable y respaldo si una web cambia su estructura.
DEMO={"007HO16276":{"code":"007HO16276","name":"OCD TROOPER SHEEPSTER-ET","breed":"Holstein","proof":"Consulta de demostración","metrics":{"milk":1217,"fat":130,"protein":64,"nm":1080,"reliability":99},"pedigree":{"name":"OCD TROOPER SHEEPSTER-ET","role":"Toro evaluado","sex":"M","metrics":{"milk":1217,"fat":130,"protein":64,"nm":1080},"parents":[{"name":"PLAIN-KNOLL RENEGAD TROOPER","role":"Padre","sex":"M","metrics":{"milk":666,"fat":88,"protein":51,"nm":651},"parents":[]},{"name":"OCD ACURA SOY 60075-ET","role":"Madre","sex":"F","metrics":{},"parents":[{"name":"PINE-TREE ACURA-ET","role":"Abuelo materno","sex":"M","metrics":{"milk":1669,"fat":73,"protein":58,"nm":765},"parents":[]},{"name":"OCD RESOLVE SOY 44814-ET","role":"Abuela materna","sex":"F","metrics":{},"parents":[]}]}]},"sources":["https://www.accelgen.com/","https://www.naab-css.org/genomic-bull-database"]}}

def clean_code(code):
    code=re.sub(r'[^0-9A-Z]','',code.upper())
    if not re.fullmatch(r'\d{3}[A-Z]{2}\d{5}',code): raise ValueError('Use un código NAAB como 007HO16276')
    return code

def get(url, timeout=15):
    r=requests.get(url,headers=HEADERS,timeout=timeout); r.raise_for_status(); return r

def ddg_links(query):
    html=get('https://html.duckduckgo.com/html/?q='+quote(query)).text
    soup=BeautifulSoup(html,'html.parser'); out=[]
    for a in soup.select('a.result__a'):
        href=a.get('href','')
        if 'uddg=' in href: href=parse_qs(urlparse(href).query).get('uddg',[href])[0]
        if href.startswith('http'): out.append(href)
    return out[:8]

def num(text, patterns):
    for p in patterns:
        m=re.search(p,text,re.I)
        if m:
            try:return float(m.group(1).replace(',',''))
            except: pass
    return None

def extract_page(url, code):
    html=get(url).text; soup=BeautifulSoup(html,'html.parser')
    text=' '.join(soup.stripped_strings); title=soup.title.get_text(' ',strip=True) if soup.title else ''
    name=None
    patterns=[rf'{re.escape(code)}\s+([A-Z0-9][A-Z0-9\- ]{{5,45}}(?:-ET)?)',r'(?:Name|Registered Name)\s*[:\-]?\s*([A-Z0-9][A-Z0-9\- ]{5,45})']
    for p in patterns:
        m=re.search(p,text,re.I)
        if m: name=m.group(1).strip(' -|'); break
    if not name:
        name=re.sub(r'\s*[-|].*','',title).strip() or code
    metrics={
      'milk':num(text,[r'(?:PTA\s*)?Milk\s*[:+]?\s*([\-\d,]+)',r'([\-\d,]+)\s*(?:lb)?\s+Milk']),
      'fat':num(text,[r'(?:PTA\s*)?Fat\s*[:+]?\s*([\-\d,]+)']),
      'protein':num(text,[r'(?:PTA\s*)?Protein\s*[:+]?\s*([\-\d,]+)']),
      'nm':num(text,[r'(?:NM\$|Net Merit)\s*[:+$]?\s*([\-\d,]+)']),
      'reliability':num(text,[r'(?:REL|Reliability)\s*[:]?\s*(\d{1,3})\s*%'])}
    sire=dam=None
    for label,key in [('Sire','sire'),('Father','sire'),('Dam','dam'),('Mother','dam')]:
        m=re.search(rf'\b{label}\b\s*[:\-]?\s*([A-Z0-9][A-Z0-9\- ]{{4,55}}?(?:-ET)?)(?=\s+(?:Sire|Dam|MGS|Mother|Father|Milk|PTA|NM\$)|$)',text,re.I)
        if m:
            if key=='sire' and not sire:sire=m.group(1).strip()
            if key=='dam' and not dam:dam=m.group(1).strip()
    parents=[]
    if sire:parents.append({'name':sire,'role':'Padre','sex':'M','metrics':{},'parents':[]})
    if dam:parents.append({'name':dam,'role':'Madre','sex':'F','metrics':{},'parents':[]})
    return {'code':code,'name':name,'breed':'Holstein' if 'Holstein' in text or code[3:5]=='HO' else code[3:5], 'proof':'Datos extraídos de fuente pública; valide fecha y base genética','metrics':metrics,'pedigree':{'name':name,'role':'Toro evaluado','sex':'M','metrics':metrics,'parents':parents},'sources':[url]}

def lookup_named_ancestor(name, role, sex, depth, visited):
    """Busca una ficha pública por nombre y completa antecesores recursivamente."""
    key=re.sub(r'[^A-Z0-9]','',name.upper())
    if depth <= 0 or not key or key in visited:
        return {'name':name,'role':role,'sex':sex,'metrics':{},'parents':[]}
    visited.add(key)
    links=[]
    try: links=ddg_links(f'"{name}" Holstein pedigree PTA sire dam')
    except Exception: pass
    for url in links[:5]:
        try:
            data=extract_page(url, '')
            node=data.get('pedigree',{})
            if node.get('parents') or any(v is not None for v in node.get('metrics',{}).values()):
                node['name']=name; node['role']=role; node['sex']=sex
                enriched=[]
                for p in node.get('parents',[]):
                    enriched.append(lookup_named_ancestor(p['name'],p.get('role','Antecesor'),p.get('sex','M'),depth-1,visited))
                node['parents']=enriched
                return node
        except Exception: pass
    return {'name':name,'role':role,'sex':sex,'metrics':{},'parents':[]}

def enrich_tree(node, depth, visited=None):
    visited=visited or set()
    if depth <= 0: node['parents']=[]; return node
    enriched=[]
    for p in node.get('parents',[]):
        found=lookup_named_ancestor(p['name'],p.get('role','Antecesor'),p.get('sex','M'),depth-1,visited)
        # Preserve better seed data where available
        found['metrics']={**found.get('metrics',{}),**p.get('metrics',{})}
        if p.get('parents') and not found.get('parents'): found['parents']=enrich_tree(p,depth-1,visited).get('parents',[])
        enriched.append(found)
    node['parents']=enriched
    return node

def lookup(code):
    now=time.time()
    if code in CACHE and now-CACHE[code][0]<TTL:return CACHE[code][1]
    domains=['accelgen.com','naab-css.org','selectsires.com','holsteinusa.com']
    links=[]
    try: links=ddg_links(f'"{code}" Holstein bull pedigree PTA')
    except Exception: pass
    links=sorted(links,key=lambda u: next((i for i,d in enumerate(domains) if d in u),99))
    errors=[]
    for url in links:
        try:
            data=extract_page(url,code)
            if data['name'] and (any(v is not None for v in data['metrics'].values()) or data['pedigree']['parents']):
                CACHE[code]=(now,data); return data
        except Exception as e: errors.append(str(e)[:100])
    if code in DEMO:
        data=dict(DEMO[code]); data['warning']='No fue posible actualizar las páginas en vivo; se muestra el respaldo local.'
        return data
    raise LookupError('No se halló una ficha pública estructurada para este código. Pruebe una URL directa de la ficha.')

@app.route('/')
def home(): return render_template('index.html')
@app.route('/api/bull/<code>')
def bull(code):
    try:
        depth=max(1,min(int(request.args.get('depth',6)),8))
        data=lookup(clean_code(code))
        data['pedigree']=enrich_tree(data['pedigree'],depth)
        data['requested_depth']=depth
        return jsonify(data)
    except ValueError as e:return jsonify(error=str(e)),400
    except Exception as e:return jsonify(error=str(e)),404
@app.route('/api/from-url')
def from_url():
    try:
        code=clean_code(request.args.get('code','')); url=request.args.get('url','')
        if urlparse(url).scheme not in ('http','https'):raise ValueError('URL no válida')
        return jsonify(extract_page(url,code))
    except Exception as e:return jsonify(error=str(e)),400
if __name__=='__main__': app.run(host='0.0.0.0',port=5000,debug=True)
