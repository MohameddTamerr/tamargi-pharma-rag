import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.auth.supabase_auth import get_current_user, AuthenticatedUser
from app.database.supabase import get_supabase_client

router = APIRouter()

# In-memory store for offline/local execution
IN_MEMORY_CONVERSATIONS: Dict[str, List[Dict[str, Any]]] = {} # user_id -> list of convs
IN_MEMORY_MESSAGES: Dict[str, List[Dict[str, Any]]] = {} # conv_id -> list of messages

class CreateConversationRequest(BaseModel):
    user_id: Optional[str] = None # Ignored for auth, overridden by verified JWT sub
    title: Optional[str] = "محادثة جديدة"

class RenameConversationRequest(BaseModel):
    title: str

class FeedbackRequest(BaseModel):
    message_id: str
    user_id: Optional[str] = None # Ignored for auth, overridden by verified JWT sub
    rating: int # 1 or -1
    comment: Optional[str] = None

@router.get("")
def get_conversations(
    user_id: Optional[str] = Query(None, description="Optional legacy query param, overridden by verified JWT sub"),
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Retrieves all conversations for the authenticated Supabase user, ordered by recent."""
    authoritative_user_id = user.id
    client = get_supabase_client()
    if client:
        try:
            res = client.table("conversations").select("*").eq("user_id", authoritative_user_id).order("updated_at", desc=True).execute()
            if res.data is not None:
                return res.data
        except Exception:
            pass

    return IN_MEMORY_CONVERSATIONS.get(authoritative_user_id, [])

@router.post("")
def create_conversation(
    req: CreateConversationRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Creates a new conversation for the authenticated Supabase user."""
    authoritative_user_id = user.id
    conv_id = str(uuid.uuid4())
    now_iso = datetime.now().isoformat()
    conv_data = {
        "id": conv_id,
        "user_id": authoritative_user_id,
        "title": req.title or "محادثة جديدة",
        "created_at": now_iso,
        "updated_at": now_iso
    }

    client = get_supabase_client()
    if client:
        try:
            res = client.table("conversations").insert(conv_data).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception:
            pass

    if authoritative_user_id not in IN_MEMORY_CONVERSATIONS:
        IN_MEMORY_CONVERSATIONS[authoritative_user_id] = []
    IN_MEMORY_CONVERSATIONS[authoritative_user_id].insert(0, conv_data)
    return conv_data

@router.get("/{conv_id}/messages")
def get_conversation_messages(
    conv_id: str,
    user_id: Optional[str] = Query(None),
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Retrieves messages for a specific conversation belonging to the authenticated Supabase user."""
    authoritative_user_id = user.id
    client = get_supabase_client()
    if client:
        try:
            res = client.table("messages").select("*, message_sources(*)").eq("conversation_id", conv_id).eq("user_id", authoritative_user_id).order("created_at", desc=False).execute()
            if res.data is not None:
                return res.data
        except Exception:
            pass

    user_convs = IN_MEMORY_CONVERSATIONS.get(authoritative_user_id, [])
    if not any(c.get("id") == conv_id for c in user_convs):
        raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")

    return IN_MEMORY_MESSAGES.get(conv_id, [])

@router.patch("/{conv_id}")
def rename_conversation(
    conv_id: str,
    req: RenameConversationRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Renames a conversation belonging to the authenticated Supabase user."""
    authoritative_user_id = user.id
    client = get_supabase_client()
    if client:
        try:
            client.table("conversations").update({"title": req.title, "updated_at": datetime.now().isoformat()}).eq("id", conv_id).eq("user_id", authoritative_user_id).execute()
        except Exception:
            pass

    user_convs = IN_MEMORY_CONVERSATIONS.get(authoritative_user_id, [])
    for c in user_convs:
        if c.get("id") == conv_id:
            c["title"] = req.title
            c["updated_at"] = datetime.now().isoformat()
            return c

    raise HTTPException(status_code=404, detail="Conversation not found or unauthorized")

@router.delete("/{conv_id}")
def delete_conversation(
    conv_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Deletes a conversation and associated messages strictly for its owner."""
    authoritative_user_id = user.id
    client = get_supabase_client()
    if client:
        try:
            client.table("messages").delete().eq("conversation_id", conv_id).eq("user_id", authoritative_user_id).execute()
            client.table("conversations").delete().eq("id", conv_id).eq("user_id", authoritative_user_id).execute()
        except Exception:
            pass

    user_convs = IN_MEMORY_CONVERSATIONS.get(authoritative_user_id, [])
    IN_MEMORY_CONVERSATIONS[authoritative_user_id] = [c for c in user_convs if c.get("id") != conv_id]
    if conv_id in IN_MEMORY_MESSAGES:
        del IN_MEMORY_MESSAGES[conv_id]

    return {"status": "deleted", "id": conv_id}

@router.post("/feedback")
def submit_feedback(
    request: FeedbackRequest,
    user: AuthenticatedUser = Depends(get_current_user)
):
    authoritative_user_id = user.id
    client = get_supabase_client()
    if not client:
        return {"status": "mock", "message": "Feedback received (Supabase disabled)"}

    try:
        res = client.table("feedback").insert({
            "message_id": request.message_id,
            "user_id": authoritative_user_id,
            "rating": request.rating,
            "comment": request.comment
        }).execute()
        return {"status": "success", "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
