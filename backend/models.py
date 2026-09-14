import json
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


class Source(Base):
    """Эх сурвалж: нийтлэл (scrape), гар тэмдэглэл, баримт бичиг.

    selected_text нь хэшлэгдсэн каноник текст — фактын source_quote
    үүний exact substring байх ёстой (visual anchoring үүнд тулгуурладаг).
    """
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(Text, nullable=False, default="article")  # "article" | "note" | "document"
    url = Column(Text, nullable=True)  # note/document-д NULL
    title = Column(Text, nullable=False)
    author = Column(Text, nullable=True)
    publication_date = Column(Date, nullable=True)
    cleaned_text = Column(Text, nullable=False)
    selected_text = Column(Text, nullable=False)
    raw_hash = Column(Text, nullable=True)
    sha256_hash = Column(Text, nullable=False)
    # Хэвлэлийн хандлага: эерэг = дэмжсэн, сөрөг = шүүмжилсэн, 0 = төвийг сахисан
    bias_score = Column(Float, nullable=True)
    # Найдвартай байдал 0.0–1.0
    reliability_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=func.now())

    facts = relationship("Fact", back_populates="source")


class Entity(Base):
    """Нэгдсэн субъект: хүн, байгууллага, компани, нам, сургууль г.м."""
    __tablename__ = "entities"

    TYPES = ("person", "org", "company", "fund", "state", "party", "school", "location", "government", "parliament", "other")

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)  # unique биш: давхардал merge саналаар шийдэгдэнэ
    entity_type = Column(Text, nullable=False, default="person")
    description = Column(Text, nullable=True)
    tldr_summary = Column(Text, nullable=True)
    # Дурдагдсанаас автоматаар үүссэн, хүн хараахан баяжуулаагүй
    is_stub = Column(Boolean, nullable=False, default=False)
    # Нэгтгэгдсэн бол хаана очсоныг заана (tombstone redirect)
    merged_into_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    facts = relationship("Fact", back_populates="entity")
    aliases = relationship("EntityAlias", back_populates="entity", cascade="all, delete-orphan")
    merged_into = relationship("Entity", remote_side=[id])

    @property
    def alias_list(self) -> list[str]:
        return [a.alias for a in self.aliases]


class EntityAlias(Base):
    """Нэрийн хувилбар: албан тушаал, хоч, товчлол, өөр бичлэг г.м."""
    __tablename__ = "entity_aliases"

    KINDS = ("spelling", "initials", "position", "nickname", "patronymic", "merged", "other")

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    alias = Column(Text, nullable=False)          # бичигдсэн хэлбэрээрээ
    alias_norm = Column(Text, nullable=False, index=True)  # services.matching.normalize_name үр дүн
    kind = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    entity = relationship("Entity", back_populates="aliases")

    __table_args__ = (UniqueConstraint("entity_id", "alias_norm"),)


class Fact(Base):
    __tablename__ = "facts"

    id = Column(Integer, primary_key=True, index=True)
    fact_id = Column(Text, unique=True, nullable=True)  # "F{id}" — flush-ийн дараа онооно
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    fact_type = Column(Text, nullable=False)  # "biographical" | "chronological"
    fact_date = Column(Date, nullable=True)
    # "day" | "month" | "year" | "range" — fact_date байвал заавал
    date_precision = Column(Text, nullable=True)
    fact_date_end = Column(Date, nullable=True)  # precision="range" үед
    fact_text = Column(Text, nullable=False)
    source_quote = Column(Text, nullable=True)
    role_context = Column(Text, nullable=True)
    _tags = Column("tags", Text, default="[]")
    # Байр суурийн факт: сэдэв + байр суурь (цаг хугацааны зөрчил илрүүлэхэд)
    topic = Column(Text, nullable=True)
    stance = Column(Text, nullable=True)
    # Sentiment: -1.0 (сөрөг/улаан) … +1.0 (эерэг/ногоон)
    sentiment_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=func.now())

    entity = relationship("Entity", back_populates="facts")
    source = relationship("Source", back_populates="facts")

    contradictions_as_new = relationship(
        "Contradiction", foreign_keys="Contradiction.new_fact_id", back_populates="new_fact"
    )
    contradictions_as_old = relationship(
        "Contradiction", foreign_keys="Contradiction.contradicted_fact_id", back_populates="contradicted_fact"
    )

    @property
    def tags(self):
        return json.loads(self._tags or "[]")

    @tags.setter
    def tags(self, value):
        self._tags = json.dumps(value, ensure_ascii=False)

    @property
    def contradictions(self):
        """Баталгаажсан (confirmed) зөрчлүүд — dismiss/resolved хийгдсэнийг орно."""
        return [c for c in self.contradictions_as_new if c.status == "confirmed"] + [
            c for c in self.contradictions_as_old if c.status == "confirmed"
        ]

    @property
    def has_contradiction(self):
        return bool(self.contradictions)


class Relationship(Base):
    """Графын ирмэг: субъект → өөр субъект (цаг хугацааны интервалтай)."""
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)  # эх сурвалж
    target_name = Column(Text, nullable=False)  # бичигдсэн хэлбэрээрээ
    target_entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True, index=True)
    rel_type = Column(Text, nullable=False)  # "дарга", "зөвлөх", "түнш", ...
    target_kind = Column(Text, nullable=True)  # entity_type таамаг ("person" | "org" | ...)
    start_date = Column(Date, nullable=True)
    start_precision = Column(Text, nullable=True)
    end_date = Column(Date, nullable=True)
    end_precision = Column(Text, nullable=True)
    source_quote = Column(Text, nullable=True)
    _dismissed_links = Column("dismissed_links", Text, default="[]")  # татгалзсан entity id-ууд
    created_at = Column(DateTime, default=func.now())

    source_entity = relationship("Entity", foreign_keys=[source_entity_id])
    target_entity = relationship("Entity", foreign_keys=[target_entity_id])
    source = relationship("Source")

    @property
    def dismissed_links(self):
        return json.loads(self._dismissed_links or "[]")

    @dismissed_links.setter
    def dismissed_links(self, value):
        self._dismissed_links = json.dumps(value)


class Contradiction(Base):
    __tablename__ = "contradictions"

    STATUSES = ("confirmed", "dismissed", "resolved")

    id = Column(Integer, primary_key=True, index=True)
    new_fact_id = Column(Integer, ForeignKey("facts.id"), nullable=False)
    contradicted_fact_id = Column(Integer, ForeignKey("facts.id"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="confirmed")
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    new_fact = relationship("Fact", foreign_keys=[new_fact_id], back_populates="contradictions_as_new")
    contradicted_fact = relationship("Fact", foreign_keys=[contradicted_fact_id], back_populates="contradictions_as_old")


class ExtractionBatch(Base):
    """AI ажиллагааны нэг багц: промпт → хариу → suggestions."""
    __tablename__ = "extraction_batches"

    KINDS = ("extraction", "sweep_fuzzy", "sweep_ai")
    STATUSES = ("awaiting_response", "ready_for_review", "completed", "failed")

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(Text, nullable=False, default="extraction")
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    provider = Column(Text, nullable=False)  # "manual" | "gemini" | "claude" | "system"
    model = Column(Text, nullable=True)
    prompt_version = Column(Text, nullable=False, default="v2")
    prompt_text = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)  # аудит: хэзээ ч устгахгүй
    status = Column(Text, nullable=False, default="awaiting_response")
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    entity = relationship("Entity")
    source = relationship("Source")
    suggestions = relationship("Suggestion", back_populates="batch")


class Suggestion(Base):
    """AI-ийн санал болгосон нэгж — батлагдсаны дараа л ledger-т бичигдэнэ."""
    __tablename__ = "suggestions"

    KINDS = ("fact", "relationship", "entity", "contradiction", "merge", "link", "alias")
    STATUSES = ("pending", "accepted", "rejected")
    DEDUP_STATUSES = ("new", "possible_duplicate", "exact_duplicate")

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("extraction_batches.id"), nullable=False, index=True)
    kind = Column(Text, nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    _payload = Column("payload", Text, nullable=False)
    dedup_status = Column(Text, nullable=False, default="new")
    dedup_ref_id = Column(Integer, nullable=True)  # таарсан одоогийн мөрийн id
    dedup_score = Column(Float, nullable=True)
    status = Column(Text, nullable=False, default="pending")
    edited = Column(Boolean, nullable=False, default=False)
    accepted_kind = Column(Text, nullable=True)
    accepted_id = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    batch = relationship("ExtractionBatch", back_populates="suggestions")
    entity = relationship("Entity")

    @property
    def payload(self):
        return json.loads(self._payload or "{}")

    @payload.setter
    def payload(self, value):
        self._payload = json.dumps(value, ensure_ascii=False)


class Mention(Base):
    """Субъект X эх сурвалж Y-д дурдагдсан бүртгэл (самнах + тоолуурт)."""
    __tablename__ = "mentions"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    name_as_written = Column(Text, nullable=False)
    quote = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    source = relationship("Source")
    entity = relationship("Entity")

    __table_args__ = (UniqueConstraint("source_id", "entity_id", "name_as_written"),)
