"""
blood.ai | FastAPI Server
==========================
혈액 수치 + 생활 맥락 기반 영양제·식품·루틴 추천 API.
Render 배포용 — 시작 시 SQLite DB 초기화.
"""

import os, math, sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── 앱 설정 ──────────────────────────────────────────────────
app = FastAPI(title="blood.ai API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = os.path.dirname(__file__)
DB   = os.path.join(BASE, "blood_ai.db")


# ── DB 초기화 (Render 시작 시마다 실행) ──────────────────────
@app.on_event("startup")
def init_db():
    conn = sqlite3.connect(DB)
    with open(os.path.join(BASE, "schema.sql")) as f:
        conn.executescript(f.read())
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        with open(os.path.join(BASE, "seed_data.sql")) as f:
            conn.executescript(f.read())
    conn.commit()
    conn.close()


# ── 스코어링 로직 (클라이언트 로직과 동일) ───────────────────
W = dict(biomarker=0.35, nutrition=0.25, context=0.20, preference=0.10, adherence=0.10)

NEED_FN = {
    "LDL":     lambda v: min(max(0, (v-100)/100), 1),
    "HDL":     lambda v: min(max(0, (50-v)/30),   1),
    "TG":      lambda v: min(max(0, (v-100)/150),  1),
    "GLUCOSE": lambda v: min(max(0, (v-90)/60),    1),
    "VITD":    lambda v: min(max(0, (30-v)/30),    1),
    "HB":      lambda v: min(max(0, (13-v)/6),     1),
    "FERRITIN":lambda v: min(max(0, (15-v)/15),    1),
    "ALT":     lambda v: min(max(0, (v-30)/90),    1),
    "TSH":     lambda v: min(max(0, (v-2.5)/3.0),  1),
    "URIC":    lambda v: min(max(0, (v-5.0)/3.0),  1),
    "CR":      lambda v: min(max(0, (v-1.0)/1.0),  1),
}

def need_score(code, val):
    if val is None: return 0.0
    fn = NEED_FN.get(code)
    return max(0.0, fn(val)) if fn else 0.0

def bio_area(mk):
    return {
        "lipid":   min(1, need_score("LDL",mk.get("LDL",0))*.5 + need_score("TG",mk.get("TG",0))*.3 + need_score("HDL",mk.get("HDL",0))*.2),
        "glucose": need_score("GLUCOSE", mk.get("GLUCOSE") or mk.get("GL", 0)),
        "vitd":    need_score("VITD",    mk.get("VITD") or mk.get("VD", 0)),
        "iron":    min(1, need_score("HB",mk.get("HB",0))*.5 + need_score("FERRITIN",mk.get("FERRITIN") or mk.get("FE",0))*.5),
        "liver":   need_score("ALT", mk.get("ALT", 0)),
        "renal":   1 if (mk.get("CR") or 0) > 1.4 else 0,
        "uric":    need_score("URIC", mk.get("URIC", 0)),
        "tsh":     need_score("TSH", mk.get("TSH", 0)),
    }

def cosine(a, b):
    dot   = sum(x*y for x,y in zip(a,b))
    norm_a = math.sqrt(sum(x*x for x in a))
    norm_b = math.sqrt(sum(x*x for x in b))
    return dot / (norm_a * norm_b + 1e-9)

def food_fit(food, bio):
    fv = [min(food["fiber"]/5,1), min(food["iron"]/3,1), min(food["vitd"]/10,1),
          max(0,1-food["sat_fat"]/5), max(0,1-food["sodium"]/800)]
    hv = [max(bio["glucose"],bio["lipid"]), bio["iron"], bio["vitd"],
          bio["lipid"], bio["lipid"]*.5+bio["liver"]*.5]
    return cosine(fv, hv)

def ctx_sc(type_, ctx):
    sd  = ctx.get("sd", 0)
    sn  = ctx.get("sn", 0)
    lm  = ctx.get("lm", 0)
    bf  = ctx.get("bf", 0)
    if type_ == "supplement": return min(1, .5 + sd*.06 + sn*.06)
    if type_ == "food":       return min(1, .5 - lm*.12 + (1-bf)*.06)
    if type_ == "routine":    return min(1, .4 + sn*.18 + sd*.12)
    return .5

def final_score(sc):
    return sum(W[k]*sc[k] for k in W)

SUPP_ICONS = {
    "lipid": "🐠", "vitd": "☀️", "glucose": "💊",
    "iron": "🔴", "immune": "🔷", "liver": "🌿",
}

FOOD_ICONS = {
    "고등어구이": "🐟", "연어스테이크": "🍣", "현미밥": "🍚",
    "시금치나물": "🥬", "두부조림": "🍱", "아몬드": "🥜",
    "삶은 계란": "🥚", "그릭요거트": "🫙", "브로콜리볶음": "🥦",
    "렌틸콩수프": "🫘", "잡곡밥": "🍚", "닭가슴살": "🍗",
    "아보카도": "🥑",
}

def mmr(items, k=5, lam=.6):
    if not items: return []
    sel   = [items[0]]
    rem   = items[1:]
    while len(sel) < k and rem:
        best, bs = None, -float("inf")
        for c in rem:
            sim = 1.0 if any(s["type"] == c["type"] for s in sel) else 0.0
            sc  = lam * c["final"] - (1-lam) * sim
            if sc > bs:
                bs, best = sc, c
        if best:
            sel.append(best)
            rem.remove(best)
    return sel


# ── 안전 필터 ─────────────────────────────────────────────────
SAFETY_MAP = {
    "항응고제": ["오메가3 (EPA/DHA)", "코엔자임Q10"],
    "신장질환": ["마그네슘", "베르베린"],
    "임신수유": ["베르베린"],
}

def is_safe(supp_name, risk_tags, conds, mk):
    if (mk.get("ALT") or 0) >= 120: return False
    if (mk.get("CR")  or 0) >= 1.5 and "renal_caution" in risk_tags: return False
    for c in conds:
        blocked = SAFETY_MAP.get(c, [])
        if supp_name in blocked: return False
    return True


# ── 요청 모델 ─────────────────────────────────────────────────
class RecommendReq(BaseModel):
    markers:    dict = {}
    conditions: list = []
    context:    dict = {}
    top_k:      int  = 5


# ── 엔드포인트 ────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "db_exists": os.path.exists(DB)}


@app.post("/api/recommend")
def api_recommend(req: RecommendReq):
    mk   = req.markers
    conds = req.conditions
    raw_ctx = req.context
    ctx = {
        "sd": max(0, 8 - raw_ctx.get("sleep", 7)),
        "sn": (raw_ctx.get("stress", 3) - 1) / 4,
        "bf": raw_ctx.get("bf", raw_ctx.get("breakfast", 3)) / 7,
        "lm": raw_ctx.get("lm", raw_ctx.get("late_meal", 1)) / 7,
        "ex": raw_ctx.get("ex", raw_ctx.get("exercise", 0)),
    }
    bio = bio_area(mk)
    cands = []

    conn = sqlite3.connect(DB)

    # 영양제 후보
    supps = conn.execute(
        "SELECT ingredient_name, target_biomarker, risk_tags FROM supplement_master"
    ).fetchall()
    area_map = {
        "VITD": "vitd", "LDL": "lipid", "TG": "lipid",
        "GLUCOSE_FASTING": "glucose", "HB": "iron", "FERRITIN": "iron",
        "ALT": "liver", "AST": "liver",
    }
    for name, target, risk_tags_raw in supps:
        risk_tags = []
        try:
            import json; risk_tags = json.loads(risk_tags_raw or "[]")
        except: pass
        if not is_safe(name, risk_tags, conds, mk): continue
        area   = area_map.get(target, "")
        bm_fit = bio.get(area, 0)
        if bm_fit < 0.12: continue
        sc = dict(biomarker=bm_fit, nutrition=bm_fit*.85,
                  context=ctx_sc("supplement", ctx), preference=.80, adherence=.72)
        icon = SUPP_ICONS.get(area, "💊")
        cands.append(dict(
            type="supplement", icon=icon, name=name,
            reason=f"{name} 보충을 권장합니다.",
            scores=sc, final=final_score(sc),
            biomarker_fit=round(bm_fit, 3),
            context_score=round(ctx_sc("supplement", ctx), 3),
        ))

    # 식품 후보
    foods = conn.execute(
        "SELECT name_ko, fiber_g, iron_mg, vitamin_d_ug, saturated_fat_g, sodium_mg FROM food_master"
    ).fetchall()
    for fname, fiber, iron, vitd, sat_fat, sodium in foods:
        food = dict(fiber=fiber or 0, iron=iron or 0, vitd=vitd or 0,
                    sat_fat=sat_fat or 0, sodium=sodium or 0)
        nf = food_fit(food, bio)
        if nf < 0.28: continue
        sc = dict(biomarker=nf*.9, nutrition=nf,
                  context=ctx_sc("food", ctx), preference=.76, adherence=.80)
        icon = FOOD_ICONS.get(fname, "🍽️")
        cands.append(dict(
            type="food", icon=icon, name=fname,
            reason=f"오늘 관리 지표 개선에 도움이 되는 {fname}을(를) 권장합니다.",
            scores=sc, final=final_score(sc),
            biomarker_fit=round(nf*.9, 3),
            context_score=round(ctx_sc("food", ctx), 3),
        ))

    conn.close()

    # 루틴 후보
    if bio["glucose"] >= .35 or ctx.get("lm", 0) >= .4:
        sc = dict(biomarker=bio["glucose"], nutrition=.5, context=ctx_sc("routine",ctx), preference=.70, adherence=.62)
        cands.append(dict(type="routine", icon="🍽️", name="야식 제한 & 아침식사 루틴",
            reason="혈당 관리를 위해 야식을 줄이고 아침 식사를 규칙적으로 하는 루틴을 권장합니다.",
            scores=sc, final=final_score(sc),
            biomarker_fit=round(bio["glucose"],3), context_score=round(ctx_sc("routine",ctx),3)))
    if ctx.get("sd", 0) >= 1.5:
        sc = dict(biomarker=.4, nutrition=.3, context=ctx_sc("routine",ctx), preference=.75, adherence=.65)
        cands.append(dict(type="routine", icon="😴", name="수면 개선 루틴",
            reason=f"수면 부족({raw_ctx.get('sleep',7)}시간) — 취침 1시간 전 스크린을 줄이고 일정한 수면 시간을 유지하세요.",
            scores=sc, final=final_score(sc),
            biomarker_fit=0.4, context_score=round(ctx_sc("routine",ctx),3)))
    if not raw_ctx.get("exercise", raw_ctx.get("ex", 1)):
        sc = dict(biomarker=max(bio["lipid"],bio["glucose"])*.7, nutrition=.3, context=ctx_sc("routine",ctx), preference=.75, adherence=.58)
        cands.append(dict(type="routine", icon="🏃", name="유산소 운동 루틴",
            reason="운동 없음 — 주 3~5회 30분 이상 유산소 운동(빠르게 걷기, 자전거 등)을 권장합니다.",
            scores=sc, final=final_score(sc),
            biomarker_fit=round(max(bio["lipid"],bio["glucose"])*.7,3),
            context_score=round(ctx_sc("routine",ctx),3)))

    cands.sort(key=lambda x: x["final"], reverse=True)
    results = mmr(cands, k=req.top_k)

    return {"items": [
        {"type": r["type"], "icon": r["icon"], "name": r["name"],
         "score": round(r["final"], 3), "reason": r["reason"],
         "biomarker_fit": r["biomarker_fit"], "context_score": r["context_score"]}
        for i, r in enumerate(results)
    ]}


@app.get("/api/biomarkers/{user_id}")
def api_biomarkers(user_id: str):
    conn = sqlite3.connect(DB)
    rows = conn.execute("""
        SELECT br.biomarker_code, br.display_name_ko, br.value, br.unit,
               br.ref_low, br.ref_high, br.need_score, br.trend_score, br.interpretation
        FROM   biomarker_results br
        JOIN   blood_tests bt ON br.blood_test_id = bt.id
        WHERE  bt.user_id   = ?
          AND  bt.tested_at = (SELECT MAX(tested_at) FROM blood_tests WHERE user_id = ?)
        ORDER BY COALESCE(br.need_score,0) DESC
    """, (user_id, user_id)).fetchall()
    conn.close()
    return {"biomarkers": [
        {"code":r[0],"name":r[1],"value":r[2],"unit":r[3],
         "ref_low":r[4],"ref_high":r[5],"need_score":r[6],
         "trend_score":r[7],"interpretation":r[8]}
        for r in rows
    ]}
