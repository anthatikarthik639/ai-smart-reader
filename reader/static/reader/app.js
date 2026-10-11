(() => {
  const app = document.getElementById("readerApp");
  if (!app) return;
  const docId = Number(app.dataset.documentId);
  const pdfUrl = app.dataset.pdfUrl;
  const csrf = () => document.cookie.split("; ").find(x => x.startsWith("csrftoken="))?.split("=")[1] || "";
  const $ = id => document.getElementById(id);
  let pdf = null, page = Math.max(1, Number(app.dataset.startPage) || 1), zoom = 1, selected = "", toastTimer;
  const toast = msg => { const el=$("toast"); el.textContent=msg; el.classList.add("show"); clearTimeout(toastTimer); toastTimer=setTimeout(()=>el.classList.remove("show"),2600); };
  async function api(url, method="GET", body=null) {
    const opts={method,headers:{"X-CSRFToken":csrf()}};
    if(body){opts.headers["Content-Type"]="application/json";opts.body=JSON.stringify(body);}
    const res=await fetch(url,opts); const data=await res.json().catch(()=>({}));
    if(!res.ok) throw new Error(data.error || "Request failed."); return data;
  }
  const pdfjs=window.pdfjsLib;
  pdfjs.GlobalWorkerOptions.workerSrc="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
  const canvas=$("pdfCanvas"), ctx=canvas.getContext("2d"), textLayer=$("textLayer");
  async function renderPage(n) {
    if(!pdf) return; page=Math.max(1,Math.min(pdf.numPages,n)); $("pdfLoading").classList.remove("hidden");
    try {
      const p=await pdf.getPage(page), viewport=p.getViewport({scale:zoom}), outputScale=window.devicePixelRatio||1;
      canvas.width=Math.floor(viewport.width*outputScale); canvas.height=Math.floor(viewport.height*outputScale);
      canvas.style.width=viewport.width+"px"; canvas.style.height=viewport.height+"px";
      textLayer.innerHTML=""; textLayer.style.width=viewport.width+"px"; textLayer.style.height=viewport.height+"px";
      await p.render({canvasContext:ctx,viewport,transform:outputScale!==1?[outputScale,0,0,outputScale,0,0]:null}).promise;
      const content=await p.getTextContent();
      await pdfjs.renderTextLayer({textContentSource:content,container:textLayer,viewport,textDivs:[]}).promise;
      $("pageInput").value=page; $("pageTotal").textContent="/ "+pdf.numPages; $("pageStatus").textContent=`Page ${page} of ${pdf.numPages}`;
      $("bottomPage").textContent=`Page ${page} of ${pdf.numPages}`; $("notePageLabel").textContent=page; $("zoomLabel").textContent=Math.round(zoom*100)+"%";
      $("prevPage").disabled=$("prevBottom").disabled=page<=1; $("nextPage").disabled=$("nextBottom").disabled=page>=pdf.numPages;
      $("pdfScroll").scrollTop=0; $("pdfScroll").scrollLeft=0; $("pdfLoading").classList.add("hidden");
      try { await api("/api/progress/","POST",{document_id:docId,page}); } catch(e) {}
      loadBookmarks(); loadNotes(); loadHighlights();
    } catch(e) { $("pdfLoading").innerHTML=`<p>Could not render this PDF page.</p><small>${e.message}</small>`; }
  }
  pdfjs.getDocument({url:pdfUrl}).promise.then(async value=>{pdf=value;$("pdfLoading").classList.add("hidden");await renderPage(page);}).catch(()=>{$("pdfLoading").innerHTML="<p>We couldn't open this PDF.</p><small>Try uploading a valid PDF file.</small>";});
  const go=n=>renderPage(n);
  $("prevPage").onclick=$("prevBottom").onclick=()=>go(page-1);
  $("nextPage").onclick=$("nextBottom").onclick=()=>go(page+1);
  $("pageInput").addEventListener("change",()=>go(Number($("pageInput").value)||1));
  $("zoomOut").onclick=()=>{zoom=Math.max(.6,zoom-.1);renderPage(page);};
  $("zoomIn").onclick=()=>{zoom=Math.min(2.2,zoom+.1);renderPage(page);};
  textLayer.addEventListener("mouseup",()=>{const s=window.getSelection()?.toString().trim();if(s){selected=s;$("selectedText").textContent=s;$("selectedText").classList.add("has-selection");}});
  document.querySelectorAll(".tab").forEach(btn=>btn.addEventListener("click",()=>{document.querySelectorAll(".tab,.tab-content").forEach(el=>el.classList.remove("active"));btn.classList.add("active");$("tab-"+btn.dataset.tab).classList.add("active");}));
  function showAnswer(answer, mode){$("aiResult").classList.remove("hidden");$("aiAnswer").textContent=answer;const h=$("aiResult").querySelector(".result-head span");h.textContent=mode==="ollama"?"✦ LOCAL AI RESPONSE":(mode==="ai"?"✦ AI RESPONSE":"✦ DEMO RESPONSE");}
  async function ask(action) {
    const question=$("questionInput").value.trim();
    if(!selected && !(action==="ask"&&question)){toast("Select a passage in the PDF first.");return;}
    if(action==="ask"&&!question){toast("Write your question first.");return;}
    const buttons=[...document.querySelectorAll(".ai-action"),$("askButton")];buttons.forEach(b=>b.disabled=true);
    $("aiResult").classList.remove("hidden");$("aiAnswer").textContent="Thinking…";
    try {const data=await api("/api/ai/","POST",{document_id:docId,text:selected,question,action});showAnswer(data.answer,data.mode);}
    catch(e){$("aiAnswer").textContent=e.message;toast("AI request failed.");}
    finally{buttons.forEach(b=>b.disabled=false);}
  }
  document.querySelectorAll(".ai-action").forEach(b=>b.addEventListener("click",()=>ask(b.dataset.action)));
  $("askButton").onclick=()=>ask("ask"); $("clearResult").onclick=()=>$("aiResult").classList.add("hidden");
  $("saveHighlight").onclick=async()=>{if(!selected){toast("Select text in the PDF first.");return;}try{await api("/api/highlights/","POST",{document_id:docId,text:selected,page,color:"yellow"});toast("Highlight saved.");loadHighlights();}catch(e){toast(e.message);}};
  $("saveNote").onclick=async()=>{const text=$("noteInput").value.trim();if(!text){toast("Write a note first.");return;}try{await api("/api/notes/","POST",{document_id:docId,text,page});$("noteInput").value="";toast("Note saved.");loadNotes();}catch(e){toast(e.message);}};
  $("addBookmark").onclick=async()=>{const label=prompt("Bookmark label (optional):","");if(label===null)return;try{await api("/api/bookmarks/","POST",{document_id:docId,page,label});toast("Page bookmarked.");loadBookmarks();}catch(e){toast(e.message);}};
  function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
  async function loadNotes(){try{const d=await api("/api/notes/?document_id="+docId);$("notesList").innerHTML=d.notes.length?d.notes.map(n=>`<article class="saved-item"><div class="saved-item-top"><span>PAGE ${n.page}</span><button class="mini-delete" data-note="${n.id}" aria-label="Delete note">×</button></div><p>${escapeHtml(n.text)}</p></article>`).join(""):'<p class="empty-small">Your saved notes will appear here.</p>';document.querySelectorAll("[data-note]").forEach(b=>b.onclick=async()=>{await api("/api/notes/"+b.dataset.note+"/","DELETE");loadNotes();toast("Note deleted.");});}catch(e){}}
  async function loadBookmarks(){try{const d=await api("/api/bookmarks/?document_id="+docId);$("bookmarksList").innerHTML=d.bookmarks.length?d.bookmarks.map(b=>`<article class="saved-item bookmark-item"><button class="bookmark-jump" data-jump="${b.page}"><span>☆ Page ${b.page}</span><small>${escapeHtml(b.label||"Saved page")}</small></button><button class="mini-delete" data-bookmark="${b.id}">×</button></article>`).join(""):'<p class="empty-small">No bookmarks yet.</p>';document.querySelectorAll("[data-jump]").forEach(b=>b.onclick=()=>go(Number(b.dataset.jump)));document.querySelectorAll("[data-bookmark]").forEach(b=>b.onclick=async()=>{await api("/api/bookmarks/"+b.dataset.bookmark+"/","DELETE");loadBookmarks();toast("Bookmark removed.");});}catch(e){}}
  async function loadHighlights(){try{const d=await api("/api/highlights/?document_id="+docId);$("highlightsList").innerHTML=d.highlights.length?d.highlights.map(h=>`<article class="saved-item highlight-item"><div class="saved-item-top"><span>PAGE ${h.page}</span><button class="mini-delete" data-highlight="${h.id}">×</button></div><button class="highlight-jump" data-hjump="${h.page}">${escapeHtml(h.text)}</button></article>`).join(""):'<p class="empty-small">Save selected passages as highlights.</p>';document.querySelectorAll("[data-hjump]").forEach(b=>b.onclick=()=>go(Number(b.dataset.hjump)));document.querySelectorAll("[data-highlight]").forEach(b=>b.onclick=async()=>{await api("/api/highlights/"+b.dataset.highlight+"/","DELETE");loadHighlights();toast("Highlight removed.");});}catch(e){}}
  loadNotes();loadBookmarks();loadHighlights();
})();