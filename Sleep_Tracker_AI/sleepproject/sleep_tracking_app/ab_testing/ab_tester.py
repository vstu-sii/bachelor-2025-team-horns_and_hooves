import os
import json
import re
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from sleep_tracking_app.models import UserData, SleepStatistics, SleepRecord
from sleep_tracking_app.prompts.prompts_templates import create_sleep_analysis_prompt
from prompts.prompts_templates import get_system_prompt as get_baseline_system_prompt
from sleep_tracking_app.prompts.baseline import call_gemini
from sleep_tracking_app.rag.rag_service import RagService
from sleep_tracking_app.ab_testing.judge import SleepLLMJudge
from scenarios import get_test_scenarios_from_db  


# --- ОПРЕДЕЛЕНИЕ ВАРИАНТОВ ПРОМПТОВ ---

SYSTEM_PROMPT_A = get_baseline_system_prompt()

SYSTEM_PROMPT_B = (
    "Ты — опытный врач-сомнолог. Твоя задача — дать персональную, "
    "конкретную и практическую рекомендацию по улучшению сна на основе присланных показателей.\n"
    "Требования к ответу:\n"
    "1) Кратко опиши основную проблему сна пользователя и на какие показатели ты опираешься.\n"
    "2) Дай 3–5 чётких шагов, что пользователь может сделать уже сегодня/завтра.\n"
    "3) Для каждого шага коротко объясни, почему он важен именно при таких данных сна.\n"
    "4) Избегай медицинских назначений и упоминаний лекарств. При серьёзных проблемах мягко рекомендуй обратиться к врачу.\n"
    "5) Пиши простыми, понятными фразами без сложной терминологии. Не используй Markdown."
)

PROMPT_VARIANTS = {
    "A": SYSTEM_PROMPT_A,
    "B": SYSTEM_PROMPT_B,
}

# --- ВСПОМОГАТЕЛЬНЫЕ МЕТРИКИ ---

def simple_quality_metrics(text: str) -> Dict[str, Any]:
    """Простые авто‑метрики для A/B."""
    words = text.split()
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    w = len(words)
    s = max(1, len(sentences))

    readability = min(100.0, (w / s) * 5.0)
    recommendation_density = (
        sum(1 for w_ in words if any(k in w_.lower() for k in ["рекоменд", "совет", "стоит", "попробуй", "избегайте"]))
        / w * 1000
    ) if w else 0.0
    structure_score = 1.0 if s >= 3 else 0.5
    specificity = min(100.0, (len([w_ for w_ in words if any(ch.isdigit() for ch in w_)]) / w * 500)) if w else 0.0

    return {
        "word_count": w,
        "sentence_count": s,
        "readability_score": round(readability, 2),
        "recommendation_density": round(recommendation_density, 2),
        "structure_score": structure_score,
        "specificity_score": round(specificity, 2),
    }


def compose_overall_score(auto: Dict[str, Any], judge_scores: Optional[Dict[str, int]]) -> float:
    """
    Итоговый скор A/B:
    - авто‑метрики (0–100)
    - оценки судьи (1–10 → масштабируем до 0–100)
    """
    weights = {
        "readability_score": 0.15,
        "recommendation_density": 0.2,
        "structure_score": 0.1,
        "specificity_score": 0.15,
        "data_coverage": 0.1,
        "problem_accuracy": 0.1,
        "actionability": 0.1,
        "safety": 0.1,
    }

    total = 0.0
    wsum = 0.0

    for k, w in weights.items():
        if k in auto:
            val = auto[k]  # 0–100
        elif judge_scores and k in judge_scores:
            val = judge_scores[k] * 10  # 1–10 → 10–100
        else:
            continue

        total += val * w
        wsum += w

    return round(total / wsum, 2) if wsum > 0 else 0.0


# --- СТРУКТУРА ДЛЯ РЕЗУЛЬТАТОВ ---

@dataclass
class ABTestResult:
    test_id: str
    description: str
    variant: str
    system_prompt_preview: str
    response: str
    auto_metrics: Dict[str, Any]
    judge_scores: Optional[Dict[str, Any]]
    judge_critical_issues: Optional[List[str]]
    overall_score: float
    gemini_latency: float
    rag_latency: float


# --- ОСНОВНОЙ КЛАСС ДЛЯ A/B-ТЕСТИРОВАНИЯ ---

class SleepABOfflineTester:
    def __init__(self, variants: List[str] = None, max_tests: int = 5):
        self.variants = variants or ["A", "B"]
        self.max_tests = max_tests
        self.judge = SleepLLMJudge()
        self.rag_service = RagService()
        self.results: List[ABTestResult] = []

        self.test_cases = get_test_scenarios_from_db()[:self.max_tests]

    def _run_single(self, variant: str, case: Dict[str, Any]) -> Optional[ABTestResult]:
        user_data: UserData = case["user_data"]
        sleep_stats: SleepStatistics = case["sleep_stats"]
        sleep_record: SleepRecord = case["sleep_record"]

        system_prompt = PROMPT_VARIANTS[variant]
        
        user_prompt = create_sleep_analysis_prompt(
            user_data,
            [sleep_stats],
            [sleep_record],
        )
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # 2) Gemini → базовая рекомендация
        start_g = time.time()
        gemini_resp = call_gemini(full_prompt)
        gemini_lat = round(time.time() - start_g, 3)

        if not gemini_resp:
            print(f"[{variant}] Gemini не вернул ответ, пропускаем кейс {case['id']}")
            return None

        # 3) RAG+Mistral → улучшение
        user_ctx = {
            "age_months": float(user_data.get_age_months()),
            "gender": user_data.get_gender(),
            "weight": float(user_data.weight),
            "height": float(user_data.height),
        }

        start_r = time.time()
        rag_result = self.rag_service.enhance(gemini_resp, user_ctx)
        rag_lat = round(time.time() - start_r, 3)

        final_text = rag_result.get("enhanced") or gemini_resp

        # 4) авто‑метрики
        auto = simple_quality_metrics(final_text)

        # 5) судья
        judge_result = self.judge.evaluate(user_data, sleep_stats, sleep_record, final_text)
        judge_scores = judge_result["scores"] if judge_result and "scores" in judge_result else None
        critical_issues = judge_result.get("critical_issues") if judge_result else None

        # 6) итоговый скор
        overall = compose_overall_score(auto, judge_scores)

        return ABTestResult(
            test_id=str(case["id"]),
            description=case.get("description", ""),
            variant=variant,
            system_prompt_preview=system_prompt[:200],
            response=final_text,
            auto_metrics=auto,
            judge_scores=judge_scores,
            judge_critical_issues=critical_issues,
            overall_score=overall,
            gemini_latency=gemini_lat,
            rag_latency=rag_lat,
        )

    def run(self):
        print("Старт offline A/B‑тестирования промптов (без интеграции в прод)…")
        for case in self.test_cases:
            print(f"\n Тестовый сценарий: {case['id']} — {case.get('description', '')}")
            for variant in self.variants:
                print(f"    Вариант {variant}…", end="", flush=True)
                res = self._run_single(variant, case)
                if res:
                    self.results.append(res)
                    avg_judge = (
                        sum(res.judge_scores.values()) / len(res.judge_scores)
                        if res.judge_scores
                        else None
                    )
                    print(
                        f" готово | overall={res.overall_score} "
                        f"| judge_avg={avg_judge:.1f} "
                        f"| len={res.auto_metrics['word_count']} "
                        f"| gemini={res.gemini_latency}s, rag={res.rag_latency}s"
                        if avg_judge is not None
                        else f" готово | overall={res.overall_score} "
                             f"| len={res.auto_metrics['word_count']} "
                             f"| gemini={res.gemini_latency}s, rag={res.rag_latency}s"
                    )
                else:
                    print(" пропущено (ошибка)")

    def summarize(self) -> Dict[str, Any]:
        if not self.results:
            return {}

        summary: Dict[str, Any] = {"variants": {}}
        for v in self.variants:
            v_res = [r for r in self.results if r.variant == v]
            if not v_res:
                continue
            overall = [r.overall_score for r in v_res]
            judge_safety = [
                r.judge_scores["safety"]
                for r in v_res
                if r.judge_scores and "safety" in r.judge_scores
            ]
            summary["variants"][v] = {
                "count": len(v_res),
                "avg_overall_score": round(sum(overall) / len(overall), 2),
                "avg_gemini_latency": round(sum(r.gemini_latency for r in v_res) / len(v_res), 3),
                "avg_rag_latency": round(sum(r.rag_latency for r in v_res) / len(v_res), 3),
                "avg_judge_safety": round(sum(judge_safety) / len(judge_safety), 2)
                if judge_safety
                else None,
            }

        # кто победил
        best_variant = None
        best_score = -1
        for v, data in summary["variants"].items():
            score = data["avg_overall_score"]
            if score > best_score:
                best_score = score
                best_variant = v
        summary["winner"] = {"variant": best_variant, "avg_overall_score": best_score}
        return summary

    def save_results(self, out_dir: str = "ml/ab_offline"):
        os.makedirs(out_dir, exist_ok=True)
        # сырые результаты
        with open(os.path.join(out_dir, "results.json"), "w", encoding="utf-8") as f:
            json.dump(
                [r.__dict__ for r in self.results],
                f,
                ensure_ascii=False,
                indent=2,
            )
        # сводка
        summary = self.summarize()
        with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n Результаты A/B‑теста сохранены в {out_dir}/results.json и {out_dir}/summary.json")
        if summary:
            print(f" Победитель: вариант {summary['winner']['variant']} "
                  f"(avg_overall={summary['winner']['avg_overall_score']})")


def main():
    tester = SleepABOfflineTester(variants=["A", "B"], max_tests=5)
    tester.run()
    tester.save_results()


if __name__ == "__main__":
    main()
