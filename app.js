'use strict';
const KEY='farverig-invoices-v1', SETTINGS='farverig-settings-v1';
const $=s=>document.querySelector(s), app=$('#app');
const escapeHTML=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money=v=>new Intl.NumberFormat('da-DK',{minimumFractionDigits:2,maximumFractionDigits:2}).format(Number(v)||0);
const today=()=>new Date().toLocaleDateString('sv-SE');
const plusDays=n=>{const d=new Date();d.setDate(d.getDate()+n);return d.toLocaleDateString('sv-SE')};
const defaults={name:'Farverig I/S',cvr:'45413721',address:'Vesterbrogade 98D, 1620 København V',email:'farverigCPH@gmail.com',bank:'',reg:'',account:'',nextNumber:1};
let settings=load(SETTINGS,defaults),invoices=load(KEY,[]),editing=null;
function load(k,f){try{const x=JSON.parse(localStorage.getItem(k));return x??structuredClone(f)}catch{return structuredClone(f)}}
function save(){localStorage.setItem(KEY,JSON.stringify(invoices));localStorage.setItem(SETTINGS,JSON.stringify(settings))}
function toast(t){$('#toast').textContent=t;$('#toast').style.display='block';setTimeout(()=>$('#toast').style.display='none',3000)}
function total(d){let net=0,vat=0;for(const l of d.lines){const a=Math.round(Number(l.qty)*Number(l.price)*100);net+=a;vat+=Math.round(a*Number(l.vat)/100)}return {net:net/100,vat:vat/100,gross:(net+vat)/100}}
function field(name,label,value='',type='text'){return '<div class="field"><label for="'+name+'">'+label+'</label><input id="'+name+'" name="'+name+'" type="'+type+'" value="'+escapeHTML(value)+'" required></div>'}
function shell(title,subtitle,action=''){return '<div class="heading"><div><div class="eyebrow">'+subtitle+'</div><h1>'+title+'</h1></div>'+action+'</div>'}
function view(name){document.querySelectorAll('.nav').forEach(x=>x.classList.toggle('active',x.dataset.view===name));if(name==='overview')overview();if(name==='editor')editor();if(name==='settings')settingsView()}
document.querySelectorAll('.nav').forEach(b=>b.addEventListener('click',()=>view(b.dataset.view)));
function overview(){
 const issued=invoices.filter(x=>x.status==='issued'),due=issued.reduce((a,x)=>a+total(x).gross,0);
 let h=shell('Fakturaoversigt','Dit fakturastudio','<button class="btn primary" id="newBtn">+ Opret faktura</button>');
 h+='<div class="notice">Denne GitHub Pages-version gemmer kun oplysninger i <b>denne browsers lokale lager</b>. Den er ikke en sikker, synkroniseret database. Brug den ikke som eneste opbevaring af rigtige fakturaer. Eksportér backup regelmæssigt.</div>';
 h+='<div class="stats"><div class="panel stat"><span>Udstedte fakturaer</span><strong>'+issued.length+'</strong></div><div class="panel stat"><span>Kladder</span><strong>'+invoices.filter(x=>x.status==='draft').length+'</strong></div><div class="panel stat"><span>Samlet faktureret inkl. moms</span><strong>'+money(due)+' kr.</strong></div></div>';
 h+='<div class="panel"><div class="toolbar"><h2>Alle fakturaer</h2><button class="btn" id="backupBtn">Eksportér backup</button></div>';
 if(!invoices.length)h+='<div class="empty"><h2>Din første faktura starter her</h2><p>Opret en kladde, tilføj ydelser og se fakturaen som PDF via Udskriv.</p><button class="btn primary" id="emptyNew">Opret faktura</button></div>';
 else{h+='<div class="tablewrap"><table><thead><tr><th>Nummer</th><th>Kunde</th><th>Dato</th><th>Beløb</th><th>Status</th><th>Handling</th></tr></thead><tbody>';
 for(const x of [...invoices].reverse())h+='<tr><td>'+(x.number??'—')+'</td><td>'+escapeHTML(x.customer)+'</td><td>'+escapeHTML(x.issueDate)+'</td><td>'+money(total(x).gross)+' kr.</td><td><span class="tag '+(x.status==='issued'?'issued':'')+'">'+(x.status==='issued'?'Udstedt':'Kladde')+'</span></td><td><button class="link" data-edit="'+escapeHTML(x.id)+'">'+(x.status==='issued'?'Vis / print':'Redigér')+'</button></td></tr>';
 h+='</tbody></table></div>'}h+='</div>';app.innerHTML=h;
 $('#newBtn').onclick=()=>editor();if($('#emptyNew'))$('#emptyNew').onclick=()=>editor();
 $('#backupBtn').onclick=exportBackup;document.querySelectorAll('[data-edit]').forEach(b=>b.onclick=()=>editor(b.dataset.edit));
}
function line(l={name:'',qty:1,price:0,vat:25}){return '<div class="linegrid">'+field('lineName','Beskrivelse',l.name)+field('qty','Antal',l.qty,'number')+field('price','Pris ekskl. moms',l.price,'number')+'<div class="field"><label>Moms</label><select name="vat"><option value="25" '+(Number(l.vat)===25?'selected':'')+'>25 %</option><option value="0" '+(Number(l.vat)===0?'selected':'')+'>0 %</option></select></div><button class="btn remove" type="button" title="Fjern linje">×</button></div>'}
function editor(id){
 editing=id??null;const d=invoices.find(x=>x.id===id)??{customer:'',customerAddress:'',customerCvr:'',issueDate:today(),dueDate:plusDays(8),notes:'',lines:[{name:'',qty:1,price:0,vat:25}],status:'draft'};
 const locked=d.status==='issued';
 let h=shell(locked?'Faktura '+d.number:(id?'Redigér kladde':'Ny faktura'),'Fakturering','<button class="btn" id="back">← Til oversigten</button>');
 h+='<form id="invoiceForm"><div class="panel"><h2>Kundeoplysninger</h2><div class="grid">'+field('customer','Kundens navn',d.customer)+field('customerCvr','CVR (valgfrit)',d.customerCvr)+field('customerAddress','Adresse',d.customerAddress)+field('issueDate','Fakturadato',d.issueDate,'date')+field('dueDate','Forfaldsdato',d.dueDate,'date')+'</div></div><div class="panel"><h2>Fakturalinjer</h2><div id="lines">'+d.lines.map(line).join('')+'</div><button class="btn" type="button" id="addLine">+ Tilføj linje</button></div><div class="panel"><h2>Bemærkning</h2><div class="field"><label for="notes">Besked på faktura</label><textarea id="notes" name="notes">'+escapeHTML(d.notes??'')+'</textarea></div><div class="summary" id="sum"></div></div>';
 h+='<div class="actions"><button class="btn primary" type="submit" id="saveBtn">Gem kladde</button><button class="btn" type="button" id="issueBtn">Udsted faktura</button><button class="btn" type="button" id="printBtn">Udskriv / Gem som PDF</button>';
 if(id&&d.status==='draft')h+='<button class="btn danger" type="button" id="deleteBtn">Slet kladde</button>';
 h+='</div></form><div class="space"></div>';app.innerHTML=h;$('#back').onclick=()=>view('overview');
 $('#addLine').onclick=()=>{$('#lines').insertAdjacentHTML('beforeend',line());bindLines()};
 bindLines();$('#invoiceForm').addEventListener('input',renderSum);
 if(locked){$('#invoiceForm').querySelectorAll('input,select,textarea').forEach(e=>e.disabled=true);$('#addLine').hidden=true;$('#saveBtn').hidden=true;$('#issueBtn').hidden=true;$('#invoiceForm').onsubmit=e=>e.preventDefault()}
 else{$('#invoiceForm').onsubmit=e=>{e.preventDefault();if(commit(false))toast('Kladde gemt')};$('#issueBtn').onclick=()=>{if(!confirm('Udsted faktura? Nummeret tildeles nu og fakturaen låses.'))return;if(commit(true)){toast('Faktura udstedt');view('overview')}}}
 $('#printBtn').onclick=()=>{if(!locked&&!commit(false))return;const x=invoices.find(x=>x.id===editing);printInvoice(x)};
 if($('#deleteBtn'))$('#deleteBtn').onclick=()=>{if(confirm('Slet denne kladde?')){invoices=invoices.filter(x=>x.id!==editing);save();view('overview')}};
 renderSum();
}
function bindLines(){document.querySelectorAll('.remove').forEach(b=>b.onclick=()=>{if(document.querySelectorAll('.linegrid').length>1){b.parentElement.remove();renderSum()}})}
function extract(){
 const f=$('#invoiceForm');if(!f.reportValidity())return null;
 const val=k=>f.elements.namedItem(k).value.trim();
 const lines=[...document.querySelectorAll('.linegrid')].map(row=>({name:row.querySelector('[name=lineName]').value.trim(),qty:Number(row.querySelector('[name=qty]').value),price:Number(row.querySelector('[name=price]').value),vat:Number(row.querySelector('[name=vat]').value)}));
 if(lines.some(l=>!l.name||!Number.isFinite(l.qty)||l.qty<=0||!Number.isFinite(l.price)||l.price<0||![0,25].includes(l.vat))){alert('Kontrollér fakturalinjerne.');return null}
 if(val('dueDate')<val('issueDate')){alert('Forfaldsdato må ikke ligge før fakturadato.');return null}
 return {customer:val('customer'),customerAddress:val('customerAddress'),customerCvr:val('customerCvr'),issueDate:val('issueDate'),dueDate:val('dueDate'),notes:val('notes'),lines}
}
function commit(issue){
 const d=extract();if(!d)return false;
 let x=invoices.find(x=>x.id===editing);
 if(x&&x.status==='issued')return false;
 if(!x){x={id:crypto.randomUUID(),status:'draft'};invoices.push(x);editing=x.id}
 Object.assign(x,d);
 if(issue){x.status='issued';x.number=Number(settings.nextNumber)||1;settings.nextNumber=x.number+1;x.issuedAt=new Date().toISOString();x.company=structuredClone(settings)}
 try{save()}catch(e){alert('Kunne ikke gemme i browseren. Eksportér data og kontrollér lagerplads.');return false}
 if(!issue)editor(x.id);return true
}
function renderSum(){
 const lines=[...document.querySelectorAll('.linegrid')].map(r=>({qty:Number(r.querySelector('[name=qty]').value)||0,price:Number(r.querySelector('[name=price]').value)||0,vat:Number(r.querySelector('[name=vat]').value)||0}));
 const t=total({lines});$('#sum').innerHTML='<table><tr><td>Subtotal</td><td>'+money(t.net)+' kr.</td></tr><tr><td>Moms</td><td>'+money(t.vat)+' kr.</td></tr><tr><td>Total</td><td>'+money(t.gross)+' kr.</td></tr></table>';
}
function printInvoice(x){
 if(!x)return;
 const s=x.company??settings,t=total(x);
 document.querySelectorAll('.invoiceprint').forEach(n=>n.remove());
 const el=document.createElement('section');el.className='invoiceprint';
 el.innerHTML='<div class="printtop"><div><img class="printlogo" src="./assets/logo.png" onerror="this.style.display=\'none\'"><h2>'+escapeHTML(s.name)+'</h2><p>'+escapeHTML(s.address)+'</p><p>CVR '+escapeHTML(s.cvr)+'</p></div><div><h1>FAKTURA '+escapeHTML(x.number??'KLADDE')+'</h1><p>Dato: '+escapeHTML(x.issueDate)+'</p><p>Forfald: '+escapeHTML(x.dueDate)+'</p></div></div><div style="margin-top:40px"><b>FAKTURERES TIL</b><p>'+escapeHTML(x.customer)+'</p><p>'+escapeHTML(x.customerAddress)+'</p>'+(x.customerCvr?'<p>CVR '+escapeHTML(x.customerCvr)+'</p>':'')+'</div><table class="printtable"><thead><tr><th>Beskrivelse</th><th>Antal</th><th>Pris</th><th>Moms</th><th>Beløb</th></tr></thead><tbody>'+x.lines.map(l=>'<tr><td>'+escapeHTML(l.name)+'</td><td>'+escapeHTML(l.qty)+'</td><td>'+money(l.price)+'</td><td>'+l.vat+' %</td><td>'+money(l.qty*l.price)+'</td></tr>').join('')+'</tbody></table><table class="printtotal"><tr><td>Subtotal</td><td>'+money(t.net)+'</td></tr><tr><td>Moms</td><td>'+money(t.vat)+'</td></tr><tr><td><b>Total DKK</b></td><td><b>'+money(t.gross)+'</b></td></tr></table><div class="printfooter"><b>Betalingsoplysninger</b><p>'+escapeHTML(s.bank)+' '+escapeHTML(s.reg)+' '+escapeHTML(s.account)+'</p><p>'+escapeHTML(x.notes??'')+'</p><p>'+escapeHTML(s.email)+'</p></div>';
 document.body.append(el);setTimeout(()=>window.print(),150)
}
function settingsView(){
 let h=shell('Indstillinger','Virksomhed og backup');
 h+='<div class="notice">Indstillinger gemmes kun på denne enhed. Før første faktura skal du kontrollere firmanavn, CVR, betalingsoplysninger og næste fakturanummer. Dette er ikke en sikker fælles database.</div><form id="settingsForm" class="panel"><h2>Virksomhedsoplysninger</h2><div class="grid">';
 for(const [k,l] of [['name','Firmanavn'],['cvr','CVR'],['address','Adresse'],['email','E-mail'],['bank','Bank'],['reg','Registreringsnummer'],['account','Kontonummer'],['nextNumber','Næste fakturanummer']])h+=field(k,l,settings[k],k==='nextNumber'?'number':'text');
 h+='</div><p><button class="btn primary">Gem indstillinger</button></p></form><div class="panel"><h2>Backup</h2><p class="muted">Eksportér dine fakturaer til en JSON-fil. Filen indeholder kundeoplysninger og skal opbevares sikkert.</p><div class="actions"><button class="btn" id="backup">Eksportér backup</button><label class="btn" for="restore">Importér backup</label><input type="file" id="restore" accept=".json,application/json" hidden></div></div>';
 app.innerHTML=h;$('#settingsForm').onsubmit=e=>{e.preventDefault();const f=e.currentTarget;const next=Number(f.elements.nextNumber.value);const max=Math.max(0,...invoices.filter(x=>x.status==='issued').map(x=>x.number||0));if(!Number.isSafeInteger(next)||next<=max||next<1){alert('Næste fakturanummer skal være større end allerede udstedte numre.');return}for(const k of Object.keys(defaults))settings[k]=f.elements[k].value.trim();settings.nextNumber=next;save();toast('Indstillinger gemt')};$('#backup').onclick=exportBackup;$('#restore').onchange=importBackup;
}
function exportBackup(){const data=JSON.stringify({format:'farverig-pages-v1',exportedAt:new Date().toISOString(),settings,invoices},null,2),a=document.createElement('a');a.href=URL.createObjectURL(new Blob([data],{type:'application/json'}));a.download='farverig-backup-'+today()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
async function importBackup(e){const file=e.target.files[0];if(!file)return;try{if(file.size>10000000)throw Error('Filen er for stor');const d=JSON.parse(await file.text());if(d.format!=='farverig-pages-v1'||!Array.isArray(d.invoices)||!d.settings||typeof d.settings!=='object')throw Error('Ukendt backupformat');if(!confirm('Dette erstatter alle fakturaer og indstillinger på denne enhed. Fortsæt?'))return;invoices=d.invoices;settings=d.settings;save();view('overview');toast('Backup importeret')}catch(err){alert('Kunne ikke importere backup: '+err.message)}}
const logo=$('#brandLogo');logo.onload=()=>{logo.hidden=false;$('.brandmark').hidden=true};logo.onerror=()=>{logo.hidden=true};view('overview');
