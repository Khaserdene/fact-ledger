"""Auth and Session Management Router.

Хэрэглэгчийн нэвтрэлтийг шалгах, token үүсгэх, идэвхтэй сессүүдийг хянах,
хүчингүй болгох (terminate), хугацааг сунгах (extend) API-ууд.
"""
from datetime import datetime, timedelta, timezone
import secrets
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_SALT = "MNT_FL_INTEL_K99"
MASTER_CODE = "factledger2026"


def _djb2(s: str) -> int:
    h = 5381
    for c in s:
        h = ((h * 33) & 0xFFFFFFFF) ^ ord(c)
        h &= 0xFFFFFFFF
    return h


def _lcg_mix(n: int) -> int:
    return ((n * 1664525) + 1013904223) & 0xFFFFFFFF


def _to_base36(num: int) -> str:
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if num == 0:
        return "0"
    res = []
    while num > 0:
        res.append(chars[num % 36])
        num //= 36
    return "".join(reversed(res))


def generate_time_code(dt: Optional[datetime] = None) -> str:
    """Тухайн UTC цаг үед хамааралтай 6 тэмдэгттэй нэвтрэх код үүсгэнэ."""
    now = dt or datetime.now(timezone.utc)
    yyyy = now.year
    mm = f"{now.month:02d}"
    dd = f"{now.day:02d}"
    block = now.hour // 2
    raw = f"{SECRET_SALT}|{yyyy}-{mm}-{dd}|{block:02d}"
    mixed = _lcg_mix(_djb2(raw))
    b36 = 36**6
    val = mixed % b36
    return _to_base36(val).rjust(6, "0")


def get_valid_codes_now() -> set[str]:
    """Одоогийн болон 2 цагийн өмнөх/дараагийн блокийн хүчинтэй кодуудыг буцаана (цагийн зөрүүний хамгаалалт)."""
    now = datetime.now(timezone.utc)
    curr = generate_time_code(now)
    prev = generate_time_code(now - timedelta(hours=1, minutes=50))
    nxt = generate_time_code(now + timedelta(hours=2))
    return {curr.upper(), prev.upper(), nxt.upper()}


def _extract_token(
    authorization: Optional[str] = Header(None),
    x_session_token: Optional[str] = Header(None),
) -> Optional[str]:
    if x_session_token:
        return x_session_token.strip()
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1].strip()
        return authorization.strip()
    return None


@router.post("/login", response_model=schemas.LoginResponse)
def login(
    req: schemas.LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    code_raw = req.code.strip()
    if not code_raw:
        raise HTTPException(status_code=400, detail="Нэвтрэх код хоосон байна.")

    is_master = code_raw.lower() == MASTER_CODE.lower()
    valid_time_codes = get_valid_codes_now()
    is_time_code = code_raw.upper() in valid_time_codes

    if not is_master and not is_time_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Нэвтрэх код буруу эсвэл хугацаа нь дууссан байна.",
        )

    code_type = "master" if is_master else "time_code"
    code_display = "MASTER" if is_master else code_raw.upper()[:6]

    # Төхөөрөмж болон IP мэдээлэл
    client_ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown")
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()

    user_agent = request.headers.get("user-agent", "")[:250]

    # Шинэ session_token
    token = secrets.token_hex(24)
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now_utc + timedelta(hours=2)

    sess = models.UserSession(
        session_token=token,
        code_type=code_type,
        code_value=code_display,
        client_label=req.client_label or None,
        ip_address=client_ip,
        user_agent=user_agent,
        status="active",
        created_at=now_utc,
        last_active_at=now_utc,
        expires_at=expires_at,
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)

    return schemas.LoginResponse(
        token=sess.session_token,
        session_id=sess.id,
        status=sess.status,
        code_type=sess.code_type,
        is_master=(sess.code_type == "master"),
        expires_at=sess.expires_at,
    )


def require_master_session(
    token: Optional[str] = Depends(_extract_token),
    db: Session = Depends(get_db),
) -> models.UserSession:
    """Зөвхөн мастер түлхүүрээр нэвтэрсэн идэвхтэй сессийг шалгана."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Мастер нэвтрэх токен шаардлагатай.",
        )
    sess = db.query(models.UserSession).filter(models.UserSession.session_token == token).first()
    if not sess or sess.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сесс хүчингүй эсвэл хаагдсан байна.",
        )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if sess.expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессийн хугацаа дууссан байна.",
        )
    if sess.code_type != "master":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Энэ үйлдэл болон /generator хуудсанд хандахад Мастер нэвтрэх эрх шаардлагатай.",
        )
    return sess


@router.get("/verify", response_model=schemas.SessionVerifyResponse)
def verify_session(
    token: Optional[str] = Depends(_extract_token),
    db: Session = Depends(get_db),
):
    if not token:
        return schemas.SessionVerifyResponse(valid=False, is_master=False, reason="no_token")

    sess = db.query(models.UserSession).filter(models.UserSession.session_token == token).first()
    if not sess:
        return schemas.SessionVerifyResponse(valid=False, is_master=False, reason="not_found")

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if sess.status == "terminated":
        return schemas.SessionVerifyResponse(valid=False, is_master=False, reason="terminated")

    if sess.expires_at < now:
        if sess.status != "expired":
            sess.status = "expired"
            db.commit()
        return schemas.SessionVerifyResponse(valid=False, is_master=False, reason="expired")

    # Сесс хүчинтэй тул last_active_at шинэчлэх
    sess.last_active_at = now
    db.commit()

    rem_sec = max(0, int((sess.expires_at - now).total_seconds()))
    sess_out = schemas.SessionOut.model_validate(sess)
    sess_out.remaining_seconds = rem_sec

    is_master = (sess.code_type == "master")
    return schemas.SessionVerifyResponse(valid=True, is_master=is_master, session=sess_out)


@router.get("/sessions", response_model=List[schemas.SessionOut])
def list_sessions(
    limit: int = 50,
    admin: models.UserSession = Depends(require_master_session),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    sessions = (
        db.query(models.UserSession)
        .order_by(models.UserSession.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    has_expired_updates = False
    for s in sessions:
        rem_sec = max(0, int((s.expires_at - now).total_seconds()))
        if s.status == "active" and s.expires_at <= now:
            s.status = "expired"
            has_expired_updates = True

        out = schemas.SessionOut.model_validate(s)
        out.remaining_seconds = rem_sec if s.status == "active" else 0
        result.append(out)

    if has_expired_updates:
        db.commit()

    return result


@router.post("/sessions/{session_id}/terminate")
def terminate_session(
    session_id: int,
    admin: models.UserSession = Depends(require_master_session),
    db: Session = Depends(get_db),
):
    sess = db.query(models.UserSession).filter(models.UserSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Сесс олдсонгүй.")

    sess.status = "terminated"
    db.commit()
    return {"success": True, "message": "Сесс цуцлагдлаа (Terminate). Хэрэглэгч системээс гарна."}


@router.post("/sessions/{session_id}/extend")
def extend_session(
    session_id: int,
    body: schemas.SessionExtendRequest,
    admin: models.UserSession = Depends(require_master_session),
    db: Session = Depends(get_db),
):
    sess = db.query(models.UserSession).filter(models.UserSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Сесс олдсонгүй.")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    base_time = max(now, sess.expires_at)
    sess.expires_at = base_time + timedelta(minutes=body.minutes)
    sess.status = "active"
    db.commit()
    db.refresh(sess)

    rem_sec = max(0, int((sess.expires_at - now).total_seconds()))
    return {
        "success": True,
        "message": f"Сессийн хугацааг {body.minutes} минутаар сунгалаа.",
        "expires_at": sess.expires_at,
        "remaining_seconds": rem_sec,
    }


@router.patch("/sessions/{session_id}/label")
def update_session_label(
    session_id: int,
    body: schemas.SessionLabelUpdate,
    admin: models.UserSession = Depends(require_master_session),
    db: Session = Depends(get_db),
):
    sess = db.query(models.UserSession).filter(models.UserSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Сесс олдсонгүй.")

    sess.client_label = body.client_label.strip() or None
    db.commit()
    return {"success": True, "client_label": sess.client_label}


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    admin: models.UserSession = Depends(require_master_session),
    db: Session = Depends(get_db),
):
    sess = db.query(models.UserSession).filter(models.UserSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Сесс олдсонгүй.")

    db.delete(sess)
    db.commit()
    return {"success": True, "message": "Сесс бүртгэлээс устгагдлаа."}

