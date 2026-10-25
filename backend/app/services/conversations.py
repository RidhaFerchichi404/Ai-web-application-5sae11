from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User

LOCAL_DISPLAY_NAME = "Local"
DEFAULT_TITLE = "New conversation"


class ConversationNotFound(Exception):
    def __init__(self) -> None:
        super().__init__("Conversation not found.")


class InvalidTitle(Exception):
    def __init__(self) -> None:
        super().__init__("Title cannot be empty.")


def find_local_user(db: Session) -> User | None:
    return db.scalar(
        select(User).where(User.display_name == LOCAL_DISPLAY_NAME).order_by(User.id).limit(1)
    )


def get_or_create_local_user(db: Session) -> User:
    user = find_local_user(db)
    if user is not None:
        return user
    user = User(display_name=LOCAL_DISPLAY_NAME)
    db.add(user)
    db.flush()
    return user


def title_from_message(message: str) -> str:
    stripped = message.strip()
    if not stripped:
        return DEFAULT_TITLE
    first_line = stripped.splitlines()[0].strip()
    if not first_line:
        return DEFAULT_TITLE
    return first_line[:255]


def _touch(conversation: Conversation) -> None:
    conversation.updated_at = func.now()


def _clean_title(title: str) -> str:
    cleaned = title.strip()
    if not cleaned:
        raise InvalidTitle
    return cleaned[:255]


def _like_pattern(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def list_conversations(db: Session, query: str | None) -> list[Conversation]:
    user = find_local_user(db)
    if user is None:
        return []
    stmt = select(Conversation).where(Conversation.user_id == user.id)
    if query and query.strip():
        stmt = stmt.where(Conversation.title.ilike(_like_pattern(query.strip()), escape="\\"))
    stmt = stmt.order_by(Conversation.updated_at.desc(), Conversation.id.desc())
    return list(db.scalars(stmt))


def get_conversation(db: Session, conversation_id: int) -> Conversation:
    user = find_local_user(db)
    conversation = db.get(Conversation, conversation_id) if user is not None else None
    if conversation is None or user is None or conversation.user_id != user.id:
        raise ConversationNotFound
    return conversation


def create_conversation(db: Session, title: str | None, chat_model: str | None) -> Conversation:
    user = get_or_create_local_user(db)
    stored_title = DEFAULT_TITLE if title is None else _clean_title(title)
    conversation = Conversation(user_id=user.id, title=stored_title, chat_model=chat_model)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def update_conversation(
    db: Session,
    conversation_id: int,
    *,
    title: str | None,
    title_set: bool,
    chat_model: str | None,
    chat_model_set: bool,
) -> Conversation:
    conversation = get_conversation(db, conversation_id)
    if title_set:
        if title is None:
            raise InvalidTitle
        conversation.title = _clean_title(title)
    if chat_model_set:
        conversation.chat_model = chat_model
    if title_set or chat_model_set:
        _touch(conversation)
        db.commit()
        db.refresh(conversation)
    return conversation


def delete_conversation(db: Session, conversation_id: int) -> None:
    conversation = get_conversation(db, conversation_id)
    db.execute(delete(Message).where(Message.conversation_id == conversation.id))
    db.expire(conversation, ["messages"])
    db.delete(conversation)
    db.commit()


def list_messages(db: Session, conversation_id: int) -> list[Message]:
    conversation = get_conversation(db, conversation_id)
    return list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at, Message.id)
        )
    )


def begin_turn(db: Session, conversation: Conversation, message: str, model: str) -> list[dict[str, str]]:
    if conversation.title == DEFAULT_TITLE:
        conversation.title = title_from_message(message)
    conversation.chat_model = model
    _touch(conversation)
    db.add(Message(conversation_id=conversation.id, role="user", content=message))
    db.commit()
    rows = db.scalars(
        select(Message)
        .where(
            Message.conversation_id == conversation.id,
            Message.role.in_(("user", "assistant")),
        )
        .order_by(Message.created_at, Message.id)
    )
    return [{"role": row.role, "content": row.content} for row in rows]


def save_assistant(db: Session, conversation_id: int, content: str) -> None:
    if not content:
        return
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        return
    db.add(Message(conversation_id=conversation.id, role="assistant", content=content))
    _touch(conversation)
    db.commit()
