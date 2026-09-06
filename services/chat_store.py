import os
import re
import json
import uuid
from datetime import datetime


CHAT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "chat_sessions"
)

MAX_HISTORY_FOR_AI = 20

# Oturum kimlikleri create_session icinde uretilen 12 haneli hex dizgileri.
# Bunu dayatmak path traversal'i (../../.env gibi) engeller.
_SESSION_ID_RE = re.compile(r"^[a-f0-9]{12}$")


def _ensure_dir():
    os.makedirs(CHAT_DIR, exist_ok=True)


def _session_path(session_id: str) -> str | None:
    """Guvenli oturum yolu; kimlik gecersizse None doner."""
    if not isinstance(session_id, str) or not _SESSION_ID_RE.fullmatch(session_id):
        return None
    return os.path.join(CHAT_DIR, f"{session_id}.json")


def create_session(title: str = "Yeni sohbet") -> dict:
    """Yeni bir sohbet oturumu oluşturur."""

    _ensure_dir()

    session_id = uuid.uuid4().hex[:12]

    now = datetime.now().isoformat(timespec="seconds")

    session = {
        "id": session_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "messages": []
    }

    _save(session)

    return session


def _save(session: dict):
    _ensure_dir()

    with open(
        _session_path(session["id"]),
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            session,
            file,
            ensure_ascii=False,
            indent=2
        )


def get_session(session_id: str):
    """Oturumu döndürür; yoksa veya kimlik geçersizse None döner."""

    path = _session_path(session_id)

    if path is None or not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def list_sessions() -> list:
    """Tüm oturumları en son güncellenenden itibaren listeler."""

    _ensure_dir()

    sessions = []

    for filename in os.listdir(CHAT_DIR):
        if not filename.endswith(".json"):
            continue

        try:
            with open(
                os.path.join(CHAT_DIR, filename),
                "r",
                encoding="utf-8"
            ) as file:
                session = json.load(file)

            sessions.append({
                "id": session["id"],
                "title": session.get("title"),
                "created_at": session.get("created_at"),
                "updated_at": session.get("updated_at"),
                "message_count": len(session.get("messages", []))
            })

        except (json.JSONDecodeError, KeyError):
            continue

    sessions.sort(
        key=lambda s: s.get("updated_at") or "",
        reverse=True
    )

    return sessions


def append_message(session_id: str, role: str, text: str):
    """Oturuma tek bir mesaj ekler."""

    session = get_session(session_id)

    if session is None:
        return None

    session["messages"].append({
        "role": role,
        "text": text,
        "ts": datetime.now().isoformat(timespec="seconds")
    })

    session["updated_at"] = datetime.now().isoformat(
        timespec="seconds"
    )

    _save(session)

    return session


def update_title_if_needed(session_id: str, first_message: str):
    """İlk mesaj geldiyse oturum başlığını günceller."""

    session = get_session(session_id)

    if session is None:
        return

    if session.get("title") in (None, "", "Yeni sohbet"):
        title = first_message.strip().replace("\n", " ")

        if len(title) > 60:
            title = title[:57] + "..."

        session["title"] = title or "Yeni sohbet"

        _save(session)


def delete_session(session_id: str) -> bool:
    """Oturumu siler. Başarılıysa True döner."""

    path = _session_path(session_id)

    if path is None or not os.path.exists(path):
        return False

    os.remove(path)

    return True


def get_ai_history(session: dict) -> list:
    """
    Oturum mesajlarından AI'ya gönderilecek
    geçmişi hazırlar (son MAX_HISTORY_FOR_AI mesaj).
    """

    messages = session.get("messages", [])[-MAX_HISTORY_FOR_AI:]

    return [
        {"role": m["role"], "text": m["text"]}
        for m in messages
        if m.get("role") in ("user", "model")
        and m.get("text")
    ]
