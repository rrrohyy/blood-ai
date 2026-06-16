"""
blood.ai | Recommendation Engine
==================================
혈액검사 수치 + 생활 맥락을 기반으로 영양제·식품·생활루틴을
추천하는 5-Layer Hybrid Recommendation System.

Layers:
  1. Safety Guardrail (safety_filter.py)
  2. Biomarker Scoring
  3. Content-based Matching (코사인 유사도)
  4. Contextual Scoring (간단 가중치 모델 - LightGBM 대체)
  5. Explainable Ranker + MMR 다양성 보정

KAIST Business Analytics and Data Mining
"""

import sqlite3
import json
import math
from dataclasses import dataclass, field
from typing import Optional

from safety_filter import SafetyFilter, SafetyResult


# ─── 데이터 클래스 ────────────────────────────────────────────
@dataclass
class ContextVector:
    """사용자 오늘의 생활 맥락 (16차원)"""
    # 혈액검사 기반 관리 필요도
    glucose_need: float = 0.0
    lipid_need:   float = 0.0
    liver_need:   float = 0.0
    iron_need:    float = 0.0
    vitd_need:    float = 0.0
    # 안전 플래그
    renal_caution:    int = 0   # 0/1
    medication_risk:  int = 0   # 0/1
    duplicate_score:  float = 0.0
    # 생활 맥락
    sleep_debt:       float = 0.0   # max(0, 8 - sleep_hours)
    stress_norm:      float = 0.0   # stress_level / 5
    post_exercise:    int   = 0     # 0/1 (운동 20분 이상)
    skip_breakfast:   float = 0.0   # 0~1
    late_meal_rate:   float = 0.0   # 0~1
    # 선호·예산
    budget_tier:      int   = 1     # 1=low, 2=mid, 3=high, 4=premium
    preference_score: float = 0.8
    adherence_prob:   float = 0.7


@dataclass
class RecommendItem:
    item_type:   str       # supplement / food / routine / consult_alert
    item_id:     Optional[int]
    name:        str
    biomarker_fit:  float = 0.0
    nutrition_fit:  float = 0.0
    context_score:  float = 0.0
    preference_fit: float = 0.0
    adherence_fit:  float = 0.0
    safety_pass:    bool  = True
    final_score:    float = 0.0
    reason:         str   = ""


# ─── 추천 엔진 ────────────────────────────────────────────────
class BloodAIRecommender:

    WEIGHTS = dict(
        biomarker=0.35,
        nutrition=0.25,
        context=0.20,
        preference=0.10,
        adherence=0.10,
    )

    def __init__(self, db_path: str = "blood_ai.db"):
        self.db_path = db_path
        self.safety  = SafetyFilter(db_path=db_path)

    def _conn(self):
        return sqlite3.connect(self.db_path)

    # ── Layer 2: Biomarker Scoring ────────────────────────────
    def _biomarker_scores(self, user_id: str) -> dict:
        """최신 혈액검사에서 관리 영역별 need_score 반환"""
        conn = self._conn()
        cur = conn.execute("""
            SELECT br.biomarker_code, br.need_score
            FROM   biomarker_results br
            JOIN   blood_tests bt ON br.blood_test_id = bt.id
            WHERE  bt.user_id   = ?
              AND  bt.tested_at = (
                       SELECT MAX(tested_at) FROM blood_tests WHERE user_id = ?
                   )
        """, (user_id, user_id))
        scores = {row[0]: row[1] for row in cur.fetchall()}
        conn.close()

        # 관리 영역 집계
        return {
            "glucose": scores.get("GLUCOSE_FASTING", 0) * 0.6 + scores.get("HBA1C", 0) * 0.4,
            "lipid":   scores.get("LDL", 0) * 0.5 + scores.get("TG", 0) * 0.3 + max(0, 0.5 - scores.get("HDL", 0.5)) * 0.2,
            "liver":   scores.get("ALT", 0) * 0.4 + scores.get("AST", 0) * 0.4 + scores.get("GGT", 0) * 0.2,
            "iron":    scores.get("HB", 0) * 0.5 + scores.get("FERRITIN", 0) * 0.5,
            "vitd":    scores.get("VITD", 0),
            "renal":   1 if scores.get("CREATININE", 0) >= 0.7 or scores.get("EGFR", 1.0) <= 0.5 else 0,
        }

    # ── Layer 3: Content-based Matching ──────────────────────
    @staticmethod
    def _cosine(a: list, b: list) -> float:
        dot   = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x**2 for x in a))
        norm_b = math.sqrt(sum(x**2 for x in b))
        return dot / (norm_a * norm_b + 1e-9)

    def _supplement_biomarker_fit(self, ingredient: str, bio_scores: dict) -> float:
        """성분-지표 매핑 테이블 기반 적합도"""
        conn = self._conn()
        cur = conn.execute(
            "SELECT target_biomarker FROM supplement_master WHERE ingredient_name = ?",
            (ingredient,)
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return 0.0
        code = row[0]
        # 코드 → 관리 영역 매핑
        mapping = {
            "VITD": "vitd", "LDL": "lipid", "TG": "lipid",
            "GLUCOSE_FASTING": "glucose", "HBA1C": "glucose",
            "HB": "iron", "FERRITIN": "iron",
            "ALT": "liver", "AST": "liver",
        }
        area = mapping.get(code, "")
        return bio_scores.get(area, 0.0)

    def _food_nutrition_fit(self, food_id: int, bio_scores: dict) -> float:
        """식품 영양성분 벡터와 건강 벡터 코사인 유사도"""
        conn = self._conn()
        cur = conn.execute(
            "SELECT fiber_g, iron_mg, vitamin_d_ug, saturated_fat_g, sodium_mg FROM food_master WHERE id = ?",
            (food_id,)
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return 0.0

        fiber_g, iron_mg, vitd_ug, sat_fat_g, sodium_mg = row
        # 영양소 정규화 벡터 (0~1)
        food_vec = [
            min(fiber_g / 5.0, 1.0),         # 식이섬유 (혈당·지질)
            min(iron_mg / 3.0, 1.0),          # 철분
            min(vitd_ug / 10.0, 1.0),         # 비타민D
            max(0, 1 - sat_fat_g / 5.0),      # 포화지방 낮을수록 좋음
            max(0, 1 - sodium_mg / 800.0),    # 나트륨 낮을수록 좋음
        ]
        health_vec = [
            max(bio_scores["glucose"], bio_scores["lipid"]),
            bio_scores["iron"],
            bio_scores["vitd"],
            bio_scores["lipid"],
            bio_scores["lipid"] * 0.5 + bio_scores["liver"] * 0.5,
        ]
        return self._cosine(food_vec, health_vec)

    # ── Layer 4: Contextual Scoring ───────────────────────────
    @staticmethod
    def _context_score(item_type: str, ctx: ContextVector) -> float:
        """생활 맥락 기반 선택 확률 추정 (LightGBM 대체 간단 모델)"""
        if item_type == "supplement":
            score = 0.5
            score += ctx.sleep_debt    * 0.05   # 수면 부족 → 보충제 관심↑
            score += ctx.stress_norm   * 0.05
            score -= ctx.duplicate_score * 0.10 # 중복 → 선택 확률↓
            return min(max(score, 0.0), 1.0)

        if item_type == "food":
            score = 0.5
            score -= ctx.late_meal_rate  * 0.10  # 야식 빈도↑ → 건강식단 선택↓
            score += (1 - ctx.skip_breakfast) * 0.05
            return min(max(score, 0.0), 1.0)

        if item_type == "routine":
            score = 0.4
            score += ctx.stress_norm  * 0.15   # 스트레스↑ → 루틴 제안 수용↑
            score += ctx.sleep_debt   * 0.10
            return min(max(score, 0.0), 1.0)

        return 0.5

    # ── Layer 5: Final Score + MMR ────────────────────────────
    @staticmethod
    def _final_score(item: RecommendItem) -> float:
        w = BloodAIRecommender.WEIGHTS
        return (
            w["biomarker"]  * item.biomarker_fit +
            w["nutrition"]  * item.nutrition_fit +
            w["context"]    * item.context_score +
            w["preference"] * item.preference_fit +
            w["adherence"]  * item.adherence_fit
        )

    @staticmethod
    def _mmr_rerank(items: list, top_k: int = 5, lambda_: float = 0.6) -> list:
        """
        Maximal Marginal Relevance: 동일 유형 독점을 방지하여 다양성 확보.
        lambda_=1이면 순수 relevance 정렬, 0이면 순수 다양성.
        """
        if not items:
            return []
        selected = [items[0]]
        remaining = items[1:]
        while len(selected) < top_k and remaining:
            best, best_score = None, -1.0
            for cand in remaining:
                # 유사도: 같은 item_type이면 패널티
                sim = max(1.0 if cand.item_type == s.item_type else 0.0
                          for s in selected)
                score = lambda_ * cand.final_score - (1 - lambda_) * sim
                if score > best_score:
                    best, best_score = cand, score
            if best:
                selected.append(best)
                remaining.remove(best)
        return selected

    # ── 메인 추천 API ─────────────────────────────────────────
    def recommend(
        self,
        user_id: str,
        ctx: ContextVector,
        top_k: int = 5,
    ) -> list[RecommendItem]:
        """
        사용자 ID와 생활 맥락을 입력받아 Top-K 추천 결과를 반환한다.
        """
        bio_scores = self._biomarker_scores(user_id)
        conn = self._conn()
        candidates = []

        # ── 영양제 후보 ──────────────────────────────────────
        supp_rows = conn.execute(
            "SELECT id, ingredient_name FROM supplement_master"
        ).fetchall()
        for sid, name in supp_rows:
            safety = self.safety.check(user_id, name)
            if not safety.is_safe:
                continue  # Layer 1: 안전 필터
            bio_fit  = self._supplement_biomarker_fit(name, bio_scores)
            c_score  = self._context_score("supplement", ctx)
            item = RecommendItem(
                item_type="supplement", item_id=sid, name=name,
                biomarker_fit=bio_fit, nutrition_fit=bio_fit * 0.8,
                context_score=c_score, preference_fit=ctx.preference_score,
                adherence_fit=ctx.adherence_prob, safety_pass=True,
            )
            item.final_score = self._final_score(item)
            item.reason = self._explain_supplement(name, bio_scores)
            candidates.append(item)

        # ── 식품 후보 ─────────────────────────────────────────
        food_rows = conn.execute(
            "SELECT id, name_ko FROM food_master"
        ).fetchall()
        for fid, fname in food_rows:
            nut_fit  = self._food_nutrition_fit(fid, bio_scores)
            if nut_fit < 0.3:          # 낮은 적합도 사전 필터
                continue
            c_score  = self._context_score("food", ctx)
            bio_fit  = nut_fit * 0.9
            item = RecommendItem(
                item_type="food", item_id=fid, name=fname,
                biomarker_fit=bio_fit, nutrition_fit=nut_fit,
                context_score=c_score, preference_fit=ctx.preference_score,
                adherence_fit=ctx.adherence_prob, safety_pass=True,
            )
            item.final_score = self._final_score(item)
            item.reason = self._explain_food(fname, bio_scores)
            candidates.append(item)

        # ── 생활루틴 후보 ─────────────────────────────────────
        if bio_scores["glucose"] >= 0.5 or ctx.late_meal_rate >= 0.5:
            r = RecommendItem(
                item_type="routine", item_id=None,
                name="야식 제한 & 아침 식사 루틴",
                biomarker_fit=bio_scores["glucose"],
                nutrition_fit=0.5, context_score=self._context_score("routine", ctx),
                preference_fit=0.7, adherence_fit=0.6, safety_pass=True,
            )
            r.final_score = self._final_score(r)
            r.reason = "혈당 관리를 위해 야식을 줄이고 아침 식사를 규칙적으로 하는 루틴을 권장합니다."
            candidates.append(r)

        if ctx.sleep_debt >= 1.5:
            r = RecommendItem(
                item_type="routine", item_id=None, name="수면 개선 루틴",
                biomarker_fit=0.4, nutrition_fit=0.3,
                context_score=self._context_score("routine", ctx),
                preference_fit=0.75, adherence_fit=0.65, safety_pass=True,
            )
            r.final_score = self._final_score(r)
            r.reason = f"수면 부족({8 - ctx.sleep_debt:.1f}시간)으로 회복 루틴을 권장합니다. 취침 1시간 전 스크린을 줄이세요."
            candidates.append(r)

        conn.close()

        # 최종 정렬 + MMR 다양성 보정
        candidates.sort(key=lambda x: x.final_score, reverse=True)
        return self._mmr_rerank(candidates, top_k=top_k)

    # ── 추천 사유 생성 ────────────────────────────────────────
    @staticmethod
    def _explain_supplement(name: str, bio: dict) -> str:
        mapping = {
            "비타민D3": f"비타민D가 부족하여 비타민D3 보충을 권장합니다.",
            "오메가3 (EPA/DHA)": f"LDL 콜레스테롤 관리를 위해 오메가3(EPA/DHA) 보충을 권장합니다.",
            "마그네슘": "혈당 조절을 보조하는 마그네슘 보충을 권장합니다.",
            "철분 (ferrous sulfate)": "헤모글로빈/페리틴이 낮아 철분 보충을 권장합니다.",
            "엽산": "철분 흡수를 돕는 엽산 보충을 권장합니다.",
            "비타민C": "철분 흡수율 향상을 위해 비타민C를 함께 복용하는 것을 권장합니다.",
        }
        return mapping.get(name, f"{name} 보충을 권장합니다.")

    @staticmethod
    def _explain_food(fname: str, bio: dict) -> str:
        return f"오늘 관리 지표 개선에 도움이 되는 {fname}을(를) 권장합니다."


# ─── CLI 실행 예시 ────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else "blood_ai.db"

    rec = BloodAIRecommender(db_path=db)

    # user_001 오늘 맥락: 야근, 수면 5.5h, 스트레스 4, 아침 결식
    ctx = ContextVector(
        glucose_need=0.64, lipid_need=0.87, vitd_need=0.65,
        sleep_debt=2.5, stress_norm=0.8,
        skip_breakfast=1.0, late_meal_rate=0.6,
        budget_tier=2, preference_score=0.8, adherence_prob=0.7,
    )

    print("=" * 60)
    print("blood.ai Recommendation Engine Demo")
    print("사용자: user_001  |  알고리즘: v1.0 Hybrid")
    print("=" * 60)

    results = rec.recommend("user_001", ctx, top_k=5)
    for i, item in enumerate(results, 1):
        icon = {"supplement": "💊", "food": "🥗", "routine": "🏃"}.get(item.item_type, "📋")
        print(f"\n[{i}] {icon} {item.name}  (score={item.final_score:.3f})")
        print(f"     biomarker_fit={item.biomarker_fit:.2f}  context_score={item.context_score:.2f}")
        print(f"     → {item.reason}")
