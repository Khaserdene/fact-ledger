from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ── Scrape ────────────────────────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    url: str


class ScrapedBlock(BaseModel):
    type: str   # "h1".."h6", "p", "li", "blockquote"
    text: str


class ScrapeResponse(BaseModel):
    title: str
    pub_date: Optional[str]
    blocks: List[ScrapedBlock]
    trafilatura_text: Optional[str] = None
    raw_html: Optional[str] = None


# ── Source (нийтлэл / тэмдэглэл / баримт бичиг) ──────────────────────────────

class SourceCreate(BaseModel):
    """source_type='article': url + selected_blocks шаардлагатай.
    source_type='note'|'document': body шаардлагатай, url сонголттой."""
    source_type: str = "article"
    title: str
    url: Optional[str] = None
    author: Optional[str] = None
    pub_date: Optional[str] = None
    selected_blocks: Optional[List[str]] = None  # article
    raw_text: Optional[str] = None               # article (trafilatura бүтэн текст)
    body: Optional[str] = None                   # note/document


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_type: str
    url: Optional[str]
    title: str
    author: Optional[str]
    publication_date: Optional[date]
    selected_text: str
    raw_hash: Optional[str]
    sha256_hash: str
    bias_score: Optional[float]
    reliability_score: Optional[float]
    created_at: datetime


class SourceWithFacts(SourceOut):
    cleaned_text: str
    facts: List["FactOut"] = []


class VerifyResponse(BaseModel):
    unchanged: bool
    live_raw_hash: str
    message: str
    diff_html: Optional[str] = None


# ── Entity ────────────────────────────────────────────────────────────────────

class AliasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alias: str
    kind: Optional[str]


class AliasCreate(BaseModel):
    alias: str
    kind: Optional[str] = None


class EntityCreate(BaseModel):
    name: str
    entity_type: str = "person"
    description: Optional[str] = None
    aliases: List[str] = []


class EntityUpdate(BaseModel):
    name: Optional[str] = None
    entity_type: Optional[str] = None
    description: Optional[str] = None
    tldr_summary: Optional[str] = None
    is_stub: Optional[bool] = None


class EntityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    entity_type: str
    description: Optional[str]
    tldr_summary: Optional[str]
    is_stub: bool
    merged_into_id: Optional[int]
    aliases: List[AliasOut] = []
    party_name: Optional[str] = None
    created_at: datetime


class MergeRequest(BaseModel):
    source_entity_id: int  # энэ субъект survivor руу нэгдэнэ


class MergeResult(BaseModel):
    survivor_id: int
    merged_id: int
    moved_facts: int
    moved_relationships: int
    moved_aliases: int
    moved_mentions: int


# ── Fact ──────────────────────────────────────────────────────────────────────

class FactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fact_id: Optional[str]
    entity_id: int
    source_id: Optional[int]
    fact_type: str
    fact_date: Optional[date]
    date_precision: Optional[str]
    fact_date_end: Optional[date]
    fact_text: str
    source_quote: Optional[str]
    role_context: Optional[str]
    tags: List[str]
    topic: Optional[str]
    stance: Optional[str]
    has_contradiction: bool
    contradictions: List["ContradictionOut"] = []
    sentiment_score: Optional[float] = None
    created_at: datetime


class FactCreate(BaseModel):
    entity_id: int
    fact_type: str  # "biographical" | "chronological"
    fact_text: str
    date_input: Optional[str] = None  # "1996" | "1996-05" | "1996-05-15" | "1996-1998"
    source_id: Optional[int] = None
    source_quote: Optional[str] = None
    role_context: Optional[str] = None
    tags: List[str] = []
    topic: Optional[str] = None
    stance: Optional[str] = None
    sentiment_score: Optional[float] = None


class FactUpdate(BaseModel):
    fact_type: Optional[str] = None
    fact_text: Optional[str] = None
    date_input: Optional[str] = None
    source_id: Optional[int] = None
    source_quote: Optional[str] = None
    role_context: Optional[str] = None
    tags: Optional[List[str]] = None
    topic: Optional[str] = None
    stance: Optional[str] = None
    sentiment_score: Optional[float] = None


# ── Relationship ──────────────────────────────────────────────────────────────

class RelationshipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_entity_id: int
    source_id: Optional[int]
    target_name: str
    target_entity_id: Optional[int]
    rel_type: str
    target_kind: Optional[str]
    start_date: Optional[date]
    start_precision: Optional[str]
    end_date: Optional[date]
    end_precision: Optional[str]
    source_quote: Optional[str]
    created_at: datetime


class RelationshipCreate(BaseModel):
    source_entity_id: int
    target_entity_id: Optional[int] = None
    target_name: Optional[str] = None  # target_entity_id байхгүй бол шаардлагатай
    rel_type: str
    target_kind: Optional[str] = None
    start_date_input: Optional[str] = None
    end_date_input: Optional[str] = None
    source_id: Optional[int] = None
    source_quote: Optional[str] = None


class RelationshipCandidate(BaseModel):
    id: int                      # relationship id
    source_entity_id: int        # "from" субъект
    source_entity_name: str
    target_name: str
    rel_type: str
    target_kind: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    source_quote: Optional[str]
    source_id: Optional[int]


class LinkBody(BaseModel):
    target_entity_id: int


class DismissBody(BaseModel):
    entity_id: int


# ── Contradiction ─────────────────────────────────────────────────────────────

class ContradictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    new_fact_id: int
    contradicted_fact_id: int
    reason: str
    status: str
    resolution_note: Optional[str]
    created_at: datetime


class ContradictionUpdate(BaseModel):
    status: Optional[str] = None  # "confirmed" | "dismissed" | "resolved"
    resolution_note: Optional[str] = None


# ── AI JSON import (Phase 4-т suggestions-ээр солигдоно) ─────────────────────

class NewBioFact(BaseModel):
    fact: str
    source_quote: Optional[str] = None
    role_context: Optional[str] = None
    tags: List[str] = []


class NewChronFact(BaseModel):
    date: Optional[str] = None
    fact: str
    source_quote: Optional[str] = None
    role_context: Optional[str] = None
    tags: List[str] = []


class ContradictionDetected(BaseModel):
    new_fact_quote: str
    contradicted_fact_id: str
    reason: str


class NewRelationship(BaseModel):
    target_name: str
    rel_type: str
    target_kind: Optional[str] = None       # "person" | "org" | ...
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    source_quote: Optional[str] = None


class ImportFactsPayload(BaseModel):
    article_id: Optional[int] = None
    new_biographical_facts: List[NewBioFact] = []
    new_chronological_facts: List[NewChronFact] = []
    new_relationships: List[NewRelationship] = []
    contradictions_detected: List[ContradictionDetected] = []


class ImportFactsResult(BaseModel):
    added_facts: int
    skipped_duplicates: int = 0
    added_relationships: int = 0
    contradictions_saved: int
    skipped_contradictions: List[str] = []


SourceWithFacts.model_rebuild()
FactOut.model_rebuild()
