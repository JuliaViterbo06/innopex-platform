/* =====================================================================
   InnOpEx — telas da plataforma.
   As regras de negócio moram no back-end (app/services.py e app/rules.py).
   Este arquivo só desenha as telas e chama a API (static/js/api.js).
   ===================================================================== */
var PHASES = ["Define","Measure","Analyze","Improve","Control"];
var MESES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];
var S = { meta:null, user:null, projects:[], notifs:[], cfg:null };
var VIEW_MODE = "k";
var greeted = false;

/* ---------------- helpers ---------------- */
function $(id){ return document.getElementById(id); }
function esc(v){ return String(v==null?"":v).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];}); }
function musd(v){ v=+v||0; if(v>=1) return "US$ "+v.toFixed(1).replace(".",",")+"M"; if(v===0) return "US$ 0"; return "US$ "+(v*1000).toFixed(0)+"k"; }
function parseIso(s){ var a=String(s).slice(0,10).split("-"); return new Date(+a[0],+a[1]-1,+a[2]); }
function br(s){ if(!s) return "—"; var d=parseIso(s); return String(d.getDate()).padStart(2,"0")+"/"+String(d.getMonth()+1).padStart(2,"0"); }
function brTime(s){ if(!s) return ""; var d=new Date(s); return br(String(s).slice(0,10))+" "+String(d.getHours()).padStart(2,"0")+":"+String(d.getMinutes()).padStart(2,"0"); }
function proj(id){ return S.projects.filter(function(p){return p.id===id;})[0]; }
function can(a){ return !!(S.user && S.user.permissions.indexOf(a)>=0); }
function statusLabel(s){ return {g:"No prazo",y:"Atenção",r:"Crítico"}[s]; }
function statusPill(s){ return '<span class="pill '+({g:"ok",y:"warn-p",r:"bad"}[s])+'">'+statusLabel(s)+'</span>'; }
function initials(n){ return n.split(" ").filter(Boolean).map(function(w){return w[0];}).slice(0,2).join("").toUpperCase(); }
function ok(msg){ return function(){ return reload().then(function(){ if(msg) nopexSay(msg); }); }; }
function fail(e){ nopexSay('<span style="color:var(--artifact-red)">'+esc(e.message)+'</span>'); }

/* ---------------- dados ---------------- */
function reload(){
  return Promise.all([Api.projects(), Api.notifications(), Api.config()]).then(function(r){
    S.projects=r[0]; S.notifs=r[1]; S.cfg=r[2]; return route();
  });
}

/* ---------------- modal ---------------- */
function openModal(html){ $("modal").innerHTML=html; $("modal-bg").classList.add("open"); }
function closeModal(){ $("modal-bg").classList.remove("open"); }
$("modal-bg").addEventListener("click",function(e){ if(e.target.id==="modal-bg") closeModal(); });
document.addEventListener("keydown",function(e){ if(e.key==="Escape") closeModal(); });

/* ---------------- navegação ---------------- */
var ROUTES = [["portfolio","Portfólio"],["indicadores","Indicadores"],["decks","Decks"],["cronograma","Cronograma"],["notificacoes","Notificações"],["admin","Admin"],["fontes","Fontes"]];
function renderNav(r){
  if(!S.user){ $("nav").innerHTML=""; return; }
  var unread = S.notifs.filter(function(n){return !n.read;}).length;
  $("nav").innerHTML = ROUTES.filter(function(x){ return x[0]!=="admin" || can("admin"); }).map(function(x){
    var b = (x[0]==="notificacoes" && unread) ? '<span class="badge">'+unread+'</span>' : "";
    return '<a href="#/'+x[0]+'" class="'+(r===x[0]?"active":"")+'">'+x[1]+b+'</a>';
  }).join("");
}
function route(){
  var parts = (location.hash||"").replace(/^#\/?/,"").split("/");
  var r = parts[0] || "portfolio";
  if(!S.user) r = "login";
  if(r==="login" && S.user) r = "portfolio";
  if(r==="admin" && !can("admin")) r = "portfolio";
  document.querySelectorAll(".view").forEach(function(v){ v.classList.remove("on"); });
  ($("v-"+r) || $("v-portfolio")).classList.add("on");
  renderNav(r==="projeto"?"portfolio":r);
  $("user-box").style.display = S.user ? "" : "none";
  $("nopex-launcher").style.display = S.user ? "" : "none";
  if(!S.user){ $("nopex-panel").classList.remove("open"); $("nopex-greet").classList.add("hide"); return Promise.resolve(); }
  var p = Promise.resolve();
  if(r==="portfolio") p = renderPortfolio();
  if(r==="projeto") renderProject(decodeURIComponent(parts[1]||""), parts[2]||"resumo");
  if(r==="indicadores") p = renderCharts();
  if(r==="decks") p = renderDecks();
  if(r==="cronograma") p = renderSchedule();
  if(r==="notificacoes") renderNotifs();
  if(r==="admin") p = renderAdmin();
  return p.catch(fail);
}
window.addEventListener("hashchange", function(){ route(); window.scrollTo(0,0); });

/* ---------------- login / perfil ---------------- */
$("l-go").addEventListener("click",function(){
  $("l-err").textContent="";
  Api.devLogin({name:$("l-name").value.trim(), email:$("l-mail").value.trim(), role:$("l-role").value})
    .then(start).then(function(){ location.hash="#/portfolio"; })
    .catch(function(e){ $("l-err").textContent=e.message; });
});
$("user-box").addEventListener("click",function(){
  if(S.meta.auth_mode!=="dev"){ nopexSay("Seu perfil é <b>"+esc(S.user.role)+"</b>, definido pelo Admin no cadastro de acessos."); return; }
  openModal('<h2>Trocar perfil</h2><p class="sub">Em desenvolvimento você troca o perfil para testar. Com SSO, o perfil vem do cadastro de acessos.</p>'
    +'<div class="form"><div class="full"><label>Perfil</label><select id="sw-role">'
    +["Admin","Master","Leader","Viewer"].map(function(r){return '<option'+(S.user.role===r?" selected":"")+'>'+r+'</option>';}).join("")
    +'</select></div></div><div class="form-actions"><button class="btn btn-ghost" id="sw-out">Sair</button>'
    +'<button class="btn btn-primary" id="sw-ok">Aplicar</button></div>');
  $("sw-ok").onclick=function(){
    var role=$("sw-role").value;
    Api.devLogin({name:S.user.name,email:S.user.email,role:role}).then(start).then(function(){ closeModal();
      nopexSay("Agora você está como <b>"+role+"</b>. "+({Viewer:"Repare: os botões de editar somem e o Kanban fica travado.",Admin:"A aba Admin apareceu no menu.",Master:"Você pode mover cards, editar e aceitar datas.",Leader:"Você pode atualizar o projeto e aceitar ou recusar a data proposta."})[role]);
    }).catch(fail);
  };
  $("sw-out").onclick=function(){ Api.logout().then(function(){ S.user=null; greeted=false; closeModal(); location.hash="#/login"; route(); }); };
});
function paintUser(){ $("u-ini").textContent=initials(S.user.name); $("u-name").textContent=S.user.name; $("u-role").textContent="SSO GM · "+S.user.role; }

/* ---------------- portfólio ---------------- */
function visible(){
  var q=$("q").value.trim().toLowerCase(), m=$("f-master").value, t=$("f-tipo").value, f=$("f-fase").value;
  return S.projects.filter(function(p){
    var okQ=!q||(p.name+" "+p.id+" "+p.master+" "+p.leader).toLowerCase().indexOf(q)>=0;
    return okQ&&(!m||p.master===m)&&(!t||p.type===t)&&(!f||p.phase===f);
  });
}
function cardHtml(p){
  return '<article class="card'+(can("move")?"":" locked")+'"'+(can("move")?' draggable="true"':'')+' data-id="'+esc(p.id)+'">'
    +'<span class="cid">'+esc(p.id)+'</span><h3>'+esc(p.name)+'</h3><p class="sum">'+esc(p.summary)+'</p>'
    +'<div class="chips"><span class="chip'+(p.type==="Inovação"?" inv":"")+'">'+esc(p.type)+'</span>'
    +'<span class="chip master">Master: '+esc(p.master)+'</span>'
    +(p.stale_days>S.cfg.stale_days?'<span class="chip" style="background:#fbf1dd;color:var(--artifact-amber)">'+p.stale_days+' dias parado</span>':'')+'</div>'
    +'<div class="foot"><span class="money">'+musd(p.value_musd)+'</span><span class="icons">'
    +'<button type="button" title="Visualizar" aria-label="Visualizar" data-act="view">&#128065;</button>'
    +(can("edit")?'<button type="button" title="Editar" aria-label="Editar" data-act="edit">&#9998;</button>':'')
    +'</span></div></article>';
}
function renderPortfolio(){
  return Api.dashboard().then(function(d){
    var k=d.kpis;
    $("kpi-ativos").textContent=k.active; $("kpi-ativos-d").textContent=k.opex+" OpEx · "+k.innovation+" Inovação";
    $("kpi-blue").textContent=musd(k.blue_total); $("kpi-green").textContent=musd(k.green_total);
    $("kpi-stale").innerHTML='<span class="'+(k.stale?"warn":"up")+'">'+k.stale+'</span>';
    $("ql-alerts").textContent=k.open_alerts+" alerta"+(k.open_alerts===1?"":"s")+" aberto"+(k.open_alerts===1?"":"s");
    var sel=$("f-master"), cur=sel.value, ms=[];
    S.projects.forEach(function(p){ if(ms.indexOf(p.master)<0) ms.push(p.master); });
    sel.innerHTML='<option value="">Todos os Masters</option>'+ms.sort().map(function(m){return '<option'+(m===cur?" selected":"")+'>'+esc(m)+'</option>';}).join("");
    $("btn-new").style.display=can("edit")?"":"none";
    $("kanban-hint").textContent=can("move")
      ? "Arraste e solte um card em outra coluna para mudar a fase — cada movimento grava autor, data/hora e fase anterior no histórico."
      : "Perfil Viewer: somente leitura. Clique em um card para ver os detalhes.";
    drawBoard();
  });
}
function drawBoard(){
  $("pf-kanban").style.display=VIEW_MODE==="k"?"":"none"; $("pf-lista").style.display=VIEW_MODE==="l"?"":"none";
  $("vw-k").setAttribute("aria-pressed",VIEW_MODE==="k"); $("vw-l").setAttribute("aria-pressed",VIEW_MODE==="l");
  var list=visible();
  $("kanban").innerHTML=PHASES.map(function(ph){
    var items=list.filter(function(p){return p.phase===ph;});
    return '<div class="col" data-phase="'+ph+'"><div class="col-h"><b>'+ph+'</b><span class="count">'+items.length+'</span></div>'
      +(items.length?items.map(cardHtml).join(""):'<p class="hint" style="margin:6px 4px">Sem projetos</p>')+'</div>';
  }).join("");
  $("tbody").innerHTML=list.map(function(p){
    return '<tr><td>'+esc(p.id)+'</td><td><a href="#/projeto/'+encodeURIComponent(p.id)+'"><b>'+esc(p.name)+'</b></a></td><td>'+esc(p.type)+'</td>'
      +'<td>'+esc(p.phase)+'</td><td>'+esc(p.master)+'</td><td><span class="dot '+p.status+'">'+statusLabel(p.status)+'</span></td>'
      +'<td class="num">'+(+p.value_musd).toFixed(3).replace(".",",")+'</td><td>'+(p.meeting?br(p.meeting.day):"—")+'</td></tr>';
  }).join("")||'<tr><td colspan="8">Nenhum projeto para os filtros selecionados.</td></tr>';
  bindKanban();
}
var dragId=null;
function bindKanban(){
  document.querySelectorAll("#kanban .card").forEach(function(card){
    card.addEventListener("click",function(e){
      var b=e.target.closest("button"), id=card.dataset.id;
      if(b && b.dataset.act==="edit"){ openProjectForm(id); return; }
      location.hash="#/projeto/"+encodeURIComponent(id);
    });
    card.addEventListener("dragstart",function(){ dragId=card.dataset.id; card.classList.add("dragging"); });
    card.addEventListener("dragend",function(){ card.classList.remove("dragging"); });
  });
  document.querySelectorAll("#kanban .col").forEach(function(col){
    col.addEventListener("dragover",function(e){ if(!can("move")) return; e.preventDefault(); col.classList.add("over"); });
    col.addEventListener("dragleave",function(){ col.classList.remove("over"); });
    col.addEventListener("drop",function(e){ e.preventDefault(); col.classList.remove("over"); if(dragId) movePhase(dragId,col.dataset.phase); dragId=null; });
  });
}
function movePhase(id,to){
  var p=proj(id); if(!p || p.phase===to) return;
  var from=p.phase;
  Api.movePhase(id,to).then(ok("Movi <b>"+esc(p.name)+"</b> de "+from+" para "+to+". Registrei autor, data e fase anterior no histórico."))
    .catch(function(e){ nopexSay("Não consegui mover <b>"+esc(p.name)+"</b>: "+esc(e.message)
      +(e.status===422?' <a href="#" data-edit="'+esc(id)+'">Preencher agora</a>.':'')); });
}
["q","f-master","f-tipo","f-fase"].forEach(function(id){ $(id).addEventListener(id==="q"?"input":"change",drawBoard); });
$("vw-k").onclick=function(){ VIEW_MODE="k"; drawBoard(); };
$("vw-l").onclick=function(){ VIEW_MODE="l"; drawBoard(); };
$("btn-new").onclick=function(){ openProjectForm(null); };

/* ---------------- cadastro / edição ---------------- */
function openProjectForm(id){
  if(!can("edit")){ nopexSay("O perfil Viewer não pode editar projetos."); return; }
  var p = id ? proj(id) : {name:"",type:"Opex",phase:"Define",master:"",leader:"",value_musd:0,green_musd:0,status:"g",summary:""};
  var opt=function(list,cur){ return list.map(function(v){return '<option'+(v===cur?" selected":"")+'>'+v+'</option>';}).join(""); };
  openModal('<h2>'+(id?"Editar projeto":"Novo projeto")+'</h2>'
    +'<p class="sub">'+(id?"Cada alteração grava autor e data no histórico.":"O registro é criado na plataforma; a réplica na lista de origem depende de autorização.")+'</p><div class="form">'
    +'<div class="full"><label>Nome do projeto <span class="req">*</span></label><input id="pf-name" value="'+esc(p.name)+'"></div>'
    +'<div><label>Tipo <span class="req">*</span></label><select id="pf-type">'+opt(["Opex","Inovação"],p.type)+'</select><div class="help">Opex = lista Projects (Global) · Inovação = Growth Project (GMSA)</div></div>'
    +'<div><label>Fase DMAIC <span class="req">*</span></label><select id="pf-phase">'+opt(PHASES,p.phase)+'</select><div class="help">Inovação também segue DMAIC</div></div>'
    +'<div><label>Master (único responsável) <span class="req">*</span></label><input id="pf-master" value="'+esc(p.master)+'"></div>'
    +'<div><label>Líder <span class="req">*</span></label><input id="pf-leader" value="'+esc(p.leader)+'"></div>'
    +'<div><label>Lucro estimado / Blue Value (US$ M) <span id="pf-vreq" class="req"></span></label><input id="pf-value" type="number" step="0.001" min="0" value="'+(+p.value_musd||0)+'"><div class="help">Obrigatório a partir do Measure</div></div>'
    +'<div><label>Green Value (US$ M)</label><input id="pf-green" type="number" step="0.1" min="0" value="'+(+p.green_musd||0)+'"><div class="help">Campo separado, não soma no portfólio</div></div>'
    +'<div><label>Status</label><select id="pf-status"><option value="g"'+(p.status==="g"?" selected":"")+'>No prazo</option><option value="y"'+(p.status==="y"?" selected":"")+'>Atenção</option><option value="r"'+(p.status==="r"?" selected":"")+'>Crítico</option></select></div>'
    +'<div class="full"><label>Resumo</label><textarea id="pf-sum">'+esc(p.summary)+'</textarea></div>'
    +'</div><div class="err" id="pf-err"></div>'
    +'<div class="form-actions"><button class="btn btn-ghost" id="pf-cancel">Cancelar</button><button class="btn btn-primary" id="pf-ok">Salvar</button></div>');
  var upd=function(){ $("pf-vreq").textContent=PHASES.indexOf($("pf-phase").value)>=1?"*":""; }; upd();
  $("pf-phase").onchange=upd; $("pf-cancel").onclick=closeModal;
  $("pf-ok").onclick=function(){
    var d={name:$("pf-name").value.trim(),type:$("pf-type").value,phase:$("pf-phase").value,master:$("pf-master").value.trim(),
      leader:$("pf-leader").value.trim(),value_musd:parseFloat($("pf-value").value)||0,green_musd:parseFloat($("pf-green").value)||0,
      status:$("pf-status").value,summary:$("pf-sum").value.trim()};
    if(!d.name||!d.master||!d.leader){ $("pf-err").textContent="Preencha nome, Master e líder."; return; }
    (id?Api.updateProject(id,d):Api.createProject(d)).then(function(saved){
      closeModal(); location.hash="#/projeto/"+encodeURIComponent(saved.id);
      return ok(id?"Alterações salvas e registradas no histórico.":"Projeto <b>"+esc(saved.name)+"</b> criado! Avisei o Master e o líder.")();
    }).catch(function(e){ $("pf-err").textContent=e.message; });
  };
}

/* ---------------- detalhe do projeto ---------------- */
function renderProject(id,tab){
  var p=proj(id), v=$("v-projeto");
  if(!p){ v.innerHTML='<p class="crumb"><a href="#/portfolio">Portfólio</a></p><div class="panel">Projeto não encontrado.</div>'; return; }
  var idx=PHASES.indexOf(p.phase), tabs=[["resumo","Resumo"],["historico","Histórico"],["decks","Decks"],["reunioes","Reuniões e Meeting Notes"]];
  var h='<p class="crumb"><a href="#/portfolio">Portfólio</a> <span>›</span> <a href="#/projeto/'+encodeURIComponent(p.id)+'">'+esc(p.id)+'</a></p>'
   +'<div class="panel"><div class="hero"><div><span class="eyebrow">'+esc(p.id)+' · '+esc(p.type)+' · origem: '+esc(p.source)+'</span>'
   +'<h1>'+esc(p.name)+'</h1><p>'+esc(p.summary)+'</p><div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap">'+statusPill(p.status)
   +(p.stale_days>S.cfg.stale_days?'<span class="pill warn-p">'+p.stale_days+' dias sem atualização</span>':'')
   +(p.missing_notes?'<span class="pill bad">Meeting Notes pendente</span>':'')+'</div></div>'
   +'<div class="acts"><a class="btn btn-primary" href="#/portfolio" style="text-decoration:none">← Voltar</a>'
   +(can("edit")?'<button class="btn btn-ghost" data-edit="'+esc(p.id)+'">Editar</button>':'')+'</div></div>'
   +'<div class="stepper">'+PHASES.map(function(ph,i){return '<span class="'+(i<idx?"done":i===idx?"cur":"")+'">'+ph+'</span>';}).join("")+'</div></div>'
   +'<div class="infos">'
   +'<div class="kpi"><div class="lab">Master</div><div class="val">'+esc(p.master)+'</div></div>'
   +'<div class="kpi"><div class="lab">Líder</div><div class="val">'+esc(p.leader)+'</div></div>'
   +'<div class="kpi"><div class="lab">Lucro estimado / Blue</div><div class="val">'+musd(p.value_musd)+'</div><div class="delta">Green: '+musd(p.green_musd)+'</div></div>'
   +'<div class="kpi"><div class="lab">Próxima reunião</div><div class="val">'+(p.meeting?br(p.meeting.day):"—")+'</div><div class="delta">'+(p.meeting?p.meeting.state:"sem data")+'</div></div>'
   +'</div><div class="tabs">'+tabs.map(function(t){return '<a class="btn btn-ghost" aria-pressed="'+(tab===t[0])+'" href="#/projeto/'+encodeURIComponent(p.id)+'/'+t[0]+'" style="text-decoration:none">'+t[1]+'</a>';}).join("")+'</div>';
  if(tab==="resumo"){
    var pend=[]; if(p.missing_notes) pend.push("Registrar Meeting Notes da última reunião");
    if(p.stale_days>S.cfg.stale_days) pend.push("Atualizar material (parado há "+p.stale_days+" dias)");
    if(idx>=1 && !(+p.value_musd>0)) pend.push("Informar lucro estimado");
    var last=p.decks[p.decks.length-1], lastNote=p.notes[p.notes.length-1];
    h+='<div class="gov3">'
     +'<div class="panel gov"><h3>Próxima governança</h3><ul><li>'+(p.meeting?"Terça "+br(p.meeting.day)+" · "+p.meeting.state:"Sem data na fila")+'</li><li>Intervalo de retorno: '+(lastNote?lastNote.return_weeks+" semanas":"a definir")+'</li></ul></div>'
     +'<div class="panel gov o"><h3>Pendências</h3><ul>'+(pend.length?pend.map(function(x){return "<li>"+x+"</li>";}).join(""):"<li>Nenhuma pendência 🎉</li>")+'</ul></div>'
     +'<div class="panel gov l"><h3>Material</h3><ul><li>'+(last?esc(last.file_type+" · "+last.name+" v"+last.version):"Nenhum deck enviado")+'</li><li>Última alteração: '+esc(p.history[0]?p.history[0].author:"—")+'</li></ul></div></div>';
  }
  if(tab==="historico"){
    h+='<div class="hist">'+p.history.map(function(x){return '<div class="note"><span class="ic">&#8635;</span><div style="flex:1"><b>'+esc(x.text)+'</b><p>Autor: '+esc(x.author)+'</p></div><time>'+brTime(x.at)+'</time></div>';}).join("")+'</div>';
  }
  if(tab==="decks"){
    h+='<div class="sec-head"><div></div>'+(can("edit")?'<button class="btn btn-ghost" data-upload="'+esc(p.id)+'">Enviar nova versão</button>':'')+'</div><div class="grid3">'
     +(p.decks.length?p.decks.slice().reverse().map(function(d){return deckHtml(Object.assign({project_id:p.id,project_name:p.name,featured:false},d));}).join(""):'<p class="empty">Nenhum documento ainda.</p>')+'</div>';
  }
  if(tab==="reunioes"){
    h+='<div class="sec-head"><div></div>'+(can("decide")?'<button class="btn btn-primary" data-notes="'+esc(p.id)+'">Registrar Meeting Notes</button>':'')+'</div><div class="hist">'
     +(p.notes.length?p.notes.slice().reverse().map(function(n){return '<div class="note"><span class="ic">&#9998;</span><div style="flex:1"><b>'+esc(n.text)+'</b><p>Retorno em '+n.return_weeks+' semanas · registrado por '+esc(n.author)+'</p></div><time>'+br(n.day)+'</time></div>';}).join(""):'<p class="empty">Nenhuma Meeting Notes registrada.</p>')+'</div>';
  }
  v.innerHTML=h;
}

/* ---------------- decks ---------------- */
var FEATURED_DAY=null;
function deckHtml(d){
  var old=d.days_old>S.cfg.stale_days;
  return '<article class="deck'+(d.featured?" featured":"")+'">'+(d.featured?'<span class="flag">Reunião '+br(FEATURED_DAY)+'</span>':'')
    +'<div class="file"><em>'+esc(d.file_type)+'</em> <a href="#/projeto/'+encodeURIComponent(d.project_id)+'/decks" style="color:inherit;text-decoration:none">'+esc(d.project_name)+' — '+esc(d.name)+'</a></div>'
    +'<p>v'+d.version+' · '+esc(d.author)+' · '+(d.days_old===0?"atualizado hoje":"atualizado há "+d.days_old+" dia"+(d.days_old===1?"":"s"))+'</p>'
    +(d.featured?'<p style="color:var(--artifact-blue);font-weight:600">Em destaque automático: projeto na fila de terça.</p>':'')
    +(old?'<p style="color:var(--artifact-amber);font-weight:600">Material vencido: notificar líder e Master.</p>':'')+'</article>';
}
function renderDecks(){
  $("btn-upload").style.display=can("edit")?"":"none";
  return Api.decks().then(function(r){ FEATURED_DAY=r.featured_day; $("decks-grid").innerHTML=r.items.map(deckHtml).join("")||'<p class="empty">Nenhum documento.</p>'; });
}
function openUpload(pid){
  openModal('<h2>Enviar documento</h2><p class="sub">Uma nova versão zera o contador de material parado e entra no histórico.</p><div class="form">'
    +'<div class="full"><label>Projeto</label><select id="up-p">'+S.projects.map(function(p){return '<option value="'+esc(p.id)+'"'+(p.id===pid?" selected":"")+'>'+esc(p.id+" · "+p.name)+'</option>';}).join("")+'</select></div>'
    +'<div><label>Tipo</label><select id="up-t"><option>PPTX</option><option>PDF</option><option>XLSX</option><option>DOCX</option></select></div>'
    +'<div><label>Nome do material</label><input id="up-n" placeholder="Ex.: Status Update"></div>'
    +'<div class="full"><label>Arquivo</label><input type="file" id="up-f"><div class="help">Nesta versão só o registro é salvo; o arquivo irá para a biblioteca do SharePoint na integração.</div></div>'
    +'</div><div class="err" id="up-err"></div><div class="form-actions"><button class="btn btn-ghost" id="up-cancel">Cancelar</button><button class="btn btn-primary" id="up-ok">Enviar</button></div>');
  $("up-cancel").onclick=closeModal;
  $("up-ok").onclick=function(){
    var f=$("up-f").files[0], n=$("up-n").value.trim()||(f?f.name.replace(/\.[^.]+$/,""):"");
    if(!n){ $("up-err").textContent="Dê um nome ao material ou escolha o arquivo."; return; }
    Api.uploadDeck({project_id:$("up-p").value,file_type:$("up-t").value,name:n}).then(function(p){ closeModal();
      return ok("Recebi <b>"+esc(n)+"</b> de "+esc(p.name)+". O alerta de material parado foi encerrado.")(); })
      .catch(function(e){ $("up-err").textContent=e.message; });
  };
}
$("btn-upload").onclick=function(){ openUpload(null); };

/* ---------------- cronograma ---------------- */
function renderSchedule(){
  return Api.schedule().then(function(s){
    $("pend").innerHTML=s.blocked.length?'<div class="note alert" style="margin-bottom:12px"><span class="ic">!</span><div style="flex:1"><b>'+s.blocked.length+' projeto(s) sem Meeting Notes — agendamento bloqueado</b><p>'
      +s.blocked.map(function(p){return esc(p.name)+(can("decide")?' · <a href="#" data-notes="'+esc(p.id)+'">registrar agora</a>':'');}).join(" &nbsp; ")+'</p></div></div>':"";
    $("timeline").innerHTML=s.slots.map(function(sl,i){
      var dt=parseIso(sl.day);
      var body=sl.projects.length?sl.projects.map(function(p){
        var pill=p.state==="confirmado"?'<span class="pill ok">Confirmado</span>':p.state==="reagendado"?'<span class="pill">Reagendado</span>':'<span class="pill">Aguardando aceite</span>', acts="";
        if(can("decide") && p.state!=="confirmado") acts+='<button class="btn btn-primary btn-sm" data-accept="'+esc(p.id)+'">Aceitar</button><button class="btn btn-ghost btn-sm" data-decline="'+esc(p.id)+'">Recusar e reagendar</button>';
        if(can("decide") && p.state==="confirmado") acts+='<button class="btn btn-ghost btn-sm" data-notes="'+esc(p.id)+'">Meeting Notes</button>';
        return '<div class="slot-item"><div class="grow"><a href="#/projeto/'+encodeURIComponent(p.id)+'">'+esc(p.name)+'</a><small>Líder: '+esc(p.leader)+' · Master: '+esc(p.master)+(p.note?' · '+esc(p.note):'')+'</small></div>'+pill+acts+'</div>';
      }).join(""):'<p>Nenhum projeto agendado</p>';
      return '<div class="slot"><div class="date"><small>'+MESES[dt.getMonth()]+'</small><b>'+String(dt.getDate()).padStart(2,"0")+'</b><small>Terça</small></div>'
        +'<div class="body"><b>'+sl.projects.length+' projeto(s) · '+sl.free+' vaga(s) livre(s)</b><p>Capacidade de '+sl.capacity+' projetos por reunião · '+esc(s.meeting_time)
        +(i===0?' · decks em destaque · pauta fechada automaticamente na sexta anterior':'')+'</p>'+body+'</div>'
        +'<div class="act">'+(sl.projects.length?'<button class="btn btn-ghost" data-agenda="'+sl.day+'">Ver pauta</button>':'<span class="pill">Disponível</span>')+'</div></div>';
    }).join("");
  });
}
function openNotes(id){
  var p=proj(id);
  openModal('<h2>Meeting Notes · '+esc(p.name)+'</h2><p class="sub">Obrigatório após cada reunião. Com o intervalo de retorno, a plataforma propõe a próxima terça livre.</p><div class="form">'
    +'<div class="full"><label>Notas da reunião <span class="req">*</span></label><textarea id="mn-t" placeholder="Decisões, pendências, responsáveis e prazos"></textarea></div>'
    +'<div><label>Intervalo de retorno <span class="req">*</span></label><select id="mn-w"><option value="">Escolha…</option><option value="2">2 semanas</option><option value="4">4 semanas</option><option value="6">6 semanas</option><option value="8">8 semanas</option></select></div>'
    +'</div><div class="err" id="mn-err"></div><div class="form-actions"><button class="btn btn-ghost" id="mn-cancel">Cancelar</button><button class="btn btn-primary" id="mn-ok">Salvar e propor data</button></div>');
  $("mn-cancel").onclick=closeModal;
  $("mn-ok").onclick=function(){
    var t=$("mn-t").value.trim(), w=+$("mn-w").value;
    if(!t||!w){ $("mn-err").textContent="Meeting Notes e intervalo de retorno são obrigatórios."; return; }
    Api.notes(id,{text:t,return_weeks:w}).then(function(r){ closeModal();
      return ok("Notas salvas! Propus <b>"+br(r.meeting.day)+"</b> para o retorno de "+esc(r.name)+" e avisei o líder.")(); })
      .catch(function(e){ $("mn-err").textContent=e.message; });
  };
}
function openAgenda(day){
  Api.agenda(day).then(function(rows){
    openModal('<h2>Pauta · terça '+br(day)+'</h2><p class="sub">Gerada automaticamente a partir da fila de governança.</p><div class="tablewrap"><table style="min-width:0"><thead><tr><th>Horário</th><th>Projeto</th><th>Propósito</th><th style="text-align:right">GV US$M</th><th>Sponsor / Presenter</th></tr></thead><tbody>'
      +rows.map(function(r){return '<tr><td>'+r.time+'</td><td><b>'+esc(r.project)+'</b></td><td>'+esc(r.purpose)+'</td><td class="num">'+(r.gv_musd==null?"—":(+r.gv_musd).toFixed(2).replace(".",","))+'</td><td>'+esc(r.presenter)+'</td></tr>';}).join("")
      +'</tbody></table></div><div class="form-actions"><button class="btn btn-primary" id="ag-close">Fechar</button></div>');
    $("ag-close").onclick=closeModal;
  }).catch(fail);
}

/* ---------------- notificações ---------------- */
function renderNotifs(){
  $("notif-list").innerHTML=S.notifs.map(function(n){
    var ic={alert:"!",move:"&#8635;",mail:"&#9993;"}[n.kind];
    return '<div class="note'+(n.kind==="alert"?" alert":"")+'" style="'+(n.read?"opacity:.6":"")+'"><span class="ic">'+ic+'</span><div style="flex:1"><b>'+esc(n.title)+'</b><p>'+esc(n.text)+'</p></div><time>'+brTime(n.created_at)+(n.read?"":' · <a href="#" data-read="'+esc(n.id)+'">lida</a>')+'</time></div>';
  }).join("")||'<p class="empty">Sem notificações.</p>';
}
$("btn-readall").onclick=function(){ Api.readAll().then(ok()).catch(fail); };

/* ---------------- admin ---------------- */
function renderAdmin(){
  $("p-stale").value=S.cfg.stale_days; $("p-cap").value=S.cfg.max_per_tuesday; $("p-hora").value=S.cfg.meeting_time; $("p-slot").value=S.cfg.minutes_per_project;
  var what={Admin:"Tudo + parâmetros e perfis",Master:"Editar, mover fase, aceitar datas",Leader:"Atualizar projeto, aceitar/recusar data",Viewer:"Somente leitura"};
  return Promise.all([Api.users(),Api.pending()]).then(function(r){
    $("users").innerHTML=r[0].map(function(u){return '<tr><td><b>'+esc(u.name)+'</b></td><td>'+esc(u.email)+'</td><td><span class="pill">'+u.role+'</span></td><td>'+what[u.role]+'</td></tr>';}).join("");
    $("pend-dec").innerHTML=r[1].map(function(d){return '<div class="note"><span class="ic">?</span><div style="flex:1"><b>'+esc(d)+'</b><p>A confirmar com a liderança</p></div></div>';}).join("");
  });
}
$("p-save").onclick=function(){
  Api.saveConfig({stale_days:+$("p-stale").value,max_per_tuesday:+$("p-cap").value,meeting_time:$("p-hora").value,minutes_per_project:+$("p-slot").value})
    .then(ok("Parâmetros salvos. As regras de alerta e a capacidade da terça já usam os novos valores.")).catch(fail);
};

/* ---------------- indicadores ---------------- */
var charts={};
function theme(){ var s=getComputedStyle(document.documentElement), g=function(n){return s.getPropertyValue(n).trim();};
  return {navy:g("--artifact-navy"),blue:g("--artifact-blue"),lime:g("--artifact-lime"),text:g("--artifact-text"),muted:g("--artifact-text-muted"),border:g("--artifact-border"),green:g("--artifact-green"),amber:g("--artifact-amber"),red:g("--artifact-red")}; }
function renderCharts(){
  return Api.dashboard().then(function(d){
    if(typeof echarts==="undefined"){ ["c-fase","c-master","c-tipo","c-status"].forEach(function(id){ $(id).innerHTML='<div class="chart-off">Os gráficos precisam de internet para carregar a biblioteca ECharts.<br>Conecte-se e recarregue a página.</div>'; }); return; }
    Object.keys(charts).forEach(function(k){ charts[k].dispose(); }); charts={};
    var t=theme(), ax={axisLine:{lineStyle:{color:t.border}},axisLabel:{color:t.muted}}, sp={splitLine:{lineStyle:{color:t.border}},axisLabel:{color:t.muted}};
    ["fase","master","tipo","status"].forEach(function(k){ charts[k]=echarts.init($("c-"+k),null,{renderer:"svg"}); });
    charts.fase.setOption({grid:{left:40,right:18,top:20,bottom:30},tooltip:{trigger:"axis"},xAxis:Object.assign({type:"category",data:PHASES},ax),yAxis:Object.assign({type:"value",minInterval:1},sp),
      series:[{type:"bar",barWidth:"46%",itemStyle:{color:t.blue,borderRadius:[6,6,0,0]},label:{show:true,position:"top",color:t.text},data:PHASES.map(function(ph){return d.by_phase[ph];})}]});
    var names=Object.keys(d.by_master);
    charts.master.setOption({grid:{left:130,right:40,top:14,bottom:24},tooltip:{trigger:"axis",axisPointer:{type:"shadow"}},xAxis:Object.assign({type:"value"},sp),yAxis:{type:"category",data:names,axisLine:{lineStyle:{color:t.border}},axisLabel:{color:t.text}},
      series:[{type:"bar",barWidth:"52%",itemStyle:{color:t.navy,borderRadius:[0,6,6,0]},label:{show:true,position:"right",color:t.text,formatter:function(x){return x.value.toFixed(1);}},data:names.map(function(n){return d.by_master[n];})}]});
    var tp=["Opex","Inovação"];
    charts.tipo.setOption({grid:{left:44,right:44,top:30,bottom:30},tooltip:{trigger:"axis"},legend:{top:0,textStyle:{color:t.muted}},xAxis:Object.assign({type:"category",data:tp},ax),
      yAxis:[Object.assign({type:"value",minInterval:1},sp),{type:"value",splitLine:{show:false},axisLabel:{color:t.muted}}],
      series:[{name:"Projetos",type:"bar",barWidth:"30%",itemStyle:{color:t.blue,borderRadius:[6,6,0,0]},label:{show:true,position:"top",color:t.text},data:tp.map(function(x){return d.by_type[x].count;})},
              {name:"Valor (US$ M)",type:"bar",yAxisIndex:1,barWidth:"30%",itemStyle:{color:t.lime,borderRadius:[6,6,0,0]},label:{show:true,position:"top",color:t.text,formatter:function(x){return x.value.toFixed(1);}},data:tp.map(function(x){return d.by_type[x].value;})}]});
    charts.status.setOption({tooltip:{trigger:"item"},legend:{bottom:0,textStyle:{color:t.muted}},series:[{type:"pie",radius:["48%","72%"],center:["50%","44%"],label:{color:t.text,formatter:"{b}: {c}"},
      data:[{value:d.by_status.g,name:"No prazo",itemStyle:{color:t.green}},{value:d.by_status.y,name:"Atenção",itemStyle:{color:t.amber}},{value:d.by_status.r,name:"Crítico",itemStyle:{color:t.red}}]}]});
  });
}
window.addEventListener("resize",function(){ Object.keys(charts).forEach(function(k){ charts[k].resize(); }); });

/* ---------------- ações por clique (delegação) ---------------- */
document.addEventListener("click",function(e){
  var a=e.target.closest("[data-edit],[data-upload],[data-notes],[data-accept],[data-decline],[data-agenda],[data-read],[data-action]");
  if(!a) return;
  e.preventDefault();
  var ds=a.dataset;
  if(ds.edit) openProjectForm(ds.edit);
  else if(ds.upload) openUpload(ds.upload);
  else if(ds.notes) openNotes(ds.notes);
  else if(ds.accept) Api.accept(ds.accept).then(function(p){ return ok("Data confirmada para <b>"+esc(p.name)+"</b> em "+br(p.meeting.day)+". O deck entra em destaque na semana da reunião.")(); }).catch(fail);
  else if(ds.decline) Api.decline(ds.decline).then(function(p){ return ok("Reagendei <b>"+esc(p.name)+"</b> para a próxima terça com vaga: "+br(p.meeting.day)+". Mandei a proposta para o líder.")(); }).catch(fail);
  else if(ds.agenda) openAgenda(ds.agenda);
  else if(ds.read) Api.readOne(ds.read).then(ok()).catch(fail);
  else if(ds.action==="new-project") openProjectForm(null);
});

/* ---------------- Nopex ---------------- */
function nopexOpen(){ $("nopex-panel").classList.add("open"); $("nopex-greet").classList.add("hide"); }
function nopexSay(html){ nopexOpen(); var b=$("np-body"); b.insertAdjacentHTML("beforeend",'<div class="np-msg"><b>Nopex:</b> '+html+'</div>'); b.scrollTop=b.scrollHeight; }
function greet(){
  if(greeted) return; greeted=true;
  var first=S.user.name.split(" ")[0];
  $("greet-t").textContent="Oi, "+first+"! Eu sou o Nopex 👋";
  $("np-body").innerHTML='<div class="np-msg"><b>Nopex:</b> Oi, '+esc(first)+'! Estou em todas as telas da plataforma. Posso buscar projetos, montar a pauta da terça e cobrar atualizações. Por onde começamos?</div>';
  $("nopex-greet").classList.remove("hide");
  setTimeout(function(){ $("nopex-greet").classList.add("hide"); },16000);
}
function nopexAsk(q){
  $("np-body").insertAdjacentHTML("beforeend",'<div class="np-msg" style="background:var(--artifact-blue-soft);border-color:var(--artifact-blue)"><b>Você:</b> '+esc(q)+'</div>');
  Api.nopex(q).then(function(r){ nopexSay(r.answer); }).catch(fail);
}
$("nopex-launcher").addEventListener("click",function(){ $("nopex-panel").classList.toggle("open"); $("nopex-greet").classList.add("hide"); });
$("np-close").addEventListener("click",function(){ $("nopex-panel").classList.remove("open"); });
document.querySelectorAll(".np-sug button").forEach(function(btn){ btn.addEventListener("click",function(){ nopexAsk(btn.dataset.q); }); });
$("np-send").addEventListener("click",function(){ var i=$("np-input"); if(i.value.trim()){ nopexAsk(i.value.trim()); i.value=""; } });
$("np-input").addEventListener("keydown",function(e){ if(e.key==="Enter") $("np-send").click(); });
$("nopex-greet").addEventListener("click",nopexOpen);

/* ---------------- início ---------------- */
$("btn-reset").addEventListener("click",function(e){ e.preventDefault(); Api.reset().then(ok("Demonstração reiniciada com os dados de exemplo.")).catch(fail); });
function start(){
  return Api.me().then(function(u){ S.user=u; paintUser(); return reload(); }).then(greet);
}
Api.meta().then(function(m){
  S.meta=m; $("app-version").textContent=m.version; $("data-mode").textContent=m.data_mode;
  return start().catch(function(e){
    if(e.status===401 && m.auth_mode==="dev"){ S.user=null; route(); return; }
    $("app").innerHTML='<div class="login"><div class="panel"><h1>Acesso negado</h1><p>'+esc(e.message)+'</p></div></div>';
  });
}).catch(function(){ $("app").innerHTML='<div class="login"><div class="panel"><h1>Servidor fora do ar</h1><p>Inicie o back-end no VS Code (F5) e recarregue a página.</p></div></div>'; });
