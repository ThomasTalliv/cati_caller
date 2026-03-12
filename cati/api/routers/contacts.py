"""Contacts and Do-Not-Call (DNC) management endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cati.api.dependencies import db_session, require_api_key
from cati.survey.models import Contact
from cati.utils.phone import is_valid_e164, normalize_e164

router = APIRouter(
    prefix="/api/v1/contacts",
    tags=["contacts"],
    dependencies=[Depends(require_api_key)],
)


class ContactCreate(BaseModel):
    phone_number: str
    name: str | None = None
    do_not_call: bool = False
    metadata: dict[str, Any] = {}


class ContactUpdate(BaseModel):
    name: str | None = None
    do_not_call: bool | None = None
    metadata: dict[str, Any] | None = None


class ContactOut(BaseModel):
    id: uuid.UUID
    phone_number: str
    name: str | None
    do_not_call: bool
    metadata: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_contact(cls, c: Contact) -> "ContactOut":
        return cls(
            id=c.id,
            phone_number=c.phone_number,
            name=c.name,
            do_not_call=c.do_not_call,
            metadata=c.metadata_,
            created_at=c.created_at,
        )


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactCreate,
    session: AsyncSession = Depends(db_session),
) -> ContactOut:
    e164 = normalize_e164(body.phone_number)
    if not is_valid_e164(e164):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid phone number: {body.phone_number!r}",
        )
    contact = Contact(
        phone_number=e164,
        name=body.name,
        do_not_call=body.do_not_call,
        metadata_=body.metadata,
    )
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return ContactOut.from_orm_contact(contact)


@router.get("", response_model=list[ContactOut])
async def list_contacts(
    dnc_only: bool = False,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(db_session),
) -> list[ContactOut]:
    q = select(Contact).order_by(Contact.created_at.desc()).limit(limit).offset(offset)
    if dnc_only:
        q = q.where(Contact.do_not_call.is_(True))
    result = await session.execute(q)
    return [ContactOut.from_orm_contact(c) for c in result.scalars().all()]


@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact(
    contact_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> ContactOut:
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return ContactOut.from_orm_contact(contact)


@router.patch("/{contact_id}", response_model=ContactOut)
async def update_contact(
    contact_id: uuid.UUID,
    body: ContactUpdate,
    session: AsyncSession = Depends(db_session),
) -> ContactOut:
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    if body.name is not None:
        contact.name = body.name
    if body.do_not_call is not None:
        contact.do_not_call = body.do_not_call
    if body.metadata is not None:
        contact.metadata_ = body.metadata
    await session.commit()
    await session.refresh(contact)
    return ContactOut.from_orm_contact(contact)


@router.post("/{contact_id}/do-not-call", status_code=status.HTTP_204_NO_CONTENT)
async def set_dnc(
    contact_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> None:
    """Add a contact to the Do-Not-Call list."""
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    contact.do_not_call = True
    await session.commit()


@router.delete("/{contact_id}/do-not-call", status_code=status.HTTP_204_NO_CONTENT)
async def clear_dnc(
    contact_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> None:
    """Remove a contact from the Do-Not-Call list."""
    result = await session.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    contact.do_not_call = False
    await session.commit()


@router.post("/check-dnc", response_model=dict)
async def check_dnc_by_phone(
    body: dict,
    session: AsyncSession = Depends(db_session),
) -> dict:
    """Check whether a phone number is on the DNC list."""
    phone = body.get("phone_number", "")
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="phone_number is required",
        )
    e164 = normalize_e164(phone)
    result = await session.execute(
        select(Contact).where(Contact.phone_number == e164, Contact.do_not_call.is_(True))
    )
    is_dnc = result.scalar_one_or_none() is not None
    return {"phone_number": e164, "do_not_call": is_dnc}
