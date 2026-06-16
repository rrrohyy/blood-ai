"""
blood.ai | Safety Filter
========================
복약 충돌, 위험 수치, 성분 중복, 임신·수유 등을 감지하여
추천 가능 여부와 사유를 반환하는 Rule-based Safety Guardrail.

KAIST Business Analytics and Data Mining
"""

import sqlite3
import json
from dataclasses import dataclass, field
from typing import Optional

# ─── 데이터 클래스 ─────────────────────────────────────────────
@dataclass
class SafetyResult:
    is_safe: bool                    # True: 추천 가능, False: 추천 제한
    flags: list[str] = field(default_factory=list)   # 적용된 제한 사유 코드
    messages: list[str] = field(default_factory=list) # 사용자용 안내 메시지
    consult_required: bool = False   # True: 의료진 상담 권고


# ─── 위험 수치 기준 상수 ──────────────────────────────────────
DANGER_THRESHOLDS = {
    "GLUCOSE_FASTING": {"high": 126.0,  "msg": "공복혈당이 당뇨 진단 기준(126mg/dL)에 해당합니다. 의료진 상담이 필요합니다."},
    "LDL":             {"high": 190.0,  "msg": "LDL이 매우 높습니다(190mg/dL 이상). 의료진 상담이 필요합니다."},
    "ALT":             {"high": 120.0,  "msg": "간수치(ALT)가 정상의 3배 이상입니다. 영양제 추천을 제한하고 의료진 상담을 권고합니다."},
    "AST":             {"high": 120.0,  "msg": "간수치(AST)가 정상의 3배 이상입니다. 의료진 상담을 권고합니다."},
    "CREATININE":      {"high": 1.5,    "msg": "크레아티닌이 높습니다. 신장 기능 이상 가능성으로 고용량 영양제를 제한합니다."},
    "HB":              {"low":  7.0,    "msg": "헤모글로빈이 심각하게 낮습니다(7g/dL 미만). 의료진 상담이 필요합니다."},
    "VITD":            {"low":  5.0,    "msg": "비타민D가 매우 낮습니다. 고용량 보충 전 의료진 상담을 권고합니다."},
}

# 복약 충돌 룰: {복용 조건: [충돌 성분 목록]}
MEDICATION_CONFLICTS = {
    "항응고제복용": ["오메가3 (EPA/DHA)", "코엔자임Q10", "비타민E"],
    "당뇨":        ["베르베린"],           # 저혈당 위험 중복
    "고혈압":      [],                     # blood.ai는 주의만 안내
    "신장질환":    ["마그네슘", "베르베린", "단백질파우더"],
    "간질환":      [],                     # 간수치 주의 시 별도 처리
    "임신수유":    ["고용량비타민A", "베르베린"],
}

# 임신·수유 시 전면 제한 성분 패턴
PREGNANCY_BLOCKED = ["고용량비타민A", "베르베린"]


class SafetyFilter:
    """
    혈액검사 수치와 사용자 복약/기저질환 정보를 바탕으로
    특정 영양제 성분의 추천 안전성을 판단한다.
    """

    def __init__(self, db_path: str = "blood_ai.db"):
        self.db_path = db_path

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    # ── 공개 API ──────────────────────────────────────────────

    def check(
        self,
        user_id: str,
        ingredient_name: str,
        latest_biomarkers: Optional[dict] = None,
    ) -> SafetyResult:
        """
        단일 성분에 대해 해당 사용자의 안전성을 검사한다.

        Parameters
        ----------
        user_id           : 사용자 ID
        ingredient_name   : 검사할 영양제 성분명
        latest_biomarkers : {biomarker_code: value} 형태의 최신 수치 dict.
                            None이면 DB에서 자동 조회한다.

        Returns
        -------
        SafetyResult
        """
        result = SafetyResult(is_safe=True)

        # 1. 혈액검사 수치 조회
        if latest_biomarkers is None:
            latest_biomarkers = self._fetch_latest_biomarkers(user_id)

        # 2. 위험 수치 감지
        self._check_danger_thresholds(latest_biomarkers, result)

        # 3. 복약·기저질환 충돌 감지
        user_conditions = self._fetch_user_conditions(user_id)
        self._check_medication_conflicts(ingredient_name, user_conditions, result)

        # 4. 임신·수유 감지
        self._check_pregnancy(ingredient_name, user_conditions, result)

        # 5. DB safety_rules 테이블 확인
        self._check_db_safety_rules(user_id, ingredient_name, user_conditions, result)

        # 6. 성분 중복 감지
        self._check_duplicate_supplement(user_id, ingredient_name, result)

        return result

    def check_batch(
        self,
        user_id: str,
        ingredient_names: list[str],
    ) -> dict[str, SafetyResult]:
        """여러 성분을 한 번에 검사한다."""
        biomarkers = self._fetch_latest_biomarkers(user_id)
        return {
            name: self.check(user_id, name, latest_biomarkers=biomarkers)
            for name in ingredient_names
        }

    def get_consult_alert(self, user_id: str) -> Optional[str]:
        """
        위험 수치가 존재하면 최상단 상담 권고 메시지를 반환한다.
        안전하면 None 반환.
        """
        biomarkers = self._fetch_latest_biomarkers(user_id)
        messages = []
        for code, thresholds in DANGER_THRESHOLDS.items():
            if code not in biomarkers:
                continue
            value = biomarkers[code]
            if "high" in thresholds and value >= thresholds["high"]:
                messages.append(thresholds["msg"])
            if "low" in thresholds and value <= thresholds["low"]:
                messages.append(thresholds["msg"])
        return " / ".join(messages) if messages else None

    # ── 내부 메서드 ───────────────────────────────────────────

    def _fetch_latest_biomarkers(self, user_id: str) -> dict:
        conn = self._get_conn()
        cur = conn.execute("""
            SELECT br.biomarker_code, br.value
            FROM   biomarker_results br
            JOIN   blood_tests bt ON br.blood_test_id = bt.id
            WHERE  bt.user_id   = ?
              AND  bt.tested_at = (
                       SELECT MAX(tested_at)
                       FROM   blood_tests
                       WHERE  user_id = ?
                   )
        """, (user_id, user_id))
        rows = cur.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

    def _fetch_user_conditions(self, user_id: str) -> list[str]:
        conn = self._get_conn()
        cur = conn.execute("""
            SELECT condition_type
            FROM   user_conditions
            WHERE  user_id  = ?
              AND  is_active = 1
        """, (user_id,))
        rows = cur.fetchall()
        conn.close()
        return [row[0] for row in rows]

    def _check_danger_thresholds(self, biomarkers: dict, result: SafetyResult):
        for code, thresholds in DANGER_THRESHOLDS.items():
            if code not in biomarkers:
                continue
            value = biomarkers[code]
            if "high" in thresholds and value >= thresholds["high"]:
                result.is_safe = False
                result.flags.append(f"DANGER_HIGH_{code}")
                result.messages.append(thresholds["msg"])
                result.consult_required = True
            if "low" in thresholds and value <= thresholds["low"]:
                result.is_safe = False
                result.flags.append(f"DANGER_LOW_{code}")
                result.messages.append(thresholds["msg"])
                result.consult_required = True

    def _check_medication_conflicts(
        self, ingredient: str, conditions: list[str], result: SafetyResult
    ):
        for condition in conditions:
            blocked = MEDICATION_CONFLICTS.get(condition, [])
            if ingredient in blocked:
                result.is_safe = False
                result.flags.append(f"MED_CONFLICT_{condition.upper()}")
                result.messages.append(
                    f"{condition} 복용/질환으로 인해 {ingredient} 추천이 제한됩니다. "
                    "의료진 상담 후 복용하세요."
                )

    def _check_pregnancy(
        self, ingredient: str, conditions: list[str], result: SafetyResult
    ):
        if "임신수유" in conditions and ingredient in PREGNANCY_BLOCKED:
            result.is_safe = False
            result.flags.append("PREGNANCY_BLOCK")
            result.messages.append(
                f"임신·수유 중에는 {ingredient} 복용 전 반드시 의료진과 상담하세요."
            )
            result.consult_required = True

    def _check_db_safety_rules(
        self, user_id: str, ingredient: str, conditions: list[str], result: SafetyResult
    ):
        if not conditions:
            return
        conn = self._get_conn()
        placeholders = ",".join("?" * len(conditions))
        cur = conn.execute(f"""
            SELECT sr.rule_code, sr.rule_desc
            FROM   safety_rules sr
            WHERE  sr.condition_type IN ({placeholders})
              AND  sr.blocked_ingredient = ?
              AND  sr.is_active = 1
        """, (*conditions, ingredient))
        rows = cur.fetchall()
        conn.close()
        for rule_code, rule_desc in rows:
            result.is_safe = False
            result.flags.append(rule_code)
            result.messages.append(rule_desc)

    def _check_duplicate_supplement(
        self, user_id: str, ingredient: str, result: SafetyResult
    ):
        """현재 사용자가 이미 복용 중인 동일 성분 감지 (간단 구현)"""
        # 실제 서비스에서는 user_supplement_log 테이블을 별도 관리한다
        # 데모에서는 패스
        pass


# ─── CLI 실행 예시 ────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else "blood_ai.db"
    sf = SafetyFilter(db_path=db)

    print("=" * 60)
    print("blood.ai Safety Filter Demo")
    print("=" * 60)

    # user_001: 고혈압약 복용 중
    test_cases = [
        ("user_001", "오메가3 (EPA/DHA)"),
        ("user_001", "비타민D3"),
        ("user_001", "베르베린"),
        ("user_001", "마그네슘"),
        ("user_002", "철분 (ferrous sulfate)"),
        ("user_002", "비타민D3"),
    ]

    for user_id, ingredient in test_cases:
        res = sf.check(user_id, ingredient)
        status = "✅ 안전" if res.is_safe else "❌ 제한"
        print(f"\n[{user_id}] {ingredient:<25} {status}")
        if res.flags:
            print(f"  플래그: {', '.join(res.flags)}")
        for msg in res.messages:
            print(f"  → {msg}")

    print("\n" + "=" * 60)
    print("상담 권고 알림 체크")
    for uid in ["user_001", "user_002"]:
        alert = sf.get_consult_alert(uid)
        if alert:
            print(f"[{uid}] ⚠️  {alert}")
        else:
            print(f"[{uid}] ✅ 위험 수치 없음")
