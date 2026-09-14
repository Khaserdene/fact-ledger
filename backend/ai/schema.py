"""AI гаралтын JSON схем v2 + задлагч."""
from typing import List, Optional

from pydantic import BaseModel


class DateValue(BaseModel):
    value: Optional[str] = None      # "1996" | "1996-05" | "1996-05-15" | "1996-1998"


class FactV2(BaseModel):
    fact_type: str = "chronological"  # "chronological" | "biographical"
    date: Optional[str] = None        # уян хатан огнооны string
    fact: str
    source_quote: Optional[str] = None
    role_context: Optional[str] = None
    tags: List[str] = []
    sentiment: Optional[float] = None  # -1.0 … 1.0
    topic: Optional[str] = None        # байр суурийн факт бол сэдэв
    stance: Optional[str] = None       # байр суурь ("дэмжсэн", "эсрэг", ...)


class RelationshipV2(BaseModel):
    target_name: str
    rel_type: str
    target_kind: Optional[str] = None  # "person" | "org" | "company" | "party" | "school" | ...
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    source_quote: Optional[str] = None


class MentionedEntityV2(BaseModel):
    name: str
    entity_type_guess: Optional[str] = None
    quote: Optional[str] = None


class ContradictionV2(BaseModel):
    new_fact_index: Optional[int] = None      # facts жагсаалт дахь индекс
    contradicted_fact_id: str                  # одоо байгаа фактын "F123" id
    kind: Optional[str] = None                 # "date" | "number" | "semantic" | "temporal_position"
    reason: str


class MergeHintV2(BaseModel):
    name_a: str
    name_b: str
    reason: Optional[str] = None


class ExtractionResultV2(BaseModel):
    schema_version: str = "v2"
    facts: List[FactV2] = []
    relationships: List[RelationshipV2] = []
    mentioned_entities: List[MentionedEntityV2] = []
    contradictions: List[ContradictionV2] = []
    merge_hints: List[MergeHintV2] = []
