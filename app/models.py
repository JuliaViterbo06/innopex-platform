"""Modelos de dados (o "formato" de cada informação da plataforma).

Estes modelos são o contrato entre o front-end, a API e a camada de dados.
Quando os dados vierem do Databricks, basta a camada de dados devolver
objetos nestes mesmos formatos — as telas não mudam.
"""

from __future__ import annotations

import datetime as dt
from typing import Literal, Optional

from pydantic import BaseModel, Field, computed_field

Phase = Literal["Define", "Measure", "Analyze", "Improve", "Control"]
ProjectType = Literal["Opex", "Inovação"]
Status = Literal["g", "y", "r"]
Role = Literal["Admin", "Master", "Leader", "Viewer"]
MeetingState = Literal["confirmado", "aguardando", "reagendado"]
NotificationKind = Literal["alert", "move", "mail"]
FileType = Literal["PPTX", "PDF", "XLSX", "DOCX"]
Source = Literal["OpEx Global", "Growth Project", "InnOpEx"]


class User(BaseModel):
    name: str
    email: str
    role: Role


class Meeting(BaseModel):
    day: dt.date
    state: MeetingState
    note: Optional[str] = None


class Deck(BaseModel):
    file_type: FileType
    name: str
    version: int = 1
    author: str
    updated_on: dt.date

    @computed_field
    @property
    def days_old(self) -> int:
        return (dt.date.today() - self.updated_on).days


class MeetingNote(BaseModel):
    day: dt.date
    text: str
    return_weeks: int
    author: str


class HistoryEntry(BaseModel):
    at: dt.datetime
    author: str
    text: str


class Project(BaseModel):
    id: str
    name: str
    type: ProjectType
    source: Source = "InnOpEx"
    phase: Phase
    master: str
    leader: str
    value_musd: float = 0.0
    green_musd: float = 0.0
    status: Status = "g"
    summary: str = ""
    last_update: dt.date
    missing_notes: bool = False
    meeting: Optional[Meeting] = None
    decks: list[Deck] = Field(default_factory=list)
    notes: list[MeetingNote] = Field(default_factory=list)
    history: list[HistoryEntry] = Field(default_factory=list)

    @computed_field
    @property
    def stale_days(self) -> int:
        return (dt.date.today() - self.last_update).days


class Notification(BaseModel):
    id: str
    kind: NotificationKind
    title: str
    text: str
    created_at: dt.datetime
    read: bool = False
    project_id: Optional[str] = None


class Config(BaseModel):
    stale_days: int = Field(30, ge=1, le=365)
    max_per_tuesday: int = Field(4, ge=1, le=20)
    meeting_time: str = Field("14:00", pattern=r"^\d{2}:\d{2}$")
    minutes_per_project: int = Field(20, ge=5, le=120)


# ---------- entradas da API (o que o front envia) ----------

class ProjectIn(BaseModel):
    name: str = Field(min_length=1)
    type: ProjectType
    phase: Phase
    master: str = Field(min_length=1)
    leader: str = Field(min_length=1)
    value_musd: float = Field(0.0, ge=0)
    green_musd: float = Field(0.0, ge=0)
    status: Status = "g"
    summary: str = ""


class PhaseMoveIn(BaseModel):
    phase: Phase


class MeetingNoteIn(BaseModel):
    text: str = Field(min_length=1)
    return_weeks: int = Field(ge=1, le=26)


class DeckIn(BaseModel):
    project_id: str
    file_type: FileType
    name: str = Field(min_length=1)


class DevLoginIn(BaseModel):
    name: str = Field(min_length=1)
    email: str
    role: Role


class NopexIn(BaseModel):
    question: str = Field(min_length=1)
