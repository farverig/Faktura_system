import os, json, sqlite3, secrets, hmac
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from starlette.middleware.sessions import SessionMiddleware
from reportlab.pdfgen import canvas

ROOT=Path(os.getenv("FAKTURA_DATA","data"))
ROOT.mkdir(parents=True,exist_ok=True)
DB=ROOT/"invoices.sqlite3"
PASSWORD=os.getenv("APP_PASSWORD")
SECRET=os.getenv("APP_SECRET")
if not PASSWORD or not SECRET: raise RuntimeError("Set APP_PASSWORD and APP_SECRET")
app=FastAPI(docs_url=None,redoc_url=None)
app.add_middleware(SessionMiddleware,secret_key=SECRET,same_site="strict",https_only=os.getenv("HTTPS_ONLY")=="1")
def db():
 c=sqlite3.connect(DB,timeout=30,isolation_level=None)
 c.row_factory=sqlite3.Row
 c.execute("PRAGMA busy_timeout=30000")
 return c
with db() as c:
 c.executescript("""CREATE TABLE IF NOT EXISTS invoices(id INTEGER PRIMARY KEY,number INTEGER UNIQUE,status TEXT NOT NULL,payload TEXT NOT NULL,pdf BLOB);
 CREATE TABLE IF NOT EXISTS sequence(id INTEGER PRIMARY KEY CHECK(id=1),next_number INTEGER NOT NULL);
 INSERT OR IGNORE INTO sequence VALUES(1,1);
 CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1),payload TEXT NOT NULL);""")
 c.execute("INSERT OR IGNORE INTO settings VALUES(1,?)",(json.dumps({"name":"Farverig I/S","cvr":"45413721","address":"Vesterbrogade 98D, 1620 København V","bank":"Lunar","reg":"6695","account":"2001097701","email":"farverigCPH@gmail.com"}),))
def get_settings():
 with db() as c:return json.loads(c.execute("SELECT payload FROM settings WHERE id=1").fetchone()[0])
def auth(r):
 if not r.session.get("ok"):raise HTTPException(401,"Log ind først")
def verify(r,f):
 auth(r)
 if not hmac.compare_digest(str(f.get("csrf","")),str(r.session.get("csrf",""))):raise HTTPException(403,"Ugyldig formularnøgle")
def esc(s):
 import html
 return html.escape(str(s or ""),quote=True)
def layout(r,body):
 token=esc(r.session.get("csrf",""))
 return HTMLResponse("""<!doctype html><html lang="da"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Farverig Faktura</title><style>
 :root{font-family:Inter,system-ui,Arial,sans-serif;color:#1c2330;background:#f6f7f9}*{box-sizing:border-box}body{margin:0}
 header{background:white;border-bottom:1px solid #e5e7eb;padding:18px max(20px,calc((100vw - 1000px)/2));display:flex;justify-content:space-between;align-items:center}
 main{max-width:1000px;margin:45px auto;padding:0 20px}h1{font-size:30px;letter-spacing:-1px}h2{font-size:20px}
 .card{background:white;border:1px solid #e5e7eb;border-radius:16px;padding:26px;margin:18px 0;box-shadow:0 4px 18px #15203008}
 a{color:#284c78;text-decoration:none}a:hover{text-decoration:underline}button,.btn{background:#182c45;color:white;border:0;padding:11px 18px;border-radius:9px;cursor:pointer;display:inline-block;font:inherit}
 .muted{color:#64748b}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}label{display:block;font-size:13px;color:#475569;margin:12px 0 4px}
 input,textarea,select{width:100%;padding:11px;border:1px solid #cbd5e1;border-radius:8px;font:inherit;background:white}
 textarea{min-height:72px}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:13px 8px;border-bottom:1px solid #e5e7eb}
 .actions{display:flex;gap:10px;flex-wrap:wrap;align-items:center}form.inline{display:inline}.btn-light{background:#e8edf3;color:#24354b}
 @media(max-width:650px){.grid{grid-template-columns:1fr}table{font-size:13px}th,td{padding:8px 3px}}
 </style><header><strong>FARVERIG <span class="muted">/ Faktura</span></strong><nav><a href="/">Oversigt</a> &nbsp; <a href="/settings">Indstillinger</a> &nbsp; <form class="inline" action="/logout" method="post"><input type="hidden" name="csrf" value=""""+token+""""><button class="btn-light">Log ud</button></form></nav></header><main>"""+body+"</main></html>")
def amount(v):
 return Decimal(str(v).replace(",","." )).quantize(Decimal(".01"),rounding=ROUND_HALF_UP)
def totals(d):
 net=Decimal(0);vat=Decimal(0)
 for x in d["lines"]:
  a=(amount(x["qty"])*amount(x["price"])).quantize(Decimal(".01"),rounding=ROUND_HALF_UP)
  net+=a;vat+=(a*amount(x["vat"])/100).quantize(Decimal(".01"),rounding=ROUND_HALF_UP)
 return net,vat,net+vat
def fmt(x):return f"{x:,.2f}".replace(",","X").replace(".",",").replace("X",".")
def get_invoice(i):
 with db() as c:r=c.execute("SELECT * FROM invoices WHERE id=?",(i,)).fetchone()
 if r is None:raise HTTPException(404)
 return r
@app.get("/login")
def login(r:Request):
 return HTMLResponse('<html lang="da"><meta charset="utf-8"><body style="font:16px system-ui;max-width:360px;margin:100px auto"><h1>Farverig Faktura</h1><form method="post"><label>Adgangskode</label><input type="password" name="password" required><button>Log ind</button></form></body></html>')
@app.post("/login")
async def login_post(r:Request):
 f=await r.form()
 if not hmac.compare_digest(str(f.get("password","")),PASSWORD):raise HTTPException(401,"Forkert adgangskode")
 r.session.clear();r.session["ok"]=True;r.session["csrf"]=secrets.token_urlsafe(32)
 return RedirectResponse("/",303)
@app.post("/logout")
async def logout(r:Request):
 f=await r.form();verify(r,f);r.session.clear();return RedirectResponse("/login",303)
@app.get("/")
def home(r:Request):
 auth(r)
 with db() as c:rows=c.execute("SELECT id,number,status,payload FROM invoices ORDER BY id DESC").fetchall()
 body='<div class="actions" style="justify-content:space-between"><h1>Fakturaer</h1><a class="btn" href="/new">+ Ny faktura</a></div><div class="card"><table><tr><th>Nummer</th><th>Kunde</th><th>Status</th><th>Total</th><th>Handlinger</th></tr>'
 for x in rows:
  d=json.loads(x["payload"]);total=fmt(totals(d)[2]);i=x["id"]
  actions=(f'<a href="/invoice/{i}/edit">Redigér</a>' if x["status"]=="draft" else f'<a href="/invoice/{i}/pdf">PDF</a>')
  actions+=f' &nbsp; <form class="inline" method="post" action="/invoice/{i}/copy"><input type="hidden" name="csrf" value="{esc(r.session["csrf"])}"><button class="btn-light">Kopiér</button></form>'
  body+=f'<tr><td>{x["number"] or "Kladde"}</td><td>{esc(d["customer"])}</td><td>{esc(x["status"])}</td><td>{total} kr.</td><td>{actions}</td></tr>'
 return layout(r,body+"</table></div>")
def blank():
 return {"customer":"","customer_address":"","customer_cvr":"","issue_date":date.today().isoformat(),"due_date":(date.today()+timedelta(days=8)).isoformat(),"description":"","lines":[{"name":"","qty":"1","price":"0","vat":"25"}]}
def editor(r,d,i=None):
 auth(r)
 fields=[("customer","Kundens navn"),("customer_address","Kundens adresse"),("customer_cvr","Kundens CVR (valgfrit)"),("issue_date","Fakturadato"),("due_date","Forfaldsdato"),("description","Beskrivelse")]
 form=f'<h1>{"Redigér kladde" if i else "Ny faktura"}</h1><form action="/save" method="post"><input type="hidden" name="csrf" value="{esc(r.session["csrf"])}"><input type="hidden" name="id" value="{i or ""}"><div class="card"><h2>Kunde og datoer</h2><div class="grid">'
 for k,title in fields:
  form+=f'<div><label>{title}</label><input name="{k}" value="{esc(d.get(k,""))}" {"type=date" if k.endswith("date") else ""} required></div>'
 form+='</div></div><div class="card"><h2>Ydelser</h2><p class="muted">Tilføj flere linjer efter behov.</p><div id="lines">'
 for x in d["lines"]:
  form+=line_html(x)
 form+='</div><button type="button" class="btn-light" onclick="addLine()">+ Tilføj linje</button></div><button>Gem kladde</button></form>'
 if i:
  form+=f'<form method="post" action="/invoice/{i}/issue" class="card"><input type="hidden" name="csrf" value="{esc(r.session["csrf"])}"><p>Kontrollér alle oplysninger før udstedelse. Udstedte fakturaer kan ikke ændres.</p><button>Udsted faktura</button></form>'
 form+='''<script>function addLine(){const e=document.querySelector("#lines .grid");if(e)document.getElementById("lines").insertAdjacentHTML("beforeend",e.outerHTML.replaceAll(/value="[^"]*"/g,'value=""'));}</script>'''
 return layout(r,form)
def line_html(x):
 return '<div class="grid" style="grid-template-columns:2fr 1fr 1fr 1fr;align-items:end;margin:12px 0">'+''.join(f'<div><label>{label}</label><input name="{key}" value="{esc(x.get(key,""))}" required></div>' for key,label in [("name","Ydelse"),("qty","Antal"),("price","Stykpris"),("vat","Moms % (0/25)")])+'</div>'
@app.get("/new")
def new(r:Request):return editor(r,blank())
@app.get("/invoice/{i}/edit")
def edit(r:Request,i:int):
 auth(r);x=get_invoice(i)
 if x["status"]!="draft":raise HTTPException(409,"Udstedt faktura kan ikke redigeres")
 return editor(r,json.loads(x["payload"]),i)
@app.post("/save")
async def save(r:Request):
 f=await r.form();verify(r,f)
 d={k:str(f.get(k,"")).strip() for k in ("customer","customer_address","customer_cvr","issue_date","due_date","description")}
 if not d["customer"] or not d["customer_address"]:raise HTTPException(400,"Kunde og adresse kræves")
 try:
  issued=date.fromisoformat(d["issue_date"]);due=date.fromisoformat(d["due_date"])
  if due<issued:raise ValueError()
 except ValueError:raise HTTPException(400,"Ugyldige datoer")
 names=f.getlist("name");qty=f.getlist("qty");prices=f.getlist("price");vats=f.getlist("vat")
 if not 1<=len(names)<=100 or len({len(names),len(qty),len(prices),len(vats)})!=1:raise HTTPException(400,"Ugyldige linjer")
 d["lines"]=[]
 for n,q,p,v in zip(names,qty,prices,vats):
  try:
   q=amount(q);p=amount(p);v=amount(v)
   if q<=0 or q>100000 or p<0 or p>100000000 or v not in (0,25):raise ValueError()
  except Exception:raise HTTPException(400,"Ugyldig pris, antal eller moms")
  if n.strip():d["lines"].append({"name":n.strip()[:250],"qty":str(q),"price":str(p),"vat":str(v)})
 if not d["lines"]:raise HTTPException(400,"Mindst én ydelse kræves")
 i=int(f.get("id") or 0)
 with db() as c:
  c.execute("BEGIN IMMEDIATE")
  if i:
   x=c.execute("SELECT status FROM invoices WHERE id=?",(i,)).fetchone()
   if not x or x["status"]!="draft":raise HTTPException(409,"Kun kladder kan redigeres")
   c.execute("UPDATE invoices SET payload=? WHERE id=?",(json.dumps(d),i))
  else:i=c.execute("INSERT INTO invoices(status,payload) VALUES('draft',?)",(json.dumps(d),)).lastrowid
  c.commit()
 return RedirectResponse(f"/invoice/{i}/edit",303)
@app.post("/invoice/{i}/copy")
async def copy(r:Request,i:int):
 f=await r.form();verify(r,f);d=json.loads(get_invoice(i)["payload"])
 d["issue_date"]=date.today().isoformat();d["due_date"]=(date.today()+timedelta(days=8)).isoformat()
 with db() as c:newid=c.execute("INSERT INTO invoices(status,payload) VALUES('draft',?)",(json.dumps(d),)).lastrowid
 return RedirectResponse(f"/invoice/{newid}/edit",303)
def make_pdf(number,d,s):
 b=BytesIO();p=canvas.Canvas(b,pagesize=(595,842))
 def t(x,y,v,size=10):
  p.setFont("Helvetica",size);p.drawString(x,y,str(v).encode("latin-1","replace").decode("latin-1"))
 t(45,785,s["name"],22);t(45,730,d["customer"],12);t(45,711,d["customer_address"]);t(45,690,"CVR: "+d["customer_cvr"])
 t(365,780,"FAKTURA "+str(number),17);t(365,750,"Dato: "+d["issue_date"]);t(365,732,"Forfald: "+d["due_date"])
 p.line(45,650,550,650);t(45,628,"YDELSE");t(300,628,"ANTAL");t(390,628,"PRIS");t(480,628,"I ALT")
 y=598
 for x in d["lines"]:
  if y<240:p.showPage();y=790
  t(45,y,x["name"][:38]);t(300,y,x["qty"]);t(390,y,fmt(amount(x["price"])));t(480,y,fmt(amount(x["qty"])*amount(x["price"])))
  y-=34
 net,vat,total=totals(d);y=min(y-20,300)
 t(370,y,"Subtotal");t(480,y,fmt(net));t(370,y-24,"Moms");t(480,y-24,fmt(vat));t(370,y-54,"TOTAL DKK",12);t(480,y-54,fmt(total),12)
 t(45,125,"BETALING",14);t(45,103,s["bank"]+"  Reg. "+s["reg"]+"  Konto "+s["account"])
 t(45,84,"Angiv fakturanr. "+str(number)+" ved betaling")
 t(45,45,s["name"]+"  |  "+s["address"]);t(45,28,"CVR "+s["cvr"]+"  |  "+s["email"])
 p.save();return b.getvalue()
@app.post("/invoice/{i}/issue")
async def issue(r:Request,i:int):
 f=await r.form();verify(r,f)
 with db() as c:
  c.execute("BEGIN IMMEDIATE")
  x=c.execute("SELECT status,payload FROM invoices WHERE id=?",(i,)).fetchone()
  if not x or x["status"]!="draft":raise HTTPException(409,"Faktura ikke en kladde")
  n=c.execute("SELECT next_number FROM sequence WHERE id=1").fetchone()[0]
  pdf=make_pdf(n,json.loads(x["payload"]),get_settings())
  c.execute("UPDATE sequence SET next_number=? WHERE id=1",(n+1,))
  c.execute("UPDATE invoices SET number=?,status='issued',pdf=? WHERE id=?",(n,pdf,i))
  c.commit()
 return RedirectResponse("/",303)
@app.get("/invoice/{i}/pdf")
def pdf(r:Request,i:int):
 auth(r);x=get_invoice(i)
 if x["status"]!="issued":raise HTTPException(409)
 return Response(x["pdf"],media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="Faktura-{x["number"]}.pdf"'})
@app.get("/settings")
def settings(r:Request):
 auth(r);s=get_settings();body='<h1>Firmaoplysninger</h1><form class="card" method="post"><input type="hidden" name="csrf" value="'+esc(r.session["csrf"])+'">'
 for k,title in [("name","Firmanavn"),("cvr","CVR"),("address","Adresse"),("bank","Bank"),("reg","Registreringsnummer"),("account","Kontonummer"),("email","E-mail")]:
  body+=f'<label>{title}</label><input name="{k}" value="{esc(s.get(k,""))}" required>'
 return layout(r,body+'<p><button>Gem oplysninger</button></p></form>')
@app.post("/settings")
async def settings_post(r:Request):
 f=await r.form();verify(r,f)
 s={k:str(f.get(k,"")).strip()[:250] for k in ("name","cvr","address","bank","reg","account","email")}
 if not all(s.values()):raise HTTPException(400,"Udfyld alle felter")
 with db() as c:c.execute("UPDATE settings SET payload=? WHERE id=1",(json.dumps(s),))
 return RedirectResponse("/settings",303)
