"""Засгийн газруудын төсөв, эдийн засаг, засаглалын динамик шинжилгээний endpoint-ууд."""
import math
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

import models
from database import get_db
from scripts.ingest_cabinet_budgets import CABINET_DATA

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/cabinet-budgets")
def get_cabinet_budgets(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Үе үеийн Засгийн газруудын төсвийн динамик, өсөлт, засаглалын хугацаа болон холбогдох баримтууд."""
    # Субъект бүрийн баримтуудын тоо болон сайд/гишүүдийн тоог DB-ээс нэгтгэн авна
    cabinet_ids = [c["id"] for c in CABINET_DATA]

    # Сайд/гишүүдийн тоо (relationships target_entity_id == cabinet.id)
    rel_counts = dict(
        db.query(models.Relationship.target_entity_id, func.count(models.Relationship.id))
        .filter(models.Relationship.target_entity_id.in_(cabinet_ids))
        .group_by(models.Relationship.target_entity_id)
        .all()
    )

    # Факт-уудын тоо
    fact_counts = dict(
        db.query(models.Fact.entity_id, func.count(models.Fact.id))
        .filter(models.Fact.entity_id.in_(cabinet_ids))
        .group_by(models.Fact.entity_id)
        .all()
    )

    # DB дээрх тайлбар
    entities = {
        e.id: e
        for e in db.query(models.Entity).filter(models.Entity.id.in_(cabinet_ids)).all()
    }

    # Төсвийн баримтуудыг нарийвчлан авах
    budget_facts_rows = (
        db.query(models.Fact)
        .filter(
            models.Fact.entity_id.in_(cabinet_ids),
            models.Fact.fact_type == "chronological"
        )
        .order_by(models.Fact.fact_date.asc())
        .all()
    )
    facts_by_entity = {}
    for f in budget_facts_rows:
        facts_by_entity.setdefault(f.entity_id, []).append({
            "id": f.id,
            "fact_id": f.fact_id,
            "fact_date": str(f.fact_date) if f.fact_date else None,
            "fact_text": f.fact_text,
            "topic": f.topic,
            "tags": f.tags,
            "source_quote": f.source_quote
        })

    items = []
    # Шилжилтийн үеэс хойших засгийн газруудыг голлон 1990-2024 дэс дарааллаар эрэмбэлнэ
    # (Содном 1984 нь БНМАУ-ын үе тул төгсгөлд эсвэл эхэнд нь үзүүлж болно)
    ordered_cabinets = sorted(CABINET_DATA, key=lambda x: x.get("start", "1990-01-01"))

    for c in ordered_cabinets:
        cid = c["id"]
        entity = entities.get(cid)
        entity_name = entity.name if entity else c["name"]
        
        budgets_raw = c.get("budgets", [])
        annual_budgets = []
        for b_date, b_amount, b_desc in budgets_raw:
            year = int(b_date.split("-")[0])
            billion = float(b_amount)
            trillion = round(billion / 1000.0, 4)
            if billion >= 1000.0:
                disp_str = f"{round(billion / 1000.0, 2)} их наяд ₮"
            else:
                disp_str = f"{round(billion, 1)} тэрбум ₮"

            annual_budgets.append({
                "date": b_date,
                "year": year,
                "amount_billion": round(billion, 1),
                "amount_trillion": round(trillion, 3),
                "display": disp_str,
                "description": b_desc
            })

        init_trill = annual_budgets[0]["amount_trillion"] if annual_budgets else 0.0
        final_trill = annual_budgets[-1]["amount_trillion"] if annual_budgets else 0.0
        init_disp = annual_budgets[0]["display"] if annual_budgets else "-"
        final_disp = annual_budgets[-1]["display"] if annual_budgets else "-"

        growth_pct = 0.0
        if init_trill > 0:
            growth_pct = round(((final_trill - init_trill) / init_trill) * 100.0, 1)

        # Тухайн Засгийн газрын үед холбогдох дуулиант хэргүүд
        cabinet_cases = (
            db.query(models.Case)
            .filter(models.Case.cabinet_id == cid)
            .all()
        )
        total_scandal_billion = sum(c_item.amount_billion or 0.0 for c_item in cabinet_cases)
        total_scandal_trillion = round(total_scandal_billion / 1000.0, 3)

        # Төсвийн хулгай / дарамтын хувь (тухайн үеийн дундаж жилийн төсөвт эзлэх хувь)
        avg_annual_trill = (
            sum(ab["amount_trillion"] for ab in annual_budgets) / len(annual_budgets)
            if annual_budgets else final_trill
        )
        scandal_to_budget_pct = 0.0
        if avg_annual_trill > 0:
            scandal_to_budget_pct = round((total_scandal_trillion / avg_annual_trill) * 100.0, 1)

        items.append({
            "id": cid,
            "name": entity_name,
            "short_name": c["name"].replace(" Засгийн газар", "").replace(" танхим", ""),
            "pm": c.get("pm"),
            "party": c.get("party"),
            "start_date": c.get("start"),
            "end_date": c.get("end"),
            "duration_months": c.get("duration_months"),
            "initial_budget_trillion": init_trill,
            "final_budget_trillion": final_trill,
            "initial_budget_display": init_disp,
            "final_budget_display": final_disp,
            "growth_pct": growth_pct,
            "annual_budgets": annual_budgets,
            "description": entity.description if entity else c.get("description"),
            "tldr": entity.tldr_summary if entity else c.get("tldr"),
            "ministers_count": rel_counts.get(cid, 0),
            "facts_count": fact_counts.get(cid, 0),
            "all_facts": facts_by_entity.get(cid, []),
            "scandals_count": len(cabinet_cases),
            "total_scandal_billion": round(total_scandal_billion, 1),
            "total_scandal_trillion": total_scandal_trillion,
            "scandal_to_budget_pct": scandal_to_budget_pct,
            "cases": [
                {
                    "id": cs.id,
                    "slug": cs.slug,
                    "title": cs.title,
                    "amount_billion": cs.amount_billion,
                    "year": cs.case_year
                }
                for cs in cabinet_cases
            ]
        })

    # Нийт ерөнхий статистик
    modern_items = [it for it in items if it["id"] != 33]  # 1990-2024
    first_b = modern_items[0]["initial_budget_trillion"] if modern_items else 0.0045
    last_b = modern_items[-1]["final_budget_trillion"] if modern_items else 27.36
    total_mult = round(last_b / first_b, 0) if first_b > 0 else 0

    return {
        "cabinets": items,
        "summary": {
            "total_cabinets": len(items),
            "period": "1990 – 2024 он",
            "start_budget": f"{round(first_b * 1000, 1)} тэрбум ₮ (1990)",
            "current_budget": f"{last_b} их наяд ₮ (2024)",
            "growth_multiplier": f"{int(total_mult):,} дахин",
            "max_budget_cabinet": max(items, key=lambda x: x["final_budget_trillion"])["name"],
            "max_budget_trillion": max(items, key=lambda x: x["final_budget_trillion"])["final_budget_trillion"]
        }
    }


# ── Түүхэн тоон цуваа (Macro Time-Series) Endpoint-ууд ───────────────────────

HISTORICAL_MILESTONES = {
    1990: "Ардчилсан хувьсгал, чөлөөт зах зээлийн шилжилт эхэлсэн",
    1991: "Засгийн газрын 20-р тогтоол: Үнэ чөлөөлөлт & банкны хоёр шатлал",
    1993: "Төгрөгийн нэгдсэн хөвөгч ханшийн дэглэмд шилжсэн (1 USD = 395 ₮)",
    1997: "Гаалийн тариф тэглэх бодлого, Азийн санхүүгийн хямрал",
    2000: "Дараалсан зуд турхан, МАХН УИХ-д 72 суудал авсан",
    2008: "Дэлхийн санхүүгийн хямрал, зэсийн үнийн огцом уналт",
    2012: "Чингис бонд 1.5 тэрбум USD, Хөгжлийн банкны санхүүжилт",
    2015: "Монгол Улсын 3 сая дахь иргэн мэндэлсэн (хүн ам 3 саяд хүрсэн)",
    2017: "ОУВС-гийн Өргөтгөсөн санхүүжилтийн хөтөлбөр (EFF) баталсан",
    2020: "Ковид-19 цар тахал, хил хаагдаж төсвийн зарлага огцом тэлсэн",
    2024: "126 гишүүнтэй УИХ, анхны Хамтарсан Засгийн газар байгуулагдсан"
}

YEAR_CABINET_MAP = {
    1990: "Д.Бямбасүрэн", 1991: "Д.Бямбасүрэн", 1992: "П.Жасрай", 1993: "П.Жасрай",
    1994: "П.Жасрай", 1995: "П.Жасрай", 1996: "М.Энхсайхан", 1997: "М.Энхсайхан",
    1998: "Ц.Элбэгдорж / Ж.Наранцацралт", 1999: "Р.Амаржаргал", 2000: "Н.Энхбаяр",
    2001: "Н.Энхбаяр", 2002: "Н.Энхбаяр", 2003: "Н.Энхбаяр", 2004: "Ц.Элбэгдорж",
    2005: "Ц.Элбэгдорж", 2006: "М.Энхболд", 2007: "С.Баяр", 2008: "С.Баяр",
    2009: "С.Батболд", 2010: "С.Батболд", 2011: "С.Батболд", 2012: "Н.Алтанхуяг",
    2013: "Н.Алтанхуяг", 2014: "Ч.Сайханбилэг", 2015: "Ч.Сайханбилэг", 2016: "Ж.Эрдэнэбат",
    2017: "У.Хүрэлсүх", 2018: "У.Хүрэлсүх", 2019: "У.Хүрэлсүх", 2020: "У.Хүрэлсүх",
    2021: "Л.Оюун-Эрдэнэ", 2022: "Л.Оюун-Эрдэнэ", 2023: "Л.Оюун-Эрдэнэ", 2024: "Л.Оюун-Эрдэнэ",
    2025: "Л.Оюун-Эрдэнэ", 2026: "Л.Оюун-Эрдэнэ"
}


@router.get("/macro-indicators")
def get_macro_indicators(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Бүх макро тоон үзүүлэлтийн тодорхойлолт, хамрах хугацаа ба сүүлийн утга."""
    indicators = db.query(models.MacroIndicator).order_by(models.MacroIndicator.id.asc()).all()
    results = []
    for ind in indicators:
        dps = ind.datapoints
        latest_dp = max(dps, key=lambda p: p.year) if dps else None
        earliest_dp = min(dps, key=lambda p: p.year) if dps else None
        results.append({
            "id": ind.id,
            "code": ind.code,
            "name": ind.name,
            "category": ind.category,
            "unit": ind.unit,
            "default_axis": ind.default_axis,
            "color": ind.color,
            "description": ind.description,
            "entity_id": ind.entity_id,
            "source_id": ind.source_id,
            "datapoints_count": len(dps),
            "min_year": earliest_dp.year if earliest_dp else None,
            "max_year": latest_dp.year if latest_dp else None,
            "earliest_value": earliest_dp.value if earliest_dp else None,
            "latest_value": latest_dp.value if latest_dp else None,
            "latest_year": latest_dp.year if latest_dp else None
        })
    return results


@router.get("/macro-series")
def get_macro_series(
    indicators: str = "budget_expenditure,usd_rate,cny_rate,population",
    start_year: int = 1990,
    end_year: int = 2026,
    normalize: bool = False,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Сонгосон макро үзүүлэлтүүдийн он оноор нэгтгэсэн, зэрэгцүүлсэн цаг хугацааны цуваа."""
    codes = [c.strip() for c in indicators.split(",") if c.strip()]
    if not codes:
        codes = ["budget_expenditure", "usd_rate"]

    inds = db.query(models.MacroIndicator).filter(models.MacroIndicator.code.in_(codes)).all()
    inds_by_code = {ind.code: ind for ind in inds}

    # Тухайн завсар дахь бүх тоон цэгүүдийг татах
    ind_ids = [ind.id for ind in inds]
    datapoints = (
        db.query(models.MacroDataPoint)
        .filter(
            models.MacroDataPoint.indicator_id.in_(ind_ids),
            models.MacroDataPoint.year >= start_year,
            models.MacroDataPoint.year <= end_year
        )
        .order_by(models.MacroDataPoint.year.asc())
        .all()
    )

    # Эх сурвалжуудын cache
    source_ids = {dp.source_id for dp in datapoints if dp.source_id}
    sources_map = {}
    if source_ids:
        for s in db.query(models.Source).filter(models.Source.id.in_(source_ids)).all():
            sources_map[s.id] = {
                "id": s.id,
                "title": s.title,
                "url": s.url,
                "category": s.category,
                "author": s.author
            }

    # Он тус бүрийн бүтцийг үүсгэх
    timeline_dict: Dict[int, Dict[str, Any]] = {}
    all_years = sorted(list(range(start_year, end_year + 1)))
    for yr in all_years:
        timeline_dict[yr] = {
            "year": yr,
            "cabinet": YEAR_CABINET_MAP.get(yr, ""),
            "milestone": HISTORICAL_MILESTONES.get(yr, None),
            "values": {},
            "notes": {},
            "sources": {},
            "yoy_growth": {},
            "indexed_values": {}
        }

    # Үзүүлэлт тус бүрийн өмнөх оны утга (YoY өсөлт тооцоолоход)
    prev_values: Dict[str, float] = {}
    base_values: Dict[str, float] = {}

    # Завсраас өмнөх хамгийн сүүлийн цэгийг авах (start_year-ийн YoY-г зөв тооцохын тулд)
    pre_datapoints = (
        db.query(models.MacroDataPoint)
        .filter(
            models.MacroDataPoint.indicator_id.in_(ind_ids),
            models.MacroDataPoint.year == start_year - 1
        )
        .all()
    )
    for pdp in pre_datapoints:
        c = next((k for k, v in inds_by_code.items() if v.id == pdp.indicator_id), None)
        if c:
            prev_values[c] = pdp.value

    # Цэгүүдийг он тус бүрт хуваарилах
    # Эхлээд үзүүлэлт тус бүрээр эрэмбэлж боловсруулах
    dps_by_ind: Dict[int, List[models.MacroDataPoint]] = {}
    for dp in datapoints:
        dps_by_ind.setdefault(dp.indicator_id, []).append(dp)

    for code in codes:
        ind = inds_by_code.get(code)
        if not ind:
            continue
        pts = dps_by_ind.get(ind.id, [])
        pts_sorted = sorted(pts, key=lambda p: p.year)
        
        # Base value (анхны утга) суурь индексэд зориулж
        if pts_sorted:
            base_values[code] = pts_sorted[0].value

        current_prev = prev_values.get(code)
        for dp in pts_sorted:
            yr = dp.year
            if yr not in timeline_dict:
                continue

            val = dp.value
            timeline_dict[yr]["values"][code] = val
            timeline_dict[yr]["notes"][code] = dp.note
            if dp.source_id and dp.source_id in sources_map:
                timeline_dict[yr]["sources"][code] = sources_map[dp.source_id]

            # YoY өсөлт тооцоолох
            if current_prev is not None and current_prev > 0:
                yoy = round(((val - current_prev) / current_prev) * 100.0, 1)
                timeline_dict[yr]["yoy_growth"][code] = yoy
            else:
                timeline_dict[yr]["yoy_growth"][code] = None
            current_prev = val

            # Суурь индекс (эхний цэг = 100)
            bval = base_values.get(code)
            if bval and bval > 0:
                timeline_dict[yr]["indexed_values"][code] = round((val / bval) * 100.0, 2)

    # Timeline жагсаалт
    timeline = [timeline_dict[y] for y in all_years if timeline_dict[y]["values"]]

    # Хураангуй үзүүлэлтүүд (Summary Metrics)
    summary_metrics = {}
    for code, ind in inds_by_code.items():
        vals = [timeline_dict[y]["values"][code] for y in all_years if code in timeline_dict[y]["values"]]
        if vals:
            start_v = vals[0]
            end_v = vals[-1]
            mult = round(end_v / start_v, 1) if start_v > 0 else None
            summary_metrics[code] = {
                "name": ind.name,
                "unit": ind.unit,
                "color": ind.color,
                "start_val": start_v,
                "end_val": end_v,
                "min_val": min(vals),
                "max_val": max(vals),
                "growth_multiplier": mult,
                "total_pct_change": round(((end_v - start_v) / start_v) * 100.0, 1) if start_v > 0 else None
            }

    milestones_in_range = [
        {"year": yr, "event": desc}
        for yr, desc in sorted(HISTORICAL_MILESTONES.items())
        if start_year <= yr <= end_year
    ]

    return {
        "period": f"{start_year} – {end_year} он",
        "requested_indicators": [
            {
                "id": ind.id,
                "code": ind.code,
                "name": ind.name,
                "category": ind.category,
                "unit": ind.unit,
                "default_axis": ind.default_axis,
                "color": ind.color,
                "description": ind.description
            }
            for code, ind in inds_by_code.items()
        ],
        "timeline": timeline,
        "milestones": milestones_in_range,
        "summary": summary_metrics
    }


# ── Макро шинжилгээний цогц аргууд (Macro Analytics Lab) ─────────────────────

def _calculate_pearson(x_vals: List[float], y_vals: List[float]) -> Optional[float]:
    n = len(x_vals)
    if n < 3:
        return None
    mx = sum(x_vals) / n
    my = sum(y_vals) / n
    num = sum((x - mx) * (y - my) for x, y in zip(x_vals, y_vals))
    den_x = sum((x - mx) ** 2 for x in x_vals)
    den_y = sum((y - my) ** 2 for y in y_vals)
    if den_x <= 0 or den_y <= 0:
        return 0.0
    val = num / math.sqrt(den_x * den_y)
    return round(float(val), 3)


def _interpret_r(r: float, name1: str, name2: str) -> str:
    if r >= 0.9:
        return f"{name1} ба {name2} нь бараг төгс шууд хамааралтай (+{r}). Нэг нь тэлэхэд нөгөө нь зэрэг өсдөг."
    elif r >= 0.7:
        return f"{name1} ба {name2} нь өндөр шууд хамааралтай (+{r}). Өсөлтийн чиглэл ерөнхийдөө нэг байна."
    elif r >= 0.4:
        return f"{name1} ба {name2} нь дунд зэргийн эерэг хамааралтай (+{r})."
    elif r > -0.4:
        return f"{name1} ба {name2} хооронд шууд хамаарал бага байна ({r:+.2f})."
    elif r > -0.7:
        return f"{name1} ба {name2} нь дунд зэргийн урвуу хамааралтай ({r:+.2f})."
    else:
        return f"{name1} ба {name2} нь хүчтэй урвуу хамааралтай ({r:+.2f}). Нэг нь өсөхөд нөгөө нь буурах хандлагатай."


@router.get("/macro-analytics")
def get_macro_analytics(
    start_year: int = 1990,
    end_year: int = 2026,
    indicators: str = "",
    base_year: int = 2000,
    amount_mnt: float = 1_000_000.0,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Макро өгөгдлүүд дээр суурилсан Корреляци, CAGR/Савалгаа, Худалдан авах чадвар ба Засгийн газрын онооны хуудас."""
    all_inds = db.query(models.MacroIndicator).order_by(models.MacroIndicator.id.asc()).all()
    inds_map = {ind.code: ind for ind in all_inds}

    if indicators:
        req_codes = [c.strip() for c in indicators.split(",") if c.strip() in inds_map]
    else:
        req_codes = [ind.code for ind in all_inds]

    ind_ids = [inds_map[c].id for c in req_codes]
    dps = (
        db.query(models.MacroDataPoint)
        .filter(models.MacroDataPoint.indicator_id.in_(ind_ids))
        .all()
    )

    id_to_code = {ind.id: ind.code for ind in all_inds}
    series_data: Dict[str, Dict[int, float]] = {c: {} for c in req_codes}
    for dp in dps:
        code = id_to_code.get(dp.indicator_id)
        if code and dp.value is not None:
            series_data[code][dp.year] = dp.value

    # 1. Pearson Correlation Matrix
    corr_indicators = []
    for code in req_codes:
        ind = inds_map[code]
        corr_indicators.append({
            "code": code,
            "name": ind.name,
            "category": ind.category,
            "unit": ind.unit,
            "color": ind.color
        })

    matrix = []
    pairs = []
    for i, c1 in enumerate(req_codes):
        row = []
        d1 = series_data[c1]
        for j, c2 in enumerate(req_codes):
            if i == j:
                row.append(1.0)
                continue
            d2 = series_data[c2]
            common_yrs = sorted(
                y for y in set(d1.keys()) & set(d2.keys())
                if start_year <= y <= end_year
            )
            if len(common_yrs) >= 3:
                x = [d1[y] for y in common_yrs]
                y = [d2[y] for y in common_yrs]
                r_val = _calculate_pearson(x, y)
                row.append(r_val)
                if i < j and r_val is not None:
                    pairs.append({
                        "ind1": c1,
                        "ind2": c2,
                        "name1": inds_map[c1].name,
                        "name2": inds_map[c2].name,
                        "color1": inds_map[c1].color,
                        "color2": inds_map[c2].color,
                        "r": r_val,
                        "n": len(common_yrs),
                        "description": _interpret_r(r_val, inds_map[c1].name, inds_map[c2].name)
                    })
            else:
                row.append(None)
        matrix.append(row)

    pairs.sort(key=lambda p: abs(p["r"]), reverse=True)

    # 2. CAGR & Volatility / Risk Profile
    cagr_list = []
    inflation_data = series_data.get("cpi_inflation", {})
    inf_in_range = [inflation_data[y] for y in sorted(inflation_data.keys()) if start_year <= y <= end_year]
    avg_inf = round(sum(inf_in_range) / len(inf_in_range), 1) if inf_in_range else 8.5

    for code in req_codes:
        ind = inds_map[code]
        d = series_data[code]
        valid_years = sorted(y for y in d.keys() if start_year <= y <= end_year)
        if len(valid_years) >= 2:
            y0, y1 = valid_years[0], valid_years[-1]
            v0, v1 = d[y0], d[y1]
            n_years = y1 - y0
            if n_years > 0 and v0 > 0 and v1 > 0:
                cagr_pct = round(((v1 / v0) ** (1.0 / n_years) - 1.0) * 100.0, 2)
            else:
                cagr_pct = None

            yoy_changes = []
            for k in range(1, len(valid_years)):
                prev_y = valid_years[k - 1]
                curr_y = valid_years[k]
                if curr_y == prev_y + 1 and d[prev_y] > 0:
                    chg = ((d[curr_y] - d[prev_y]) / d[prev_y]) * 100.0
                    yoy_changes.append(chg)

            if len(yoy_changes) >= 2:
                mean_chg = sum(yoy_changes) / len(yoy_changes)
                var = sum((g - mean_chg) ** 2 for g in yoy_changes) / (len(yoy_changes) - 1)
                volatility = round(math.sqrt(var), 1)
            else:
                volatility = 0.0

            mult = round(v1 / v0, 2) if v0 > 0 else None
            tot_pct = round(((v1 - v0) / v0) * 100.0, 1) if v0 > 0 else None
            beats = (cagr_pct > avg_inf) if cagr_pct is not None and code != "cpi_inflation" else False

            cagr_list.append({
                "code": code,
                "name": ind.name,
                "category": ind.category,
                "unit": ind.unit,
                "color": ind.color,
                "start_year": y0,
                "start_val": v0,
                "end_year": y1,
                "end_val": v1,
                "years_count": n_years,
                "total_multiplier": mult,
                "total_pct_change": tot_pct,
                "cagr_pct": cagr_pct,
                "volatility_pct": volatility,
                "beats_inflation": beats
            })

    cagr_list.sort(key=lambda x: x["cagr_pct"] if x["cagr_pct"] is not None else -999, reverse=True)
    for rank, item in enumerate(cagr_list, 1):
        item["rank"] = rank

    # 3. Purchasing Power Parity (PPP)
    target_year = min(end_year, 2025)
    by = base_year if base_year in series_data.get("usd_rate", {}) else 2000

    def get_val_at(c: str, yr: int) -> Optional[float]:
        pts_c = series_data.get(c, {})
        if yr in pts_c:
            return pts_c[yr]
        available = sorted(pts_c.keys())
        if not available:
            return None
        nearest = min(available, key=lambda y: abs(y - yr))
        if abs(nearest - yr) <= 3:
            return pts_c[nearest]
        return None

    meat_b = get_val_at("meat_price_kg", by)
    meat_c = get_val_at("meat_price_kg", target_year)
    house_b = get_val_at("housing_price_sqm", by)
    house_c = get_val_at("housing_price_sqm", target_year)
    gold_b = get_val_at("gold_price_mnt_gram", by)
    gold_c = get_val_at("gold_price_mnt_gram", target_year)
    usd_b = get_val_at("usd_rate", by)
    usd_c = get_val_at("usd_rate", target_year)

    btc_usd_b = get_val_at("bitcoin_usd", by)
    btc_usd_c = get_val_at("bitcoin_usd", target_year)
    btc_mnt_b = (btc_usd_b * usd_b) if btc_usd_b and usd_b else None
    btc_mnt_c = (btc_usd_c * usd_c) if btc_usd_c and usd_c else None

    base_purchases = {
        "meat_kg": round(amount_mnt / meat_b, 1) if meat_b else None,
        "housing_sqm": round(amount_mnt / house_b, 2) if house_b else None,
        "gold_gram": round(amount_mnt / gold_b, 2) if gold_b else None,
        "usd": round(amount_mnt / usd_b, 1) if usd_b else None,
        "btc": round(amount_mnt / btc_mnt_b, 4) if btc_mnt_b else None,
    }

    current_purchases = {
        "meat_kg": round(amount_mnt / meat_c, 1) if meat_c else None,
        "housing_sqm": round(amount_mnt / house_c, 2) if house_c else None,
        "gold_gram": round(amount_mnt / gold_c, 2) if gold_c else None,
        "usd": round(amount_mnt / usd_c, 1) if usd_c else None,
        "btc": round(amount_mnt / btc_mnt_c, 6) if btc_mnt_c else None,
    }

    retention_pct = {}
    for k in ["meat_kg", "housing_sqm", "gold_gram", "usd"]:
        bv = base_purchases.get(k)
        cv = current_purchases.get(k)
        if bv and cv and bv > 0:
            retention_pct[k] = round((cv / bv) * 100.0, 1)
        else:
            retention_pct[k] = None

    benchmark_years = [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025]
    benchmarks = []
    for y in benchmark_years:
        m_val = get_val_at("meat_price_kg", y)
        h_val = get_val_at("housing_price_sqm", y)
        g_val = get_val_at("gold_price_mnt_gram", y)
        u_val = get_val_at("usd_rate", y)
        benchmarks.append({
            "year": y,
            "meat_kg": round(1_000_000.0 / m_val, 1) if m_val else None,
            "housing_sqm": round(1_000_000.0 / h_val, 2) if h_val else None,
            "gold_gram": round(1_000_000.0 / g_val, 2) if g_val else None,
            "usd": round(1_000_000.0 / u_val, 1) if u_val else None,
        })

    # 4. Cabinet Macro Scorecard
    cabinet_scorecard = []
    for c in sorted(CABINET_DATA, key=lambda x: x.get("start", "1990-01-01")):
        if c.get("id") == 33:
            continue
        st_yr = int(c["start"].split("-")[0])
        en_yr = int(c["end"].split("-")[0]) if c.get("end") else 2026
        en_yr = max(st_yr, en_yr)

        def get_diff_pct(code: str) -> Optional[float]:
            v0 = get_val_at(code, st_yr)
            v1 = get_val_at(code, en_yr)
            if v0 and v1 and v0 > 0:
                return round(((v1 - v0) / v0) * 100.0, 1)
            return None

        inf_vals = [inflation_data[yr] for yr in range(st_yr, en_yr + 1) if yr in inflation_data]
        cab_avg_inf = round(sum(inf_vals) / len(inf_vals), 1) if inf_vals else None

        # Тухайн Засгийн газрын үеийн хэргүүдийн нийт дүн ба Төсөвт эзлэх хувь
        cab_cases = db.query(models.Case).filter(models.Case.cabinet_id == c["id"]).all()
        scandal_bill = sum(cs.amount_billion or 0.0 for cs in cab_cases)
        scandal_trill = round(scandal_bill / 1000.0, 3)

        # Төсвийн хулгайн харьцаа
        b_vals = [series_data.get("budget_expenditure", {}).get(yr) for yr in range(st_yr, en_yr + 1) if yr in series_data.get("budget_expenditure", {})]
        avg_b_trill = (sum(b_vals) / len(b_vals)) if b_vals else get_val_at("budget_expenditure", en_yr)
        scandal_ratio_pct = 0.0
        if avg_b_trill and avg_b_trill > 0:
            scandal_ratio_pct = round((scandal_trill / avg_b_trill) * 100.0, 1)

        cabinet_scorecard.append({
            "id": c["id"],
            "name": c["name"],
            "short_name": c["name"].replace(" Засгийн газар", "").replace(" танхим", ""),
            "pm": c.get("pm"),
            "party": c.get("party"),
            "start": c.get("start"),
            "end": c.get("end"),
            "start_year": st_yr,
            "end_year": en_yr,
            "duration_months": c.get("duration_months"),
            "budget_growth_pct": get_diff_pct("budget_expenditure"),
            "usd_growth_pct": get_diff_pct("usd_rate"),
            "meat_growth_pct": get_diff_pct("meat_price_kg"),
            "housing_growth_pct": get_diff_pct("housing_price_sqm"),
            "gold_growth_pct": get_diff_pct("gold_price_mnt_gram"),
            "avg_inflation_pct": cab_avg_inf,
            "scandals_count": len(cab_cases),
            "total_scandal_billion": round(scandal_bill, 1),
            "total_scandal_trillion": scandal_trill,
            "scandal_to_budget_pct": scandal_ratio_pct,
            "top_scandals": [
                {"title": cs.title, "amount_billion": cs.amount_billion, "slug": cs.slug}
                for cs in sorted(cab_cases, key=lambda x: x.amount_billion or 0.0, reverse=True)[:3]
            ]
        })

    return {
        "period": f"{start_year} – {end_year} он",
        "correlation": {
            "indicators": corr_indicators,
            "matrix": matrix,
            "pairs": pairs[:25]
        },
        "cagr_risk": {
            "average_inflation_cagr": avg_inf,
            "ranking": cagr_list
        },
        "purchasing_power": {
            "base_year": by,
            "target_year": target_year,
            "amount_mnt": amount_mnt,
            "base_purchases": base_purchases,
            "current_purchases": current_purchases,
            "retention_pct": retention_pct,
            "benchmarks": benchmarks
        },
        "cabinet_scorecard": cabinet_scorecard
    }


# ── Media Intelligence & 'Хаалтын гэрээ' илрүүлэлт ─────────────────────────

@router.get("/media-intelligence")
def get_media_intelligence(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Хэвлэл мэдээллийн эх сурвалжуудын хандлага (bias/sentiment), 
    мэдээллийн дүлий бүс (Blackout / Silence) ба хаалтын гэрээний магадлалын шинжилгээ.
    """
    from urllib.parse import urlparse

    sources = db.query(models.Source).all()
    facts = (
        db.query(models.Fact)
        .options(joinedload(models.Fact.source), joinedload(models.Fact.entity))
        .filter(models.Fact.source_id.isnot(None))
        .all()
    )
    cases = db.query(models.Case).options(joinedload(models.Case.links)).all()
    entities = {e.id: e for e in db.query(models.Entity).all()}

    # 1. Эх сурвалжуудын домэйноор бүлэглэх
    domain_data = {}
    for s in sources:
        domain = "бусад / тэмдэглэл"
        if s.url:
            parsed = urlparse(s.url)
            domain = parsed.netloc.replace("www.", "") or "бусад"
        elif s.category in ["document", "note"]:
            domain = f"албан_{s.category}"

        if domain not in domain_data:
            domain_data[domain] = {
                "domain": domain,
                "sources_count": 0,
                "categories": set(),
                "facts_count": 0,
                "entity_sentiments": {}, # entity_id -> [scores]
                "entity_mentions": {},   # entity_id -> count
                "case_mentions": set(),   # case_id-ууд
            }
        domain_data[domain]["sources_count"] += 1
        domain_data[domain]["categories"].add(s.category)

    # 2. Факт ба субъектүүдийн мэдрэмжийн тооцоолол
    for f in facts:
        if not f.source:
            continue
        domain = "бусад / тэмдэглэл"
        if f.source.url:
            domain = urlparse(f.source.url).netloc.replace("www.", "") or "бусад"
        elif f.source.category in ["document", "note"]:
            domain = f"албан_{f.source.category}"

        if domain in domain_data:
            d = domain_data[domain]
            d["facts_count"] += 1
            eid = f.entity_id
            d["entity_mentions"][eid] = d["entity_mentions"].get(eid, 0) + 1
            if f.sentiment_score is not None:
                d["entity_sentiments"].setdefault(eid, []).append(f.sentiment_score)

    # 3. Мөрдлөгийн хэргүүд дэх дурдалт ба Дүлий бүс (Blackout Tracker)
    # Аль ч сайт хэрэгтэй холбоотой хүний тухай бичсэн бол уг хэргийг дурдсанд тооцно
    case_entity_map = {} # case_id -> set(entity_ids)
    for c in cases:
        case_entity_map[c.id] = {l.entity_id for l in c.links if l.entity_id}

    for domain, d in domain_data.items():
        for cid, e_set in case_entity_map.items():
            if any(eid in d["entity_mentions"] for eid in e_set):
                d["case_mentions"].add(cid)

    # Media Profiles үүсгэх
    media_profiles = []
    for domain, d in domain_data.items():
        if d["facts_count"] == 0 and d["sources_count"] < 2:
            continue

        # Дундаж мэдрэмж
        all_sentiments = [score for scores in d["entity_sentiments"].values() for score in scores]
        avg_sentiment = round(sum(all_sentiments) / len(all_sentiments), 2) if all_sentiments else 0.0

        # Топ дурдагдсан субъектүүд ба тэдгээрийн хандлага
        favored_entities = []
        criticized_entities = []
        for eid, cnt in d["entity_mentions"].items():
            scores = d["entity_sentiments"].get(eid, [])
            ent = entities.get(eid)
            if not ent:
                continue
            e_avg = round(sum(scores) / len(scores), 2) if scores else 0.0
            info = {
                "entity_id": eid,
                "name": ent.name,
                "entity_type": ent.entity_type,
                "mentions": cnt,
                "sentiment_avg": e_avg,
            }
            if e_avg >= 0.2:
                favored_entities.append(info)
            elif e_avg <= -0.2:
                criticized_entities.append(info)

        favored_entities.sort(key=lambda x: (x["sentiment_avg"], x["mentions"]), reverse=True)
        criticized_entities.sort(key=lambda x: (x["sentiment_avg"], -x["mentions"]))

        # Дүлий бүс буюу огт бичээгүй томоохон хэргүүд (Silence / Blackout)
        blackout_cases = []
        for c in cases:
            if c.id not in d["case_mentions"] and c.status == "PUBLISHED":
                blackout_cases.append({
                    "id": c.id,
                    "title": c.title,
                    "slug": c.slug,
                    "category": c.category
                })

        # "Хаалтын гэрээний магадлалын индекс" (0–100%)
        # Хэрэв тухайн эх сурвалж тодорхой улс төрчийг маш их магтаж (sentiment > 0.4), 
        # мөртлөө түүний холбогдсон хэргийг огт бичээгүй (blackout) бол магадлал өндөр байна.
        suspicious_agreements = []
        for fav in favored_entities[:5]:
            # Энэ хүн ямар нэг хэрэгт холбогдсон уу?
            involved_cases = [c for c in cases if any(l.entity_id == fav["entity_id"] for l in c.links)]
            # Гэтэл энэ эх сурвалж тэр хэргийн тухай огт дурдаагүй юу?
            muted_cases = [c.title for c in involved_cases if c.id not in d["case_mentions"]]
            if muted_cases:
                contract_risk = min(95, int(fav["sentiment_avg"] * 50 + len(muted_cases) * 25 + fav["mentions"] * 5))
                suspicious_agreements.append({
                    "entity_name": fav["name"],
                    "entity_id": fav["entity_id"],
                    "favor_score": fav["sentiment_avg"],
                    "muted_cases": muted_cases,
                    "contract_probability_pct": contract_risk,
                })

        media_profiles.append({
            "domain": domain,
            "sources_count": d["sources_count"],
            "facts_count": d["facts_count"],
            "primary_categories": list(d["categories"]),
            "average_sentiment": avg_sentiment,
            "favored_entities": favored_entities[:4],
            "criticized_entities": criticized_entities[:4],
            "blackout_cases_count": len(blackout_cases),
            "blackout_cases": blackout_cases[:6],
            "suspicious_contracts": suspicious_agreements,
        })

    # Эрэмбэлэлт
    media_profiles.sort(key=lambda x: (len(x["suspicious_contracts"]) > 0, x["facts_count"]), reverse=True)

    # Томоохон хэргүүд дээрх хэвлэлүүдийн хамрах хүрээ (Coverage Matrix)
    case_coverage = []
    for c in cases:
        reported_domains = [
            d["domain"] for d in domain_data.values() if c.id in d["case_mentions"]
        ]
        silent_domains = [
            d["domain"] for d in domain_data.values() 
            if c.id not in d["case_mentions"] and not d["domain"].startswith("албан_") and d["facts_count"] >= 3
        ]
        case_coverage.append({
            "case_id": c.id,
            "title": c.title,
            "slug": c.slug,
            "category": c.category,
            "reported_media_count": len(reported_domains),
            "reported_domains": reported_domains,
            "silent_media_count": len(silent_domains),
            "silent_domains": silent_domains[:8],
        })

    case_coverage.sort(key=lambda x: x["reported_media_count"], reverse=True)

    return {
        "total_monitored_domains": len(media_profiles),
        "media_profiles": media_profiles,
        "case_coverage": case_coverage,
    }


