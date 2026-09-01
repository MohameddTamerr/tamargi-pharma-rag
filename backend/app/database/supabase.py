from datetime import date, datetime
from app.config import settings

try:
    from supabase import create_client, Client
    HAS_SUPABASE_LIB = True
except ImportError:
    HAS_SUPABASE_LIB = False
    Client = None

# In-memory fallback log for offline / unit-testing environments when Supabase client is not connected
IN_MEMORY_UNANSWERED_LOG = []

def get_supabase_client():
    if HAS_SUPABASE_LIB and settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return None

def calculate_age(birth_date: str | date) -> int | None:
    """
    Calculates age dynamically from birth_date (DATE).
    Age is never stored statically in the database.
    """
    if not birth_date:
        return None
    try:
        if isinstance(birth_date, str):
            bdate = datetime.strptime(birth_date, "%Y-%m-%d").date()
        else:
            bdate = birth_date
        today = date.today()
        return today.year - bdate.year - ((today.month, today.day) < (bdate.month, bdate.day))
    except Exception as e:
        print(f"[calculate_age Error] {e}")
        return None

def save_chat_message(
    conversation_id: str,
    user_id: str,
    role: str,
    content: str,
    input_type: str = "text",
    sources: list[dict] = None
) -> dict:
    import uuid
    client = get_supabase_client()
    if not client:
        from app.api.conversations import IN_MEMORY_MESSAGES, IN_MEMORY_CONVERSATIONS
        msg_id = str(uuid.uuid4())
        msg_data = {
            "id": msg_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "input_type": input_type,
            "message_sources": sources or [],
            "created_at": datetime.now().isoformat()
        }
        if conversation_id not in IN_MEMORY_MESSAGES:
            IN_MEMORY_MESSAGES[conversation_id] = []
        IN_MEMORY_MESSAGES[conversation_id].append(msg_data)

        user_convs = IN_MEMORY_CONVERSATIONS.setdefault(user_id, [])
        if not any(c.get("id") == conversation_id for c in user_convs):
            user_convs.append({
                "id": conversation_id,
                "user_id": user_id,
                "title": content[:40] if role == "user" else "محادثة طبية",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
        return {"status": "success", "message_id": msg_id}

    try:
        msg_resp = client.table("messages").insert({
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "input_type": input_type
        }).execute()

        msg_id = msg_resp.data[0]["id"] if msg_resp.data else None

        if msg_id and sources:
            source_rows = []
            for src in sources:
                source_rows.append({
                    "message_id": msg_id,
                    "evidence_id": src["evidenceId"],
                    "file_name": src["fileName"],
                    "page_number": src["pageNumber"],
                    "chunk_id": src.get("chunkId"),
                    "rank": src["rank"],
                    "score": src.get("score", 0.0),
                    "excerpt": src["excerpt"]
                })
            client.table("message_sources").insert(source_rows).execute()

        return {"status": "success", "message_id": msg_id}
    except Exception as e:
        print(f"[Supabase Error] Failed to save chat message: {e}")
        return {"status": "error", "error": str(e)}

def log_unanswered_query(
    original_query: str,
    normalized_query: str = None,
    language_detected: str = None,
    user_id: str = None,
    conversation_id: str = None,
    message_id: str = None,
    top_sources: list[dict] = None,
    top_retrieved_sources: list[dict] = None,
    reason: str = "insufficient_evidence"
) -> dict:
    """
    Logs unanswered / insufficient evidence user queries into public.unanswered_queries.
    Only stores source metadata (file_name, page_number, chunk_id, rank, score). NO large excerpts.
    """
    compact_sources = []
    sources_to_use = top_sources or top_retrieved_sources or []
    for src in sources_to_use:
        compact_sources.append({
            "file_name": src.get("fileName", src.get("file", "")),
            "page_number": src.get("pageNumber", src.get("page", 0)),
            "chunk_id": src.get("chunkId", src.get("chunk_id", None)),
            "rank": src.get("rank", 0),
            "score": src.get("score", src.get("reranker_score", src.get("rrf_score", 0.0)))
        })

    record = {
        "original_query": original_query,
        "normalized_query": normalized_query,
        "language_detected": language_detected,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "message_id": message_id,
        "reason": reason,
        "top_retrieved_sources": compact_sources
    }

    # Record in in-memory fallback log for testing & offline verification
    IN_MEMORY_UNANSWERED_LOG.append(record)

    client = get_supabase_client()
    if not client:
        return True

    try:
        res = client.table("unanswered_queries").insert(record).execute()
        return True
    except Exception as e:
        print(f"[Supabase Error] Failed to log unanswered query: {e}")
        return False
