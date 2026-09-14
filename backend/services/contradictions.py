from sqlalchemy.orm import Session

from models import Contradiction, Fact


def find_fact_by_fact_id(db: Session, fact_id_str: str) -> Fact | None:
    return db.query(Fact).filter(Fact.fact_id == fact_id_str).first()


def save_contradiction(
    db: Session,
    new_fact: Fact,
    contradicted_fact: Fact,
    reason: str,
) -> Contradiction:
    contradiction = Contradiction(
        new_fact_id=new_fact.id,
        contradicted_fact_id=contradicted_fact.id,
        reason=reason,
    )
    db.add(contradiction)
    db.flush()
    return contradiction
