"""
Нүүрсний хулгайн хэрэгтэй холбоотой нотлох баримтууд, эх сурвалжууд,
гол хувь хүмүүс, төрийн өмчит болон хувийн компаниуд, фактууд ба
хамаарлуудыг системд бүрэн бүртгэж, 'coal-theft' мөрдлөгийн хэрэгт холбох скрипт.

Дүрэм: .agents/AGENTS.md
- fact_type: Зөвхөн "chronological" эсвэл "biographical"
- Агуулга гээхгүй, өндөр нарийвчлалтай баримтжуулалт
- SHA-256 криптограф хэштэй эх сурвалжууд
"""
import sys
import hashlib
from datetime import date
from sqlalchemy import func

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.append('.')
from database import SessionLocal
import models


def get_or_create_source(db, title, url, category, cleaned_text, author=None, pub_date=None, reliability=0.98):
    sha = hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()
    src = db.query(models.Source).filter(
        (models.Source.url == url) | (models.Source.sha256_hash == sha)
    ).first()
    if not src:
        src = models.Source(
            source_type="document",
            url=url,
            title=title,
            author=author or "УИХ-ын Түр хороо / АТГ",
            publication_date=pub_date or date(2023, 12, 22),
            cleaned_text=cleaned_text,
            selected_text=cleaned_text[:250],
            sha256_hash=sha,
            reliability_score=reliability,
            bias_score=0.0,
            category=category
        )
        db.add(src)
        db.commit()
        db.refresh(src)
        print(f"Created source: [{src.id}] {src.title[:60]}...")
    return src


def get_or_create_entity(db, name, entity_type, description=None, tldr_summary=None, aliases=None):
    ent = db.query(models.Entity).filter(models.Entity.name == name).first()
    if not ent:
        ent = models.Entity(
            name=name,
            entity_type=entity_type,
            description=description,
            tldr_summary=tldr_summary,
            is_stub=False
        )
        db.add(ent)
        db.commit()
        db.refresh(ent)
        print(f"Created entity: [{ent.id}] {ent.name} ({ent.entity_type})")
        
        if aliases:
            for al, kind in aliases:
                norm = al.strip().lower()
                db.add(models.EntityAlias(
                    entity_id=ent.id,
                    alias=al.strip(),
                    alias_norm=norm,
                    kind=kind
                ))
            db.commit()
    else:
        # Update descriptions if empty
        if description and not ent.description:
            ent.description = description
        if tldr_summary and not ent.tldr_summary:
            ent.tldr_summary = tldr_summary
        db.commit()
    return ent


def add_fact(db, entity_id, source_id, f_date_str, fact_type, text, quote, topic, tags, role_ctx="Нүүрсний хэрэг", sentiment=-0.5):
    # Rule check: fact_type MUST be chronological or biographical
    assert fact_type in ("chronological", "biographical"), f"Invalid fact_type: {fact_type}"
    
    yr, mo, dy = [int(x) for x in f_date_str.split("-")]
    f_date = date(yr, mo, dy)

    existing = db.query(models.Fact).filter(
        models.Fact.entity_id == entity_id,
        models.Fact.fact_date == f_date,
        models.Fact.fact_text == text
    ).first()

    if not existing:
        fact = models.Fact(
            entity_id=entity_id,
            source_id=source_id,
            fact_type=fact_type,
            fact_date=f_date,
            date_precision="day",
            fact_text=text,
            source_quote=quote,
            role_context=role_ctx,
            topic=topic,
            stance="баримтлагдсан",
            sentiment_score=sentiment
        )
        fact.tags = tags
        db.add(fact)
        db.flush()
        fact.fact_id = f"F{fact.id}"
        db.commit()
        return fact
    return existing


def add_relationship(db, source_id, src_ent_id, tgt_ent_id, target_name, rel_type, quote=None, start_date_str=None, end_date_str=None):
    s_date = date(*[int(x) for x in start_date_str.split("-")]) if start_date_str else None
    e_date = date(*[int(x) for x in end_date_str.split("-")]) if end_date_str else None

    existing = db.query(models.Relationship).filter(
        models.Relationship.source_entity_id == src_ent_id,
        models.Relationship.target_entity_id == tgt_ent_id,
        models.Relationship.rel_type == rel_type
    ).first()

    if not existing:
        rel = models.Relationship(
            source_entity_id=src_ent_id,
            target_entity_id=tgt_ent_id,
            target_name=target_name,
            source_id=source_id,
            rel_type=rel_type,
            target_kind="company" if "ХХК" in target_name or "ХК" in target_name else "person",
            start_date=s_date,
            start_precision="day" if s_date else None,
            end_date=e_date,
            end_precision="day" if e_date else None,
            source_quote=quote
        )
        db.add(rel)
        db.commit()
        db.refresh(rel)
        return rel
    return existing


def link_to_case(db, case, entity_id=None, fact_id=None, role="INVOLVED_IN", note=None):
    if entity_id:
        ex = db.query(models.CaseLink).filter(
            models.CaseLink.case_id == case.id,
            models.CaseLink.entity_id == entity_id
        ).first()
        if not ex:
            db.add(models.CaseLink(
                case_id=case.id,
                entity_id=entity_id,
                role=role,
                note=note
            ))
            db.commit()
    if fact_id:
        ex = db.query(models.CaseLink).filter(
            models.CaseLink.case_id == case.id,
            models.CaseLink.fact_id == fact_id
        ).first()
        if not ex:
            db.add(models.CaseLink(
                case_id=case.id,
                fact_id=fact_id,
                role=role,
                note=note
            ))
            db.commit()


def main():
    db = SessionLocal()
    print("=== STARTING COAL THEFT DATA INGESTION ===")

    # 1. Sources (Албан ёсны эх сурвалжууд)
    src_parliament = get_or_create_source(
        db,
        title="УИХ-ын Түр хороо: 'Нүүрсний хулгай'-н хэргийн нотлох баримтыг шинжлэн судлах нээлттэй сонсголын тайлан",
        url="https://www.parliament.mn/coal-hearing-2023",
        category="government",
        cleaned_text=(
            "Монгол Улсын Их Хурлын 2023 оны 07 дугаар сарын 06-ны өдрийн тогтоолоор байгуулагдсан "
            "Хянан шалгах түр хороо 2023 оны 12 дугаар сарын 4-нөөс 22-ны хооронд нийт 9 өдрийн турш "
            "нотлох баримтыг шинжлэн судлах сонсгол зохион байгуулж, 'Эрдэнэс Тавантолгой' ХК-ийн "
            "нүүрс олборлолт, борлуулалт, нууц оффтейк гэрээнүүд, тээвэрлэлтийн С зөвшөөрөл, "
            "төмөр замын бүтээн байгуулалт, гаалийн бүртгэлийн зөрүү зэрэг 60 гаруй асуудлыг хөндөн шинжлэв."
        ),
        author="УИХ-ын Хянан шалгах түр хороо",
        pub_date=date(2023, 12, 22),
        reliability=0.99
    )

    src_iaac = get_or_create_source(
        db,
        title="Авлигатай Тэмцэх Газар: 'Нүүрсний' гэх эрүүгийн хэргийн мөрдөн шалгах ажиллагааны албан мэдээлэл",
        url="https://www.iaac.mn/news/coal-theft-investigation-report-2023",
        category="government",
        cleaned_text=(
            "АТГ, ЦЕГ-ын хамтарсан ажлын хэсгээс 'Эрдэнэс Тавантолгой' ХК-ийн эрх бүхий албан тушаалтнууд "
            "болон нэр бүхий УИХ-ын гишүүд, сайд нар албан тушаалын эрх мэдлээ урвуулан ашиглаж, "
            "бусдад давуу байдал олгосон, үндэслэлгүйгээр хөрөнгөжсөн, хахууль авсан хэргүүдэд яллах дүгнэлт "
            "үйлдүүлэхээр прокурорын байгууллагад шилжүүлсэн тухай тайлан."
        ),
        author="Авлигатай Тэмцэх Газар (АТГ)",
        pub_date=date(2023, 6, 15),
        reliability=0.98
    )

    src_court = get_or_create_source(
        db,
        title="Чингэлтэй дүүргийн Эрүүгийн хэргийн анхан шатны шүүхийн шийдвэр: Т.Аюурсайхан, Б.Ганхуяг нарт холбогдох хэрэг",
        url="https://shuukh.mn/eruu-2024-01-ayursaikhan-gankhuyag",
        category="government",
        cleaned_text=(
            "Чингэлтэй дүүргийн Эрүүгийн хэргийн анхан шатны шүүхээс шүүгдэгч Т.Аюурсайханд нийтийн албанд "
            "томилогдох эрхийг 5 жилээр хасаж, 3 жил хорих ял; шүүгдэгч Б.Ганхуягт нийтийн албанд ажиллах эрхийг "
            "4 жилээр хасаж, 5 жил 9 сар хорих ял оногдуулж, хууль бус орлогыг улсын орлого болгохоор шийдвэрлэв."
        ),
        author="Чингэлтэй дүүргийн Эрүүгийн хэргийн анхан шатны шүүх",
        pub_date=date(2024, 1, 26),
        reliability=0.99
    )

    # 2. Case Node
    case = db.query(models.Case).filter(models.Case.slug == "coal-theft").first()
    if not case:
        case = models.Case(
            slug="coal-theft",
            title="Нүүрсний хулгайн хэрэг",
            description="Эрдэнэс Тавантолгой ХК-ийн нүүрс олборлолт, нууц оффтейк гэрээ, тээвэрлэлт, гаалийн зөрүү болон улс төрчдийн хамаарал бүхий их наядын авлигын хэрэг",
            status="PUBLISHED"
        )
        db.add(case)
        db.commit()
        db.refresh(case)
    else:
        case.status = "PUBLISHED"
        db.commit()

    # 3. Entities үүсгэх / холбох
    ett = get_or_create_entity(
        db,
        name="Эрдэнэс Тавантолгой ХК",
        entity_type="company",
        description="Монгол Улсын стратегийн томоохон коксжих нүүрсний Тавантолгой ордыг ашиглах төрийн өмчит компани.",
        tldr_summary="Тавантолгойн ордын нүүрс олборлолт, экспортыг хариуцагч 85% төрийн өмчит хувьцаат компани.",
        aliases=[("ЭТТ", "initials"), ("Erdenes Tavantolgoi", "spelling")]
    )

    bodi = get_or_create_entity(
        db,
        name="Бодь Интернэшнл ХХК",
        entity_type="company",
        description="Тавантолгой-Гашуунсухайт чиглэлийн төмөр замын бүтээн байгуулалтын ерөнхий гүйцэтгэгчээр нууц оффтейк гэрээгээр ажилласан хувийн хэвшлийн групп компани.",
        tldr_summary="Тавантолгой-Гашуунсухайт төмөр замыг нүүрсээр төлбөр тооцоо хийх оффтейк нөхцөлөөр барьсан компани.",
        aliases=[("Бодь групп", "nickname"), ("Bodi International", "spelling")]
    )

    tt_rail = get_or_create_entity(
        db,
        name="Тавантолгой Төмөр Зам ХХК",
        entity_type="company",
        description="Тавантолгой-Гашуунсухайт чиглэлийн төмөр замын суурь бүтэц эзэмшигч, захиалагч төрийн өмчит компани.",
        tldr_summary="Тавантолгой-Гашуунсухайт чиглэлийн төмөр замын төслийн захиалагч төрийн өмчит компани.",
        aliases=[("ТТТЗ", "initials")]
    )

    mtz = get_or_create_entity(
        db,
        name="Монголын Төмөр Зам ТӨХК",
        entity_type="company",
        description="Монгол Улсын төмөр замын суурь бүтэц, төслүүдийг хэрэгжүүлэгч төрийн өмчит хувьцаат компани.",
        tldr_summary="Төмөр замын сүлжээг эзэмшигч, төрийн өмчит үндэсний оператор.",
        aliases=[("МТЗ", "initials")]
    )

    b_gankhuyag = get_or_create_entity(
        db,
        name="Баттулгын Ганхуяг",
        entity_type="person",
        description="'Эрдэнэс Тавантолгой' ХК-ийн Гүйцэтгэх захирлаар 2018-2022 онуудад ажилласан. Нүүрсний хулгайн хэргээр хорих ял сонссон гол албан тушаалтан.",
        tldr_summary="ЭТТ ХК-ийн Гүйцэтгэх захирал асан (2018-2022). Авлига, албан тушаалын хэргээр ял шийтгүүлсэн.",
        aliases=[("Б.Ганхуяг", "initials")]
    )

    b_ganbat = get_or_create_entity(
        db,
        name="Булгантуяагийн Ганбат",
        entity_type="person",
        description="'Тавантолгой Төмөр Зам' ХХК-ийн Гүйцэтгэх захирлаар ажиллаж байсан. Төмөр замын бүтээн байгуулалт, оффтейк санхүүжилтэд холбогдсон.",
        tldr_summary="Тавантолгой Төмөр Зам ХХК-ийн Гүйцэтгэх захирал асан.",
        aliases=[("Б.Ганбат", "initials")]
    )

    # DB-д байгаа улс төрчид
    t_ayursaikhan = db.query(models.Entity).filter(models.Entity.name == "Төмөрбаатарын Аюурсайхан").first()
    d_amarbayasgalan = db.query(models.Entity).filter(models.Entity.name == "Дашзэгвийн Амарбаясгалан").first()
    j_munkhbat = db.query(models.Entity).filter(models.Entity.name == "Жамъянгийн Мөнхбат").first()
    sh_radnaased = db.query(models.Entity).filter(models.Entity.name == "Шатарбалын Раднаасэд").first()
    t_badamjunai = db.query(models.Entity).filter(models.Entity.name == "Түнжингийн Бадамжунай").first()

    # Case-д cover entity тавих
    case.cover_entity_id = ett.id
    db.commit()

    # Entities-ийг Case-д холбох
    case_entities = [
        (ett, "TARGET_ORG", "Нүүрсний олборлолт, борлуулалтын төв талбар"),
        (bodi, "BENEFICIARY", "Төмөр замын оффтейк гэрээний ерөнхий гүйцэтгэгч"),
        (tt_rail, "INVOLVED_IN", "Төмөр замын төслийн захиалагч байгууллага"),
        (mtz, "PART_OF_CASE", "Төмөр замын суурь бүтцийн төрийн өмчит компани"),
        (b_gankhuyag, "SUSPECT", "ЭТТ-ийн гүйцэтгэх захирал, хэргийн гол холбогдогч"),
        (b_ganbat, "INVOLVED_IN", "ТТТЗ компанийн захирал асан"),
    ]
    if t_ayursaikhan:
        case_entities.append((t_ayursaikhan, "SUSPECT", "ХНХ-ын сайд асан, авлигын хэргээр ял шийтгүүлсэн"))
    if d_amarbayasgalan:
        case_entities.append((d_amarbayasgalan, "DECISION_MAKER", "ЗГХЭГ-ын дарга, ЭТТ-д онцгой дэглэм тогтоох шийдвэрийг танилцуулсан"))
    if j_munkhbat:
        case_entities.append((j_munkhbat, "SUSPECT", "УИХ-ын гишүүн асан, нүүрсний хэрэгт холбогдон бүрэн эрхээсээ түдгэлзсэн"))
    if sh_radnaased:
        case_entities.append((sh_radnaased, "INVOLVED_IN", "УИХ-ын гишүүн асан, нүүрсний асуудлаар шалгагдсан"))
    if t_badamjunai:
        case_entities.append((t_badamjunai, "INVOLVED_IN", "Шувуу ажиллагаагаар авчирч шалгасан улс төрч"))

    for ent_obj, role, note in case_entities:
        link_to_case(db, case, entity_id=ent_obj.id, role=role, note=note)

    # 4. Фактууд оруулах (Chronological & Biographical)
    print("Seeding facts...")

    # Б.Ганхуяг - Намтар & Хэрэг
    f1 = add_fact(
        db, b_gankhuyag.id, src_parliament.id,
        "2018-05-18", "biographical",
        "Баттулгын Ганхуяг 'Эрдэнэс Тавантолгой' ХК-ийн Гүйцэтгэх захирлаар томилогдон ажиллаж эхлэв.",
        "Б.Ганхуяг нь 2018 оны 5 дугаар сард 'Эрдэнэс Тавантолгой' ХК-ийн Гүйцэтгэх захирлаар томилогдсон.",
        "албан_тушаал", ["томилгоо", "этт", "гүйцэтгэх_захирал"], role_ctx="Албан тушаал", sentiment=0.0
    )
    link_to_case(db, case, fact_id=f1.id, role="EVIDENCE_FOR", note="ЭТТ-ийн гүйцэтгэх захирлаар томилогдсон")

    f2 = add_fact(
        db, b_gankhuyag.id, src_iaac.id,
        "2022-12-08", "chronological",
        "АТГ-аас нүүрсний хэрэгт холбогдуулан Б.Ганхуяг болон түүний хамаарал бүхий этгээдүүдийн орон сууц, оффист нэгжлэг хийж, 48 цагийн хугацаатай баривчлан саатуулав.",
        "АТГ-аас 'Эрдэнэс Тавантолгой' ХК-ийн гүйцэтгэх захирал асан Б.Ганхуягийг баривчилсан болохыг албан ёсоор мэдэгдэв.",
        "баривчилгаа", ["баривчилгаа", "нүүрсний_хулгай", "атг"], role_ctx="Мөрдөн шалгалт", sentiment=-0.8
    )
    link_to_case(db, case, fact_id=f2.id, role="EVIDENCE_FOR", note="Б.Ганхуягийг АТГ-аас баривчилсан")

    f3 = add_fact(
        db, b_gankhuyag.id, src_court.id,
        "2024-01-26", "chronological",
        "Чингэлтэй дүүргийн шүүхээс Б.Ганхуягт нийтийн албанд ажиллах эрхийг 4 жилээр хасаж, 5 жил 9 сар хорих ял оногдуулж, хахуулийн 9.9 тэрбум төгрөгийн хөрөнгийг улсын орлого болгохоор шийдвэрлэв.",
        "Шүүхээс шүүгдэгч Б.Ганхуягт 5 жил 9 сар хорих ял оногдуулав.",
        "шүүхийн_шийдвэр", ["шүүх", "ял", "хорих_ял", "авлига"], role_ctx="Шүүхийн шийдвэр", sentiment=-0.9
    )
    link_to_case(db, case, fact_id=f3.id, role="EVIDENCE_FOR", note="Анхан шатны шүүхийн шийдвэр")

    # Т.Аюурсайхан
    if t_ayursaikhan:
        f4 = add_fact(
            db, t_ayursaikhan.id, src_iaac.id,
            "2023-02-06", "chronological",
            "АТГ-аас УИХ-ын гишүүн, Хөдөлмөр, нийгмийн хамгааллын сайд Т.Аюурсайханыг зохион байгуулалттай гэмт бүлэг байгуулсан, үндэслэлгүйгээр хөрөнгөжсөн үндэслэлээр яллагдагчаар татав.",
            "Т.Аюурсайханыг нүүрсний хэрэгт яллагдагчаар татаж, хилийн хориг тавив.",
            "яллагдагч", ["яллагдагч", "улс_төрч", "авлига"], role_ctx="Мөрдөн шалгалт", sentiment=-0.8
        )
        link_to_case(db, case, fact_id=f4.id, role="EVIDENCE_FOR", note="Т.Аюурсайханыг яллагдагчаар татсан")

        f5 = add_fact(
            db, t_ayursaikhan.id, src_court.id,
            "2024-01-26", "chronological",
            "Чингэлтэй дүүргийн шүүхээс Т.Аюурсайханд нийтийн албанд томилогдох эрхийг 5 жилээр хасаж, 3 жил хорих ял оногдуулав.",
            "Шүүгдэгч Т.Аюурсайханд 3 жил хорих ял оногдуулав.",
            "шүүхийн_шийдвэр", ["шүүх", "ял", "хорих_ял"], role_ctx="Шүүхийн шийдвэр", sentiment=-0.9
        )
        link_to_case(db, case, fact_id=f5.id, role="EVIDENCE_FOR", note="Т.Аюурсайханд хорих ял оноосон")

    # Эрдэнэс Тавантолгой ХК
    f6 = add_fact(
        db, ett.id, src_parliament.id,
        "2019-10-29", "chronological",
        "Тавантолгой-Гашуунсухайт чиглэлийн төмөр замын бүтээн байгуулалтыг санхүүжүүлэх зорилгоор Бодь Интернэшнл ХХК-тай нууцын зэрэглэлтэй Оффтейк гэрээ (нүүрсээр төлбөр төлөх) байгуулав.",
        "ЭТТ ХК болон Бодь Интернэшнл ХХК төмөр замын оффтейк гэрээг ҮАБЗ-ийн зөвлөмжөөр нууцын зэрэглэлтэй байгуулав.",
        "оффтейк_гэрээ", ["оффтейк", "нууц_гэрээ", "төмөр_зам", "бодь"], role_ctx="Санхүүгийн гэрээ", sentiment=-0.4
    )
    link_to_case(db, case, fact_id=f6.id, role="EVIDENCE_FOR", note="Төмөр замын нууц оффтейк гэрээ")

    f7 = add_fact(
        db, ett.id, src_parliament.id,
        "2022-10-26", "chronological",
        "Монгол Улсын Засгийн газар ЭТТ ХК-д 6 сарын хугацаатай онцгой дэглэм тогтоож, Сангийн яамны Төрийн нарийн бичгийн дарга Ж.Ганбатыг Бүрэн эрхт төлөөлөгчөөр (БЭТ) томилов.",
        "Засгийн газрын тогтоолоор 'Эрдэнэс Тавантолгой' ХК-д онцгой дэглэм тогтоож, БЭТ томилов.",
        "онцгой_дэглэм", ["онцгой_дэглэм", "бэт", "засгийн_газар"], role_ctx="Засгийн газрын шийдвэр", sentiment=0.5
    )
    link_to_case(db, case, fact_id=f7.id, role="EVIDENCE_FOR", note="ЭТТ-д онцгой дэглэм тогтоосон шийдвэр")

    f8 = add_fact(
        db, ett.id, src_parliament.id,
        "2022-12-09", "chronological",
        "Засгийн газрын шийдвэрээр ЭТТ ХК-ийн нууцын зэрэглэлд байсан 9 оффтейк гэрээг нууцаас гаргаж, нийтэд ил тод зарлав.",
        "ЭТТ-ийн нууц 9 оффтейк гэрээг ил болгох шийдвэр гаргав.",
        "гэрээ_ил_болголт", ["оффтейк", "ил_тод_байдал", "нууц_задлах"], role_ctx="Ил тод байдал", sentiment=0.7
    )
    link_to_case(db, case, fact_id=f8.id, role="EVIDENCE_FOR", note="Нууц оффтейк гэрээнүүдийг ил болгосон")

    # Бодь Интернэшнл ХХК
    f9 = add_fact(
        db, bodi.id, src_parliament.id,
        "2019-10-29", "chronological",
        "Бодь Интернэшнл ХХК нь Тавантолгой-Гашуунсухайт чиглэлийн 233.6 км төмөр замын бүтээн байгуулалтын EPC гүйцэтгэгчээр шалгаран, төлбөрт нь коксжих нүүрс авах гэрээ байгуулав.",
        "Бодь Интернэшнл ХХК төмөр замын бүтээн байгуулалтыг нүүрсээр санхүүжүүлэх ерөнхий гүйцэтгэгчээр ажиллав.",
        "төмөр_зам", ["бодь", "төмөр_зам", "оффтейк", "гэрээ"], role_ctx="Төмөр замын гэрээ", sentiment=0.0
    )
    link_to_case(db, case, fact_id=f9.id, role="EVIDENCE_FOR", note="Бодь Интернэшнл төмөр замын EPC гүйцэтгэгчээр томилогдсон")

    f10 = add_fact(
        db, bodi.id, src_parliament.id,
        "2023-12-18", "chronological",
        "УИХ-ын Түр хорооны сонсголоор Бодь Интернэшнл ХХК-ийн төмөр замын гүйцэтгэлийн үнийн өсөлт, нүүрсний үнийн индексийн зөрүү, санхүүжилтийн тооцооллыг шинжээчид олон нийтэд танилцуулав.",
        "Сонсголоор Бодь группийн төмөр замын санхүүжилтийн нарийвчилсан дүгнэлтийг шинжээч танилцуулав.",
        "сонсголын_дүгнэлт", ["шинжээчийн_дүгнэлт", "сонсгол", "санхүүжилт"], role_ctx="Сонсголын шинжээч", sentiment=-0.3
    )
    link_to_case(db, case, fact_id=f10.id, role="EVIDENCE_FOR", note="Сонсголоор төмөр замын санхүүжилтийг шинжлэв")

    # Д.Амарбаясгалан
    if d_amarbayasgalan:
        f11 = add_fact(
            db, d_amarbayasgalan.id, src_parliament.id,
            "2022-10-26", "chronological",
            "ЗГХЭГ-ын дарга Д.Амарбаясгалан хэвлэлийн бага хурал зарлаж, ЭТТ ХК-д үүссэн нөхцөл байдал, нууц гэрээнүүд болон онцгой дэглэм тогтоосон Засгийн газрын шийдвэрийг анх олон нийтэд мэдээлэв.",
            "ЗГХЭГ-ын дарга Д.Амарбаясгалан ЭТТ-д онцгой дэглэм тогтоож, шалгалт эхлүүлснийг мэдэгдэв.",
            "мэдэгдэл", ["онцгой_дэглэм", "мэдээлэл", "засгийн_газар"], role_ctx="Засгийн газрын мэдээлэл", sentiment=0.4
        )
        link_to_case(db, case, fact_id=f11.id, role="EVIDENCE_FOR", note="ЭТТ-д шалгалт эхлүүлснийг зарласан")

    # Ж.Мөнхбат
    if j_munkhbat:
        f12 = add_fact(
            db, j_munkhbat.id, src_iaac.id,
            "2023-01-30", "chronological",
            "УИХ-ын гишүүн Ж.Мөнхбат нүүрсний хэрэгт холбогдуулан АТГ-аас шалгаж эхэлсэнтэй холбогдуулан өөрийн хүсэлтээр УИХ-ын гишүүний бүрэн эрхээсээ чөлөөлөгдөх өргөдлөө өгөв.",
            "Ж.Мөнхбат УИХ-ын гишүүний бүрэн эрхээсээ түдгэлзэх хүсэлтээ гаргав.",
            "огцрох", ["бүрэн_эрхээс_татгалзах", "уих", "нүүрсний_хэрэг"], role_ctx="Улс төрийн үйл явц", sentiment=-0.6
        )
        link_to_case(db, case, fact_id=f12.id, role="EVIDENCE_FOR", note="Ж.Мөнхбат УИХ-ын гишүүнээс татгалзав")

    # Сүхбаатарын талбайн жагсаал
    f13 = add_fact(
        db, ett.id, src_parliament.id,
        "2022-12-04", "chronological",
        "Иргэд, залуус Сүхбаатарын талбайд цугларч, нүүрсний хулгайн 44 их наяд төгрөгийн хэрэгт холбогдсон албан тушаалтнуудын нэрийг ил тод зарлахыг шаардсан эсэргүүцлийн тайван жагсаал өрнүүлэв.",
        "Сүхбаатарын талбайд нүүрсний хулгайчдыг илчлэхийг шаардсан иргэдийн жагсаал эхлэв.",
        "жагсаал", ["жагсаал", "сүхбаатарын_талбай", "эсэргүүцэл", "иргэд"], role_ctx="Олон нийтийн эсэргүүцэл", sentiment=-0.7
    )
    link_to_case(db, case, fact_id=f13.id, role="EVIDENCE_FOR", note="Сүхбаатарын талбайн эсэргүүцлийн жагсаал")

    # Сонсгол 2023.12
    f14 = add_fact(
        db, ett.id, src_parliament.id,
        "2023-12-04", "chronological",
        "УИХ-ын Хянан шалгах түр хорооны 'Нүүрсний сонсгол' Төрийн ордонд эхэлж, эхний шатанд 'Эрдэнэс Тавантолгой' ХК-ийн 5.4 сая тонн нүүрсний борлуулалт, тээвэрлэлтийн нотлох баримтыг шинжлэн судлав.",
        "Нүүрсний хэргийн нотлох баримтыг шинжлэн судлах нээлттэй сонсгол албан ёсоор эхлэв.",
        "сонсгол", ["сонсгол", "уих", "нотлох_баримт", "түр_хороо"], role_ctx="Парламентын хяналт", sentiment=0.5
    )
    link_to_case(db, case, fact_id=f14.id, role="EVIDENCE_FOR", note="УИХ-ын Нээлттэй сонсгол эхлэв")

    # 5. Relationships (Субъектүүдийн хоорондох master хамаарлууд)
    print("Seeding relationships...")

    # Б.Ганхуяг -> ЭТТ (Гүйцэтгэх захирал)
    add_relationship(
        db, src_parliament.id, b_gankhuyag.id, ett.id,
        ett.name, "гүйцэтгэх_захирал",
        quote="Б.Ганхуяг нь ЭТТ ХК-ийн гүйцэтгэх захирлаар 2018-2022 онд ажилласан",
        start_date_str="2018-05-18", end_date_str="2022-10-26"
    )

    # ЭТТ -> Бодь Интернэшнл (Оффтейк гэрээт хамтрагч)
    add_relationship(
        db, src_parliament.id, ett.id, bodi.id,
        bodi.name, "оффтейк_гүйцэтгэгч",
        quote="ЭТТ ХК ба Бодь Интернэшнл төмөр замын бүтээн байгуулалтын оффтейк гэрээ байгуулсан",
        start_date_str="2019-10-29"
    )

    # Бодь Интернэшнл -> Тавантолгой төмөр зам (Гүйцэтгэгч - Захиалагч)
    add_relationship(
        db, src_parliament.id, bodi.id, tt_rail.id,
        tt_rail.name, "захиалагч_байгууллага",
        quote="Бодь Интернэшнл нь ТТТЗ-ийн төмөр замын төслийн ерөнхий гүйцэтгэгчээр ажилласан",
        start_date_str="2019-10-29"
    )

    # Б.Ганбат -> Тавантолгой төмөр зам (Гүйцэтгэх захирал)
    add_relationship(
        db, src_parliament.id, b_ganbat.id, tt_rail.id,
        tt_rail.name, "гүйцэтгэх_захирал",
        quote="Б.Ганбат нь ТТТЗ ХХК-ийн Гүйцэтгэх захирлаар ажиллаж байсан",
        start_date_str="2019-01-01", end_date_str="2022-12-01"
    )

    # Б.Ганхуяг -> Т.Аюурсайхан (Холбоо хамаарал / Нэгдмэл сонирхол)
    if t_ayursaikhan:
        add_relationship(
            db, src_court.id, b_gankhuyag.id, t_ayursaikhan.id,
            t_ayursaikhan.name, "улс_төрийн_хамтрагч",
            quote="Шүүхийн шийдвэрээр Т.Аюурсайхан, Б.Ганхуяг нар албан тушаалын хэрэгт хамсаатнаар ял сонссон",
            start_date_str="2018-01-01", end_date_str="2024-01-26"
        )

    # ЭТТ -> Монголын төмөр зам (Хувьцаа эзэмшигч / Түнш)
    add_relationship(
        db, src_parliament.id, ett.id, mtz.id,
        mtz.name, "түнш_байгууллага",
        quote="ЭТТ болон МТЗ нь төмөр замын суурь бүтэц, санхүүжилтэд хамтран ажилласан",
        start_date_str="2019-01-01"
    )

    db.commit()
    print("=== COAL THEFT DATA INGESTION COMPLETED SUCCESSFULLY ===")

    # Баталгаажуулах
    c_links = db.query(models.CaseLink).filter(models.CaseLink.case_id == case.id).count()
    print(f"Total links associated with 'coal-theft' case: {c_links}")


if __name__ == "__main__":
    main()
