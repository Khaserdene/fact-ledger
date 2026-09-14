# 📋 Үнэний Бүртгэл — Өөрчлөгдөшгүй Баримтын Платформ

Нийтлэлүүдээс улс төрч болон нийтийн хүмүүсийн мэдэгдлийг SHA-256 хэшээр баталгаажуулж, цаг хугацааны шугам дээр харагдуулж, зөрчлийг илрүүлэх платформ.

---

## ⚡ Хурдан асаах

`start.bat` файлыг давхар дарна → браузер автоматаар нээгдэнэ.

```
E:\profiling_facts\start.bat
```

**URL:** http://localhost:5200

---

## 📦 Шинээр суулгах (clone-оос)

```bat
:: 1. Clone
git clone https://github.com/Khaserdene/fact-ledger.git
cd fact-ledger

:: 2. Backend — venv үүсгэж хамаарлууд суулгах
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt

:: 3. Орчны тохиргоо (заавал биш — AI_PROVIDER=manual defaults ажилладаг)
copy .env.example .env

:: 4. Өгөгдлийн сан — repo-д бэлэн profiling_facts.db орсон тул
::    alembic шаардлагагүй. Хэрвээ хоосон эхлэх бол:
::    venv\Scripts\python -m alembic upgrade head

:: 5. Асаах
start "API" venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8020
cd ..\frontend
npm install
npm run dev
```

Frontend: http://localhost:5200 · API: http://127.0.0.1:8020/docs

---

## 🛠 Гараар асаах

### Шаардлага

| Хэрэгсэл | Хувилбар |
|---|---|
| Python | 3.14 (шлях: `C:\Users\HiTech\AppData\Local\Python\pythoncore-3.14-64\`) |
| Node.js | 18+ |
| npm | 9+ |

### Backend

```bat
cd E:\profiling_facts\backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

> API: http://127.0.0.1:8020
> Swagger docs: http://127.0.0.1:8020/docs

### Frontend

```bat
cd E:\profiling_facts\frontend
npm run dev
```

> Платформ: http://localhost:5200

---

## 📁 Файлын бүтэц

```
profiling_facts/
├── start.bat                   ← Нэг дарж асаах
├── README.md
│
├── backend/
│   ├── main.py                 ← FastAPI app + бүх endpoint
│   ├── models.py               ← SQLAlchemy (articles, profiles, facts, contradictions)
│   ├── schemas.py              ← Pydantic request/response
│   ├── scraper.py              ← URL → DOM цэвэрлэгч (Wikipedia Special:Export дэмждэг)
│   ├── hasher.py               ← SHA-256 тогтвортой хэш
│   ├── contradiction.py        ← Зөрчил хадгалах логик
│   ├── requirements.txt
│   └── profiling_facts.db      ← SQLite өгөгдлийн сан (автоматаар үүснэ)
│
└── frontend/
    └── src/
        ├── App.jsx             ← Router + навигац
        ├── api.js              ← Backend-тэй холбогч
        └── pages/
            ├── ArticleList.jsx     ← Нийтлэлүүдийн жагсаалт
            ├── ArticleCapture.jsx  ← URL → текст сонгох → хадгалах
            ├── ArticleView.jsx     ← Нийтлэл харах + факт хайрцаг + Эх текст таб
            ├── ProfileList.jsx     ← Профайлуудын жагсаалт
            ├── ProfileDetail.jsx   ← Цаг хугацааны шугам + зөрчил
            └── FactImport.jsx      ← AI промпт үүсгэх + JSON факт оруулах
```

---

## 🔄 Хэрэглээний дараалал

### 1. Нийтлэл нэмэх
1. **"+ Нийтлэл нэмэх"** → URL оруулах
2. Систем HTML татаж, зураг/реклам/скрипт устгана
3. Текст блокуудыг харуулна — бүгдийг автоматаар сонгосон байна
4. **Блок toggle горим:** Хэрэггүй хэсгийг дарж идэвхгүйжүүлнэ
5. **Маркер горим:** Хулганаар чирч, "Нэмэх" дарна
6. Огноог шалгаад → **"Баталгаажуулж хадгалах"**

> Wikipedia линк оруулбал `mn.wikipedia.org/wiki/Special:Export` API-г ашиглана — 403 алдаа гарахгүй.

### 2. Профайл үүсгэх
1. **"Профайлууд"** → **"+ Профайл үүсгэх"**
2. Үндсэн нэр + нэрийн бүх хувилбар (таслалаар): `Д.Бат, Бат сайд, Доржийн Бат`

### 3. Фактуудыг нэмэх (AI-тэй)
1. Профайл дотроос **"+ Факт нэмэх"**
2. Нийтлэл сонгох
3. **"⚙️ Промпт үүсгэх"** → textarea-д бүтэн промпт гарна
4. **"📋 Бүгдийг хуулах"** товч дарах — эсвэл textarea дотор дарж Ctrl+C
5. ChatGPT / Claude-д Ctrl+V paste хийх
6. AI-ийн JSON хариуг буцааж paste хийх
7. **"✓ Фактуудыг хадгалах"**

> Промпт дотор **одоогийн бүх фактууд** (`fact_id`, `fact`, `fact_date`, `role_context`) орсон байна →
> AI давхардлыг таньж алгасна.

### 4. Фактуудыг солих / дахин оруулах
- Профайл дэлгэрэнгүй хуудаснаас **"🔄 Фактуудыг цэвэрлэх"** → бүх факт устна, профайл хэвээр
- Дараа нь дахин **"+ Факт нэмэх"** → import хийнэ

### 5. Нийтлэл харах
- **"Нийтлэл" таб:** Фактуудтай холбогдсон текст ногоон/улаан хайрцгаар харагдана
- **"Эх текст" таб:** Баталгаажуулсан бүтэн цэвэр текст (нэг дарахад сонгогдоно)

---

## 🔐 Хэш тэмдэглэгээ

SHA-256 хэш нь дараах зүйлсийг **орхиж** тооцоолно:
- Зураг, видео, аудио
- JavaScript, CSS
- Рекламны блокууд
- Нийгмийн мэдийн виджетүүд

Иймд жилийн дараа тухайн сайтыг дахин шалгахад хэш зөрөхгүй.

---

## 🌐 API

| Endpoint | Тайлбар |
|---|---|
| `POST /scrape` | URL-аас текст татах |
| `POST /articles` | Нийтлэл хадгалах |
| `GET /articles/{id}` | Нийтлэл + фактуудтай |
| `DELETE /articles/{id}` | Нийтлэл устгах |
| `GET /profiles` | Профайлуудын жагсаалт |
| `POST /profiles` | Профайл үүсгэх |
| `PUT /profiles/{id}` | Профайл засах |
| `DELETE /profiles/{id}` | Профайл + бүх фактуудыг устгах |
| `GET /profiles/{id}/facts` | Профайлын фактууд |
| `DELETE /profiles/{id}/facts` | Профайлын бүх фактуудыг устгах (профайл хэвээр) |
| `GET /profiles/{id}/export-json` | AI промпт бэлтгэх JSON (fact_date, role_context орсон) |
| `POST /profiles/{id}/import-facts` | AI JSON → факт хадгалах (давхардал автоматаар алгасна) |
| `DELETE /facts/{id}` | Нэг факт устгах |

Swagger: http://127.0.0.1:8020/docs

---

## 🧩 Техникийн дэлгэрэнгүй

### Scraper (`scraper.py`)
- Wikipedia URL → `Special:Export` XML API → `urllib.request` (httpx 403 гарахгүй)
- Бусад сайт → `httpx` + `BeautifulSoup` (html.parser, lxml биш)
- Блокийн формат: `{"type": "h2", "text": "..."}` — heading, p, li, blockquote
- Нийтлэгдсэн огноо олдоогүй бол frontend-д өнөөдрийн огноогоор автоматаар бөглөнө

### Огнооны формат (`main.py` → `_parse_fact_date`)
AI-аас ирэх бүх огнооны хэлбэрийг дэмждэг:

| AI өгөх | Хадгалах | Харагдах |
|---|---|---|
| `"1968"` | 1968-01-01 | 1968 |
| `"1968-05"` | 1968-05-01 | 1968-05 |
| `"1968-05-15"` | 1968-05-15 | 1968-05-15 |
| `"1968-1969"` | 1968-01-01 | 1968 |

### Давхардал шалгалт (`main.py` → `import_facts`)
Import хийхдээ автоматаар шалгана:
- **Он цагийн факт:** `fact_text` + `fact_date` хоёулаа ижил бол алгасна
- **Намтар факт:** `fact_text` ижил бол алгасна
- Хариуд `skipped_duplicates` тоо буцаана

### JSON автозасвар (`FactImport.jsx` → `autoFixJson`)
AI-ийн гаралтанд `"Үнэн"` гэх мэт дотоод хашилт байвал автоматаар `\"Үнэн\"` болгон засна.
Арга: мөр бүрийг уншиж, `"fact"`, `"source_quote"` зэрэг талбарын утгын хамгийн сүүлийн `"` хүртэл greedy match хийнэ.

### Cascade устгалт
SQLAlchemy relationship cascade тохиргоо ашиглахгүй — endpoint бүрт гараар устгана:
- Профайл устгах → зөрчил → фактууд → профайл
- Факт устгах → зөрчил → факт
- Профайлын фактуудыг цэвэрлэх → зөрчил → фактууд

### Промпт бүтэц (`FactImport.jsx`)
```
[ХУУЧИН_ПРОФАЙЛ_JSON]  — primary_name, aliases, biographical_facts, chronological_facts
                          (fact_id, fact, fact_date, source_quote, role_context, tags орсон)
[ШИНЭ_НИЙТЛЭЛ_ТЕКСТ]  — article.selected_text
```
AI-д өгөх заавар: давхардал алгасах, JSON дотор `"` ашиглахгүй (`«»` эсвэл `'` ашиглах).

---

## ⚠️ Мэдэгдэж буй онцлогууд

- **Нэг хэрэглэгч** — нэвтрэх систем байхгүй
- **`cleaned_text` = `selected_text`** — DB-д хоёр адил талбар байгаа, цаашид нэгийг хасах боломжтой
- **Wikipedia хязгаарлалт** — `Special:Export` нийтийн API, ердийн хэрэглээнд хязгаар байхгүй
- **Огнооны нарийвчлал** — жилийн мэдээлэл л байвал `YYYY-01-01` болж хадгалагддаг; цаг хугацааны шугамд зөв жилдээ харагдана
