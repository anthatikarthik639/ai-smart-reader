import json
import os
from pathlib import Path
import json as json_module
import urllib.error
import urllib.request
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Document, Note, Bookmark, Highlight, ReadingProgress

def signup(request):
    if request.user.is_authenticated:
        return redirect("library")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("library")
    else:
        form = UserCreationForm()
    return render(request, "reader/signup.html", {"form": form})

def home(request):
    if request.user.is_authenticated:
        return redirect("library")
    return redirect("login")

@login_required
def library(request):
    docs = Document.objects.filter(owner=request.user)
    return render(request, "reader/library.html", {"documents": docs})

@login_required
@require_POST
def upload_document(request):
    file = request.FILES.get("pdf")
    if not file:
        messages.error(request, "Choose a PDF file to upload.")
        return redirect("library")
    if not file.name.lower().endswith(".pdf"):
        messages.error(request, "Only PDF files are allowed.")
        return redirect("library")
    if file.size > 30 * 1024 * 1024:
        messages.error(request, "PDF must be smaller than 30 MB.")
        return redirect("library")
    title = (request.POST.get("title") or Path(file.name).stem).strip()[:240]
    doc = Document.objects.create(owner=request.user, title=title or "Untitled PDF", pdf=file, original_name=file.name)
    ReadingProgress.objects.create(owner=request.user, document=doc, page=1)
    return redirect("read_document", document_id=doc.id)

@login_required
def read_document(request, document_id):
    doc = get_object_or_404(Document, pk=document_id, owner=request.user)
    progress, _ = ReadingProgress.objects.get_or_create(owner=request.user, document=doc, defaults={"page": doc.last_page})
    return render(request, "reader/reader.html", {"document": doc, "progress": progress})

@login_required
@require_POST
def delete_document(request, document_id):
    doc = get_object_or_404(Document, pk=document_id, owner=request.user)
    doc.delete()
    messages.success(request, "Document deleted.")
    return redirect("library")

def _body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return {}

def _owned_document(request, data):
    try:
        return Document.objects.get(pk=int(data.get("document_id")), owner=request.user)
    except (Document.DoesNotExist, TypeError, ValueError):
        return None

@login_required
@require_http_methods(["GET", "POST"])
def notes_api(request):
    if request.method == "GET":
        doc_id = request.GET.get("document_id")
        qs = Note.objects.filter(owner=request.user)
        if doc_id:
            qs = qs.filter(document_id=doc_id, document__owner=request.user)
        return JsonResponse({"notes": [{"id":n.id,"text":n.text,"page":n.page,"document_id":n.document_id,"document_title":n.document.title,"created_at":n.created_at.isoformat()} for n in qs]})
    data = _body(request); doc = _owned_document(request, data)
    text = (data.get("text") or "").strip()
    if not doc or not text: return JsonResponse({"error":"A valid document and note text are required."}, status=400)
    note = Note.objects.create(owner=request.user, document=doc, text=text[:12000], page=max(1, int(data.get("page") or 1)))
    return JsonResponse({"id":note.id,"text":note.text,"page":note.page}, status=201)

@login_required
@require_http_methods(["DELETE"])
def note_detail_api(request, note_id):
    note = get_object_or_404(Note, pk=note_id, owner=request.user)
    note.delete()
    return JsonResponse({"ok":True})

@login_required
@require_http_methods(["GET", "POST"])
def bookmarks_api(request):
    if request.method == "GET":
        qs = Bookmark.objects.filter(owner=request.user, document__owner=request.user)
        doc_id = request.GET.get("document_id")
        if doc_id: qs = qs.filter(document_id=doc_id)
        return JsonResponse({"bookmarks":[{"id":b.id,"page":b.page,"label":b.label} for b in qs]})
    data=_body(request); doc=_owned_document(request,data)
    if not doc: return JsonResponse({"error":"Invalid document."},status=400)
    page=max(1,int(data.get("page") or 1)); label=(data.get("label") or "").strip()[:200]
    obj, created=Bookmark.objects.get_or_create(owner=request.user,document=doc,page=page,defaults={"label":label})
    if label and not created: obj.label=label; obj.save(update_fields=["label"])
    return JsonResponse({"id":obj.id,"page":obj.page,"label":obj.label},status=201 if created else 200)

@login_required
@require_http_methods(["DELETE"])
def bookmark_detail_api(request, bookmark_id):
    obj=get_object_or_404(Bookmark,pk=bookmark_id,owner=request.user); obj.delete()
    return JsonResponse({"ok":True})

@login_required
@require_http_methods(["GET", "POST"])
def highlights_api(request):
    if request.method == "GET":
        qs=Highlight.objects.filter(owner=request.user,document__owner=request.user)
        doc_id=request.GET.get("document_id")
        if doc_id: qs=qs.filter(document_id=doc_id)
        return JsonResponse({"highlights":[{"id":h.id,"text":h.text,"page":h.page,"color":h.color} for h in qs]})
    data=_body(request); doc=_owned_document(request,data); text=(data.get("text") or "").strip()
    if not doc or not text: return JsonResponse({"error":"Select text and try again."},status=400)
    color=data.get("color") if data.get("color") in ["yellow","blue","pink","green"] else "yellow"
    h=Highlight.objects.create(owner=request.user,document=doc,text=text[:6000],page=max(1,int(data.get("page") or 1)),color=color)
    return JsonResponse({"id":h.id,"text":h.text,"page":h.page,"color":h.color},status=201)

@login_required
@require_http_methods(["DELETE"])
def highlight_detail_api(request, highlight_id):
    h=get_object_or_404(Highlight,pk=highlight_id,owner=request.user); h.delete()
    return JsonResponse({"ok":True})

@login_required
@require_POST
def progress_api(request):
    data=_body(request); doc=_owned_document(request,data)
    if not doc: return JsonResponse({"error":"Invalid document."},status=400)
    page=max(1,int(data.get("page") or 1))
    progress,_=ReadingProgress.objects.get_or_create(owner=request.user,document=doc)
    progress.page=page; progress.save()
    doc.last_page=page; doc.save(update_fields=["last_page"])
    return JsonResponse({"ok":True,"page":page})

def _ask_ollama(system_prompt, user_prompt):
    """Send a prompt to Ollama running locally; no cloud API key is required."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b").strip() or "llama3.2:3b"
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": 0.4},
    }
    request = urllib.request.Request(
        f"{base_url}/api/chat",
        data=json_module.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json_module.loads(response.read().decode("utf-8"))
        answer = (result.get("message") or {}).get("content", "").strip()
        if not answer:
            raise RuntimeError("Ollama returned an empty response. Try again.")
        return answer
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")[:300]
        if exc.code == 404:
            raise RuntimeError(
                f"Ollama model '{model}' was not found. Open PowerShell and run: ollama pull {model}"
            ) from exc
        raise RuntimeError(f"Ollama returned HTTP {exc.code}: {details}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Cannot connect to Ollama. Install Ollama, start it, and make sure it is running at "
            f"{base_url}. Then run: ollama pull {model}"
        ) from exc
    except TimeoutError as exc:
        raise RuntimeError(
            "Ollama took too long to respond. Try a smaller model such as llama3.2:1b, "
            "or wait for the first model load to finish."
        ) from exc


@login_required
@require_POST
def ai_api(request):
    data=_body(request)
    doc=_owned_document(request,data)
    if not doc: return JsonResponse({"error":"Invalid document."},status=400)
    text=(data.get("text") or "").strip()
    question=(data.get("question") or "").strip()
    action=(data.get("action") or "explain").strip()
    if not text and not question: return JsonResponse({"error":"Select some PDF text or enter a question."},status=400)
    system = "You are a clear, accurate study assistant. Explain at the user's level, use headings and concise examples, and distinguish uncertainty. Do not claim to have read content that was not provided."
    prompts={
        "explain":f"Explain this selected passage clearly with key ideas and a simple example:\n{text}",
        "example":f"Give 2 practical examples that clarify this passage. Explain each briefly:\n{text}",
        "summarize":f"Summarize this passage as concise bullet points and key takeaways:\n{text}",
        "ask":f"Answer the user's question using the supplied passage as context. If it doesn't contain the answer, say so.\nPassage:\n{text}\nQuestion:\n{question}",
    }
    prompt=prompts.get(action, prompts["explain"])
    if action=="ask" and not question: return JsonResponse({"error":"Enter a question first."},status=400)

    provider = os.getenv("AI_PROVIDER", "ollama").strip().lower()
    if provider == "ollama":
        try:
            answer = _ask_ollama(system, prompt)
            return JsonResponse({"answer":answer,"mode":"ollama"})
        except RuntimeError as exc:
            return JsonResponse({"error":str(exc)},status=502)
    elif provider == "openai":
        api_key=os.getenv("OPENAI_API_KEY","").strip()
        if not api_key:
            return JsonResponse({"error":"AI_PROVIDER is set to openai, but OPENAI_API_KEY is empty. Add a key to .env or set AI_PROVIDER=ollama."},status=503)
        try:
            from openai import OpenAI
            client=OpenAI(api_key=api_key)
            result=client.chat.completions.create(model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),messages=[{"role":"system","content":system},{"role":"user","content":prompt}],temperature=0.4)
            answer=result.choices[0].message.content or "No response returned."
            return JsonResponse({"answer":answer,"mode":"ai"})
        except Exception as exc:
            return JsonResponse({"error":"AI request failed. Check your API key, model, internet connection, and account access.","details":str(exc)[:400]},status=502)
    return JsonResponse({"error":"Unknown AI_PROVIDER. Set AI_PROVIDER=ollama in your .env file."},status=500)
