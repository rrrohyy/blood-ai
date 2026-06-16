-- =============================================================
-- blood.ai  |  Seed Data (데모용 샘플 데이터)
-- KAIST Business Analytics and Data Mining
-- =============================================================

-- ─── 사용자 2명 ──────────────────────────────────────────────
INSERT INTO users (id, nickname, birth_year, sex, height_cm, weight_kg, budget_tier, allergies)
VALUES
    ('user_001', '김건강', 1985, 'male',   175.0, 82.0, 'mid',  '[]'),
    ('user_002', '이웰니스', 1992, 'female', 163.0, 58.0, 'low',  '["새우","갑각류"]');

-- ─── 건강 목표 ────────────────────────────────────────────────
INSERT INTO user_goals (user_id, goal_type, priority) VALUES
    ('user_001', '콜레스테롤관리', 1),
    ('user_001', '혈당관리',       2),
    ('user_001', '비타민D',        3),
    ('user_002', '빈혈철분',       1),
    ('user_002', '피로관리',       2);

-- ─── 복약/기저질환 ───────────────────────────────────────────
INSERT INTO user_conditions (user_id, condition_type, medication_name, risk_level, is_active)
VALUES
    ('user_001', '고혈압', '암로디핀', 'medium', 1);

-- ─── 혈액검사 (user_001: 3회, user_002: 1회) ─────────────────
INSERT INTO blood_tests (id, user_id, tested_at, lab_name, source_type, overall_status) VALUES
    (1, 'user_001', '2025-12-10', '세브란스건강검진센터', 'manual',  'caution'),
    (2, 'user_001', '2026-03-15', '세브란스건강검진센터', 'pdf',     'watch'),
    (3, 'user_001', '2026-06-01', '강남건강검진클리닉',   'manual',  'watch'),
    (4, 'user_002', '2026-05-20', '서울아산병원',          'manual',  'watch');

-- ─── 혈액검사 항목별 수치 ────────────────────────────────────
-- user_001 / 2025-12-10 (1차)
INSERT INTO biomarker_results (blood_test_id,biomarker_code,display_name_ko,value,unit,ref_low,ref_high,need_score,trend_score,interpretation) VALUES
(1,'GLUCOSE_FASTING','공복혈당',    114.0,'mg/dL',70, 100,0.78, NULL,'공복혈당이 경계 수준입니다. 식습관 관리가 필요합니다'),
(1,'LDL',           'LDL 콜레스테롤',162.0,'mg/dL', 0, 130,0.96, NULL,'LDL이 정상 범위를 크게 초과합니다. 지질 관리가 시급합니다'),
(1,'HDL',           'HDL 콜레스테롤', 42.0,'mg/dL',40, 999,0.15, NULL,'HDL이 낮은 편입니다. 유산소 운동을 권장합니다'),
(1,'TG',            '중성지방',      185.0,'mg/dL', 0, 150,0.72, NULL,'중성지방이 기준을 초과합니다'),
(1,'AST',           'AST(간수치)',    38.0,'IU/L',  0,  40,0.12, NULL,'정상 범위 내입니다'),
(1,'ALT',           'ALT(간수치)',    32.0,'IU/L',  0,  40,0.10, NULL,'정상 범위 내입니다'),
(1,'VITD',          '비타민D',        12.5,'ng/mL', 30, 100,0.76, NULL,'비타민D가 부족합니다. 보충을 권장합니다'),
(1,'HB',            '헤모글로빈',     14.2,'g/dL',  13,  17,0.05, NULL,'정상 범위 내입니다');

-- user_001 / 2026-03-15 (2차)
INSERT INTO biomarker_results (blood_test_id,biomarker_code,display_name_ko,value,unit,ref_low,ref_high,need_score,trend_score,interpretation) VALUES
(2,'GLUCOSE_FASTING','공복혈당',    110.0,'mg/dL',70, 100,0.70, 0.08,'공복혈당이 경계 수준입니다. 소폭 개선되었습니다'),
(2,'LDL',           'LDL 콜레스테롤',155.0,'mg/dL', 0, 130,0.92, 0.06,'LDL이 여전히 높습니다. 지질 관리를 지속하세요'),
(2,'HDL',           'HDL 콜레스테롤', 45.0,'mg/dL',40, 999,0.12, 0.04,'HDL이 소폭 개선되었습니다'),
(2,'TG',            '중성지방',      170.0,'mg/dL', 0, 150,0.62, 0.10,'중성지방이 소폭 개선되었습니다'),
(2,'VITD',          '비타민D',        15.0,'ng/mL', 30, 100,0.70, 0.08,'비타민D가 여전히 부족합니다'),
(2,'HB',            '헤모글로빈',     14.5,'g/dL',  13,  17,0.04, 0.02,'정상 범위 내입니다');

-- user_001 / 2026-06-01 (3차 최신)
INSERT INTO biomarker_results (blood_test_id,biomarker_code,display_name_ko,value,unit,ref_low,ref_high,need_score,trend_score,interpretation) VALUES
(3,'GLUCOSE_FASTING','공복혈당',    108.0,'mg/dL',70, 100,0.64, 0.13,'공복혈당이 개선 중입니다. 식단 관리를 유지하세요'),
(3,'LDL',           'LDL 콜레스테롤',148.0,'mg/dL', 0, 130,0.87, 0.14,'LDL이 개선 중이나 여전히 관리가 필요합니다'),
(3,'HDL',           'HDL 콜레스테롤', 48.0,'mg/dL',40, 999,0.10, 0.05,'HDL이 정상 범위로 개선되었습니다'),
(3,'TG',            '중성지방',      158.0,'mg/dL', 0, 150,0.55, 0.11,'중성지방이 경계 수준입니다'),
(3,'AST',           'AST(간수치)',    35.0,'IU/L',  0,  40,0.08, 0.03,'정상 범위 내입니다'),
(3,'ALT',           'ALT(간수치)',    29.0,'IU/L',  0,  40,0.07, 0.02,'정상 범위 내입니다'),
(3,'VITD',          '비타민D',        18.0,'ng/mL', 30, 100,0.65, 0.15,'비타민D가 개선 중이나 아직 부족합니다'),
(3,'HB',            '헤모글로빈',     14.8,'g/dL',  13,  17,0.04, 0.01,'정상 범위 내입니다'),
(3,'CREATININE',    '크레아티닌',      0.9,'mg/dL', 0.6,  1.2,0.05, NULL,'정상 범위 내입니다');

-- user_002 / 2026-05-20
INSERT INTO biomarker_results (blood_test_id,biomarker_code,display_name_ko,value,unit,ref_low,ref_high,need_score,trend_score,interpretation) VALUES
(4,'HB',            '헤모글로빈',     10.8,'g/dL', 12,  16,0.55, NULL,'헤모글로빈이 낮아 빈혈 관리가 필요합니다'),
(4,'FERRITIN',      '페리틴',          8.0,'ng/mL', 12, 150,0.70, NULL,'페리틴이 낮아 철분 보충을 권장합니다'),
(4,'VITD',          '비타민D',          9.0,'ng/mL', 30, 100,0.82, NULL,'비타민D가 심각하게 부족합니다'),
(4,'GLUCOSE_FASTING','공복혈당',       88.0,'mg/dL', 70, 100,0.05, NULL,'정상 범위 내입니다'),
(4,'LDL',           'LDL 콜레스테롤', 102.0,'mg/dL',  0, 130,0.10, NULL,'정상 범위 내입니다');

-- ─── 생활 맥락 로그 ──────────────────────────────────────────
INSERT INTO daily_logs (user_id, log_date, sleep_hours, stress_level, schedule_type, skip_breakfast, late_meal_flag, alcohol_flag, exercise_min) VALUES
('user_001','2026-06-01', 5.5, 4, 'overtime',   1, 1, 0, 0),
('user_001','2026-05-31', 7.0, 3, 'normal',     0, 0, 1, 30),
('user_002','2026-06-01', 6.5, 3, 'normal',     1, 0, 0, 20);

-- ─── 영양제 마스터 ───────────────────────────────────────────
INSERT INTO supplement_master (ingredient_name, product_name, target_biomarker, dosage_unit, dose_per_serving, risk_tags, price_band, evidence_level, source_name) VALUES
('비타민D3',            NULL, 'VITD',            'IU',  2000, '[]',                              'low',     'A', '식약처공시'),
('오메가3 (EPA/DHA)',   NULL, 'LDL',             'mg',  1000, '["medication_interaction"]',       'mid',     'A', '식약처공시'),
('마그네슘',            NULL, 'GLUCOSE_FASTING', 'mg',   300, '["renal_caution"]',               'low',     'B', '식약처공시'),
('철분 (ferrous sulfate)',NULL,'HB',             'mg',    18, '[]',                              'low',     'A', '식약처공시'),
('철분 (ferrous sulfate)',NULL,'FERRITIN',        'mg',    18, '[]',                              'low',     'A', '식약처공시'),
('엽산',                NULL, 'HB',              'ug',   400, '[]',                              'low',     'A', '식약처공시'),
('비타민C',             NULL, 'HB',              'mg',   500, '[]',                              'low',     'A', '식약처공시'),
('코엔자임Q10',         NULL, 'LDL',             'mg',   100, '["medication_interaction"]',       'mid',     'B', '식약처공시'),
('베르베린',            NULL, 'GLUCOSE_FASTING', 'mg',   500, '["medication_interaction","renal_caution"]','mid','B','학술자료'),
('오메가3 저용량',       NULL, 'TG',              'mg',   500, '[]',                              'low',     'A', '식약처공시'),
('밀크씨슬',            NULL, 'ALT',             'mg',   150, '[]',                              'low',     'B', '학술자료'),
('밀크씨슬',            NULL, 'AST',             'mg',   150, '[]',                              'low',     'B', '학술자료'),
('NAC',                 NULL, 'ALT',             'mg',   600, '[]',                              'mid',     'B', '학술자료'),
('비타민B12',           NULL, 'HB',              'ug',  1000, '[]',                              'low',     'A', '식약처공시'),
('비타민B군',           NULL, 'HB',              'mg',     1, '[]',                              'low',     'A', '식약처공시'),
('칼슘',                NULL, 'HB',              'mg',   500, '["renal_caution"]',               'low',     'A', '식약처공시'),
('비타민K2',            NULL, 'VITD',            'ug',   100, '["medication_interaction"]',       'low',     'B', '학술자료'),
('유산균',              NULL, 'GLUCOSE_FASTING', 'CFU', 1000, '[]',                              'mid',     'B', '학술자료'),
('알파리포산',          NULL, 'GLUCOSE_FASTING', 'mg',   300, '["renal_caution"]',               'mid',     'B', '학술자료'),
('비타민E',             NULL, 'LDL',             'IU',   400, '["medication_interaction"]',       'low',     'B', '식약처공시'),
('셀레늄',              NULL, 'TSH',             'ug',   200, '[]',                              'low',     'B', '식약처공시'),
('커큐민',              NULL, 'ALT',             'mg',   500, '[]',                              'mid',     'B', '학술자료'),
('아쉬와간다',          NULL, 'GLUCOSE_FASTING', 'mg',   300, '[]',                              'mid',     'B', '학술자료'),
('홍국',                NULL, 'LDL',             'mg',   600, '["medication_interaction"]',       'mid',     'B', '학술자료'),
('나이아신',            NULL, 'TG',              'mg',   500, '[]',                              'low',     'A', '식약처공시'),
('나이아신',            NULL, 'LDL',             'mg',   500, '[]',                              'low',     'A', '식약처공시'),
('크롬',                NULL, 'GLUCOSE_FASTING', 'ug',   200, '[]',                              'low',     'B', '식약처공시'),
('글루코사민',          NULL, 'LDL',             'mg',  1500, '[]',                              'mid',     'B', '학술자료'),
('체리 엑스트랙트',     NULL, 'URIC',            'mg',   500, '[]',                              'mid',     'C', '학술자료'),
('L-카르니틴',          NULL, 'TG',              'mg',  1000, '[]',                              'mid',     'B', '학술자료'),
('루테인',              NULL, 'VITD',            'mg',    20, '[]',                              'low',     'B', '학술자료'),
('아이오딘',            NULL, 'TSH',             'ug',   150, '[]',                              'low',     'A', '식약처공시'),
('스피루리나',          NULL, 'HB',              'g',      3, '[]',                              'low',     'C', '학술자료'),
('오메가3 고용량',      NULL, 'TG',              'mg',  2000, '["medication_interaction"]',       'mid',     'A', '식약처공시');

-- ─── 식품 마스터 (샘플 20개) ─────────────────────────────────
INSERT INTO food_master (food_code, name_ko, serving_size_g, energy_kcal, protein_g, carb_g, fiber_g, sodium_mg, saturated_fat_g, iron_mg, vitamin_d_ug) VALUES
('F001','고등어구이',      100, 183, 20.2, 0,    0,   150, 3.1, 1.1, 8.9),
('F002','연어스테이크',    120, 218, 24.1, 0,    0,    80, 3.2, 0.4,16.0),
('F003','현미밥',          210, 313,  6.5,69.8,  2.8, 12,  0.4, 0.7, 0),
('F004','시금치나물',       70,  16,  2.0, 1.6,  1.5, 180, 0.1, 2.4, 0),
('F005','두부조림',        120,  86,  9.6, 2.4,  0.5, 320, 0.5, 1.8, 0),
('F006','아몬드 (한줌)',    30, 175,  6.0, 6.0,  3.5,   1, 1.3, 1.1, 0),
('F007','삶은 계란',        60,  91,  7.5, 0.5,  0,    71, 1.6, 1.2, 1.1),
('F008','그릭요거트',      150, 100, 10.0, 6.0,  0,    65, 0.6, 0,   0),
('F009','브로콜리볶음',     80,  28,  2.4, 3.5,  2.6,  30, 0.1, 0.7, 0),
('F010','렌틸콩수프',      200, 140,  9.0,24.0,  8.0, 280, 0.1, 3.3, 0),
('F011','잡곡밥',          210, 320,  7.0,68.0,  3.5,  10, 0.5, 1.0, 0),
('F012','닭가슴살',        100, 165, 31.0, 0,    0,    74, 1.0, 1.0, 0.1),
('F013','아보카도',         80, 128,  1.2, 7.0,  5.1,   7, 1.8, 0.5, 0),
('F014','바나나',           90,  79,  1.0,20.0,  1.8,   1, 0.1, 0.3, 0),
('F015','두유 무가당',     200,  63,  5.0, 5.0,  0.4, 160, 0.3, 1.2, 0),
('F016','편의점 닭가슴살 샐러드',150,180,18.0,8.0,3.0,420,1.2,1.0,0.1),
('F017','편의점 삶은달걀 2개',120,182,15.0,1.0,0,142,3.2,2.4,2.2),
('F018','외식 된장찌개 (한끼)',300,120,8.0,10.0,2.0,1200,0.8,2.0,0),
('F019','외식 비빔밥',     350, 480, 13.0,88.0,  4.0,1050, 1.5, 2.5, 0),
('F020','통밀식빵 2쪽',     60, 140,  5.5,27.0,  3.0, 240, 0.3, 1.5, 0),
('F021','방울토마토',       80,  14,  0.7, 2.8,  0.9,   5, 0.0, 0.3, 0),
('F022','블루베리',         80,  45,  0.6,11.0,  1.8,   1, 0.0, 0.2, 0),
('F023','오트밀',          40, 148,  5.4,26.0,  3.8,   2, 0.9, 1.7, 0),
('F024','호두 (한줌)',      30, 196,  4.6, 4.0,  2.0,   1, 1.7, 0.8, 0),
('F025','참치캔',          100, 128, 26.2, 0,    0,   270, 0.6, 1.3, 2.1),
('F026','병아리콩 조림',   150, 180, 10.0,28.0,  7.5, 210, 0.4, 2.8, 0),
('F027','케일 무침',        70,  30,  2.2, 3.8,  2.2,  60, 0.1, 1.1, 0),
('F028','고구마 (중간)',   100,  86,  1.6,20.0,  2.5,  57, 0.0, 0.7, 0),
('F029','멸치볶음',         20,  52,  8.8, 0.9,  0,   540, 0.3, 1.5, 0.5),
('F030','표고버섯볶음',     80,  35,  2.4, 5.8,  2.1,  95, 0.1, 0.4, 0.8),
('F031','굴 (생)',         100,  69,  8.0, 4.5,  0,   380, 0.7, 7.2, 0),
('F032','돼지고기 안심',   100, 143, 22.8, 0,    0,    50, 1.0, 1.0, 0.4),
('F033','콩나물국',        200,  20,  2.0, 2.0,  0.8, 450, 0.0, 0.5, 0),
('F034','아마씨 (분말)',    15,  72,  2.5, 3.8,  3.8,   3, 0.5, 0.8, 0),
('F035','퀴노아밥',        200, 280,  9.0,52.0,  5.0,   8, 0.6, 3.5, 0);

-- ─── 안전 룰 ─────────────────────────────────────────────────
INSERT INTO safety_rules (rule_code, condition_type, blocked_ingredient, risk_threshold, rule_desc, is_active) VALUES
('SR_001','신장질환',  '마그네슘',           0.5, '신장질환 사용자에게 마그네슘 고용량 보충제 추천 제한',    1),
('SR_002','신장질환',  '베르베린',           0.5, '신장질환 사용자에게 베르베린 추천 제한',                  1),
('SR_003','항응고제복용','오메가3 (EPA/DHA)', 0.0, '항응고제(와파린 등) 복용자에게 고용량 오메가3 추천 제한', 1),
('SR_004','항응고제복용','코엔자임Q10',       0.0, '항응고제 복용자에게 코엔자임Q10 추천 주의',              1),
('SR_005','임신수유',  NULL,                 0.0, '임신·수유 중 고용량 영양제 전체 추천 제한 및 상담 권고',  1),
('SR_006','간질환',    NULL,                 0.7, '간수치(ALT/AST) 위험 수준 시 모든 영양제 추천 제한',     1);

-- ─── 추천 세션 & 추천 아이템 샘플 ───────────────────────────
INSERT INTO recommendation_sessions (id, user_id, blood_test_id, biomarker_snapshot_json, safety_flags, algorithm_version)
VALUES (1, 'user_001', 3,
    '{"LDL":{"value":148.0,"need_score":0.87},"VITD":{"value":18.0,"need_score":0.65},"GLUCOSE_FASTING":{"value":108.0,"need_score":0.64}}',
    '[]',
    'v1.0');

INSERT INTO recommended_items (session_id, item_type, item_id, biomarker_fit, nutrition_fit, context_score, preference_fit, adherence_fit, safety_pass, final_score, recommendation_reason)
VALUES
(1,'supplement',2, 0.88,0.75,0.70,0.80,0.65, 1, 0.79, 'LDL 콜레스테롤(148mg/dL)이 기준을 초과하여 오메가3(EPA/DHA) 보충을 권장합니다'),
(1,'supplement',1, 0.82,0.68,0.65,0.85,0.70, 1, 0.74, '비타민D(18ng/mL)가 부족하여 비타민D3 2000IU 보충을 권장합니다'),
(1,'food',      1, 0.85,0.90,0.72,0.75,0.80, 1, 0.82, 'LDL 관리에 오메가3가 풍부한 고등어구이를 권장합니다'),
(1,'food',      2, 0.80,0.88,0.68,0.70,0.75, 1, 0.78, '비타민D와 오메가3가 풍부한 연어스테이크를 권장합니다'),
(1,'routine',   NULL,0.70,0.65,0.75,0.80,0.60,1, 0.70, '혈당 관리를 위해 아침 결식을 줄이고 야식 빈도를 낮추는 생활 루틴을 권장합니다');

