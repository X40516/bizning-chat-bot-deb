"""
Barcha database CRUD operatsiyalari.
"""
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Content, Couple, Message, PairRequest, User


# ---------- Foydalanuvchilar ----------

async def get_or_create_user(
    session: AsyncSession, telegram_id: int, username: str | None, first_name: str
) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, username=username, first_name=first_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        changed = False
        if user.username != username:
            user.username = username
            changed = True
        if user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if changed:
            await session.commit()
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(func.lower(User.username) == username.lower()))
    return result.scalar_one_or_none()


async def touch_last_activity(session: AsyncSession, user_id: int) -> None:
    await session.execute(
        update(User).where(User.id == user_id).values(last_activity=datetime.now(timezone.utc))
    )
    await session.commit()


# ---------- Juftliklar ----------

async def get_couple_for_user(session: AsyncSession, user_id: int) -> Couple | None:
    result = await session.execute(
        select(Couple).where(
            Couple.is_active.is_(True),
            ((Couple.user1_id == user_id) | (Couple.user2_id == user_id)),
        )
    )
    return result.scalar_one_or_none()


async def get_partner_user(session: AsyncSession, couple: Couple, self_user_id: int) -> User | None:
    partner_id = couple.user2_id if couple.user1_id == self_user_id else couple.user1_id
    return await get_user_by_id(session, partner_id)


async def create_couple(session: AsyncSession, user1_id: int, user2_id: int) -> Couple:
    couple = Couple(user1_id=user1_id, user2_id=user2_id)
    session.add(couple)
    await session.commit()
    await session.refresh(couple)
    return couple


async def deactivate_couple(session: AsyncSession, couple_id: int) -> None:
    await session.execute(update(Couple).where(Couple.id == couple_id).values(is_active=False))
    await session.commit()


# ---------- Ulanish so'rovlari ----------

async def create_pair_request(session: AsyncSession, from_user_id: int, to_user_id: int) -> PairRequest:
    req = PairRequest(from_user_id=from_user_id, to_user_id=to_user_id, status="pending")
    session.add(req)
    await session.commit()
    await session.refresh(req)
    return req


async def get_pair_request(session: AsyncSession, request_id: int) -> PairRequest | None:
    result = await session.execute(select(PairRequest).where(PairRequest.id == request_id))
    return result.scalar_one_or_none()


async def update_request_status(session: AsyncSession, request_id: int, status: str) -> None:
    await session.execute(update(PairRequest).where(PairRequest.id == request_id).values(status=status))
    await session.commit()


# ---------- Xabarlar (log) ----------

async def log_message(
    session: AsyncSession, couple_id: int, sender_id: int, message_type: str, telegram_message_id: int
) -> None:
    session.add(
        Message(
            couple_id=couple_id,
            sender_id=sender_id,
            message_type=message_type,
            telegram_message_id=telegram_message_id,
        )
    )
    await session.commit()


# ---------- Kontent (kino/musiqa/rasm/video) ----------

async def add_content(
    session: AsyncSession,
    content_type: str,
    title: str,
    description: str,
    telegram_file_id: str,
    cover_file_id: str | None = None,
    artist: str | None = None,
    genre: str | None = None,
) -> Content:
    item = Content(
        type=content_type,
        title=title,
        description=description,
        telegram_file_id=telegram_file_id,
        cover_file_id=cover_file_id,
        artist=artist,
        genre=genre,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def get_content_list(session: AsyncSession, content_type: str) -> list[Content]:
    result = await session.execute(
        select(Content).where(Content.type == content_type).order_by(Content.created_at.desc())
    )
    return list(result.scalars().all())


async def get_content_by_id(session: AsyncSession, content_id: int) -> Content | None:
    result = await session.execute(select(Content).where(Content.id == content_id))
    return result.scalar_one_or_none()


async def delete_content(session: AsyncSession, content_id: int) -> None:
    item = await get_content_by_id(session, content_id)
    if item:
        await session.delete(item)
        await session.commit()


async def update_content_field(session: AsyncSession, content_id: int, field: str, value: str) -> None:
    await session.execute(update(Content).where(Content.id == content_id).values(**{field: value}))
    await session.commit()
