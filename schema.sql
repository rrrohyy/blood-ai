-- =============================================================
-- blood.ai  |  DB Schema  (SQLite / PostgreSQL 호환)
-- KAIST Business Analytics and Data Mining
-- =============================================================

-- ─── 1. 사용자 도메인 ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id          TEXT        PRIMARY KEY,   -- UUID v4
    nickname    TEXT        NOT NULL,
    birth_year  INTEGER,
    sex         TEXT        CHECK(sex IN ('male','female','other','no_answer')),
    height_cm   REAL,
    weight_kg   REAL,
    budget_tier TEXT        CHECK(budget_tier IN ('low','mid','high','premium')),
    allergies   TEXT,                      -- JSON array
    created_at  DATETIME    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_goals (
    id          INTEGER     PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT        NOT NULL REFERENCES users(id),
    goal_type   TEXT        NOT NULL,      -- 혈당관리, 콜레스테롤관리, 간건강, 빈혈철분, 비타민D, 체중관리, 피로관리
    priority    INTEGER     DEFAULT 1,
    created_at  DATETIME    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_conditions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT    NOT NULL REFERENCES users(id),
    condition_type  TEXT    NOT NULL,  -- 신장질환, 간질환, 임신수유, 당뇨, 고혈압, 항응고제복용 등
    medication_name TEXT,
    risk_level      TEXT    CHECK(risk_level IN ('low','medium','high')),
    is_active       INTEGER DEFAULT 1,
    updated_at      DATETIME DEFAULT (datetime('now'))
);

-- ─── 2. 혈액검사 도메인 ───────────────────────────────────────

CREATE TABLE IF NOT EXISTS blood_tests (
    id             INTEGER  PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT     NOT NULL REFERENCES users(id),
    tested_at      DATE     NOT NULL,
    lab_name       TEXT,
    source_type    TEXT     CHECK(source_type IN ('manual','pdf','image_ocr','b2b_file','api')),
    raw_file_uri   TEXT,
    overall_status TEXT     CHECK(overall_status IN ('normal','watch','caution','consult')),
    created_at     DATETIME DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_blood_tests_user ON blood_tests(user_id, tested_at DESC);

CREATE TABLE IF NOT EXISTS biomarker_results (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    blood_test_id    INTEGER NOT NULL REFERENCES blood_tests(id),
    biomarker_code   TEXT    NOT NULL,   -- GLUCOSE_FASTING, LDL, HDL, ALT, AST, GGT, HB, FERRITIN, VITD, CREATININE, EGFR 등
    display_name_ko  TEXT,
    value            REAL    NOT NULL,
    unit             TEXT,
    ref_low          REAL,
    ref_high         REAL,
    need_score       REAL,               -- 0~1 관리 필요도
    trend_score      REAL,               -- 이전 대비 개선(+)/악화(-)
    interpretation   TEXT
);

CREATE INDEX IF NOT EXISTS idx_biomarker_user_code ON biomarker_results(blood_test_id, biomarker_code);

-- ─── 3. 생활 맥락 로그 ───────────────────────────────────────

CREATE TABLE IF NOT EXISTS daily_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT    NOT NULL REFERENCES users(id),
    log_date        DATE    NOT NULL,
    sleep_hours     REAL,
    stress_level    INTEGER CHECK(stress_level BETWEEN 1 AND 5),
    schedule_type   TEXT    CHECK(schedule_type IN ('normal','remote','overtime','holiday')),
    skip_breakfast  INTEGER DEFAULT 0,
    late_meal_flag  INTEGER DEFAULT 0,
    alcohol_flag    INTEGER DEFAULT 0,
    exercise_min    INTEGER DEFAULT 0,
    created_at      DATETIME DEFAULT (datetime('now'))
);

-- ─── 4. 마스터 데이터 ────────────────────────────────────────

CREATE TABLE IF NOT EXISTS supplement_master (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    ingredient_name   TEXT    NOT NULL,
    product_name      TEXT,
    target_biomarker  TEXT    NOT NULL,  -- 연결되는 검사 지표 코드
    dosage_unit       TEXT,              -- IU, mg, ug 등
    dose_per_serving  REAL,
    risk_tags         TEXT,              -- JSON: ['renal_caution','medication_interaction','pregnancy_caution']
    price_band        TEXT    CHECK(price_band IN ('low','mid','high','premium')),
    evidence_level    TEXT    CHECK(evidence_level IN ('A','B','C','internal_rule')),
    source_name       TEXT
);

CREATE TABLE IF NOT EXISTS food_master (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    food_code        TEXT    UNIQUE,
    name_ko          TEXT    NOT NULL,
    serving_size_g   REAL,
    energy_kcal      REAL,
    protein_g        REAL,
    carb_g           REAL,
    fiber_g          REAL,
    sodium_mg        REAL,
    saturated_fat_g  REAL,
    iron_mg          REAL,
    vitamin_d_ug     REAL,
    source_name      TEXT    DEFAULT '식약처DB'
);

CREATE TABLE IF NOT EXISTS safety_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_code       TEXT    NOT NULL UNIQUE,
    condition_type  TEXT    NOT NULL,  -- 신장질환, 간질환, 임신, 항응고제 등
    blocked_ingredient TEXT,           -- 차단 성분명 (NULL이면 전체 고용량 차단)
    risk_threshold  REAL,              -- need_score 기준값
    rule_desc       TEXT,
    is_active       INTEGER DEFAULT 1
);

-- ─── 5. 추천 도메인 ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS recommendation_sessions (
    id                      INTEGER  PRIMARY KEY AUTOINCREMENT,
    user_id                 TEXT     NOT NULL REFERENCES users(id),
    blood_test_id           INTEGER  REFERENCES blood_tests(id),
    context_vector          TEXT,    -- JSON: 16차원 맥락 스냅샷
    biomarker_snapshot_json TEXT,    -- JSON: 추천 시점 핵심 수치
    safety_flags            TEXT,    -- JSON: 추천 제한 사유
    algorithm_version       TEXT     DEFAULT 'v1.0',
    created_at              DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS recommended_items (
    id                     INTEGER  PRIMARY KEY AUTOINCREMENT,
    session_id             INTEGER  NOT NULL REFERENCES recommendation_sessions(id),
    item_type              TEXT     CHECK(item_type IN ('supplement','food','routine','consult_alert')),
    item_id                INTEGER,
    biomarker_fit          REAL,    -- 검사 지표 적합도 (35%)
    nutrition_fit          REAL,    -- 영양소 부합도 (25%)
    context_score          REAL,    -- 맥락 선택 확률 (20%)
    preference_fit         REAL,    -- 선호도 적합도 (10%)
    adherence_fit          REAL,    -- 지속 가능성 (10%)
    safety_pass            INTEGER  DEFAULT 1,  -- 0/1
    final_score            REAL,
    recommendation_reason  TEXT,    -- 사용자용 추천 사유
    was_clicked            INTEGER  DEFAULT 0,
    was_taken              INTEGER  DEFAULT 0,
    was_stopped            INTEGER  DEFAULT 0,
    side_effect_note       TEXT,
    created_at             DATETIME DEFAULT (datetime('now'))
);

-- ─── 6. 동의·감사 로그 ───────────────────────────────────────

CREATE TABLE IF NOT EXISTS consent_logs (
    id              INTEGER  PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT     NOT NULL REFERENCES users(id),
    consent_type    TEXT     NOT NULL,  -- health_data, marketing, b2b_report, third_party
    is_agreed       INTEGER  NOT NULL,
    consent_version TEXT,
    agreed_at       DATETIME DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id          INTEGER  PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT,
    action      TEXT     NOT NULL,
    table_name  TEXT,
    record_id   TEXT,
    ip_address  TEXT,
    created_at  DATETIME DEFAULT (datetime('now'))
);

-- =============================================================
-- 뷰: 최신 검사 기준 관리 필요 지표 요약
-- =============================================================
CREATE VIEW IF NOT EXISTS v_latest_biomarkers AS
SELECT
    u.id          AS user_id,
    u.nickname,
    bt.tested_at,
    br.biomarker_code,
    br.display_name_ko,
    br.value,
    br.unit,
    br.ref_low,
    br.ref_high,
    br.need_score,
    br.trend_score,
    br.interpretation
FROM users u
JOIN blood_tests bt  ON bt.user_id = u.id
JOIN biomarker_results br ON br.blood_test_id = bt.id
WHERE bt.tested_at = (
    SELECT MAX(tested_at) FROM blood_tests WHERE user_id = u.id
);
