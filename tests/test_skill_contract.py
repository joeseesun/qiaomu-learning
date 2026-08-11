#!/usr/bin/env python3
"""Standard-library contract tests for qiaomu-learning."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_skill.py"
QUESTION_MARK_RE = re.compile(r"[?？]")


def load_json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssertionError(f"{relative} must contain a JSON object")
    return value


def case_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {case["category"]: case for case in data["cases"]}


class SkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.triggers = load_json("evals/trigger_cases.json")
        cls.outputs = load_json("evals/output_cases.json")
        cls.by_category = case_map(cls.outputs)

    def test_standalone_validator_passes_complete_package(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(ROOT)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("PASS qiaomu-learning v2.0.1", result.stdout)

    def test_trigger_eval_is_bilingual_and_boundary_focused(self) -> None:
        cases = self.triggers["cases"]
        buckets = {case["bucket"] for case in cases}
        self.assertEqual({"should_trigger", "should_not_trigger", "near_neighbor"}, buckets)

        for bucket in buckets:
            bucket_cases = [case for case in cases if case["bucket"] == bucket]
            self.assertGreaterEqual(len(bucket_cases), 4)
            self.assertEqual({"zh-CN", "en"}, {case["language"] for case in bucket_cases})
            self.assertTrue(all(len(case["evaluator_concepts"]) >= 2 for case in bucket_cases))

        self.assertTrue(
            all(case["expected_activation"] for case in cases if case["bucket"] == "should_trigger")
        )
        self.assertTrue(
            all(
                not case["expected_activation"]
                for case in cases
                if case["bucket"] == "should_not_trigger"
            )
        )
        near_values = {
            case["expected_activation"] for case in cases if case["bucket"] == "near_neighbor"
        }
        self.assertEqual({True, False}, near_values)
        self.assertIn("semantically", self.triggers["evaluation_method"])

    def test_trigger_eval_has_no_magic_phrase_oracle(self) -> None:
        serialized = json.dumps(self.triggers, ensure_ascii=False).casefold()
        for forbidden_key in (
            '"exact_match"',
            '"expected_keyword"',
            '"expected_keywords"',
            '"must_contain"',
            '"required_phrase"',
            '"trigger_regex"',
        ):
            self.assertNotIn(forbidden_key, serialized)

    def test_trigger_eval_has_exact_meta_skill_projection(self) -> None:
        required_keys = {
            "recommended_threshold",
            "description_required_concepts",
            "positive_concepts",
            "negative_patterns",
            "should_trigger",
            "should_not_trigger",
            "near_neighbor",
        }
        self.assertTrue(required_keys.issubset(self.triggers))
        self.assertEqual(0.34, self.triggers["recommended_threshold"])
        self.assertTrue(
            set(self.triggers["description_required_concepts"]).issubset(
                self.triggers["positive_concepts"]
            )
        )

        expected = {
            "should_trigger": {},
            "should_not_trigger": {},
            "near_neighbor": {},
        }
        for case in self.triggers["cases"]:
            if case["expected_activation"]:
                destination = "should_trigger"
            elif case["bucket"] == "should_not_trigger":
                destination = "should_not_trigger"
            else:
                destination = "near_neighbor"
            expected[destination][case["id"]] = case["user_prompt"]

        projected_families: set[str] = set()
        for bucket, expected_items in expected.items():
            actual = {
                item["family"]: item["text"] for item in self.triggers[bucket]
            }
            self.assertEqual(expected_items, actual, bucket)
            self.assertTrue(projected_families.isdisjoint(actual), bucket)
            projected_families.update(actual)
        self.assertEqual(24, len(projected_families))

    def test_output_eval_covers_required_acceptance_scenarios(self) -> None:
        required = {
            "source_diagnostic",
            "correct_advance",
            "correct_transfer",
            "partial_target_gap",
            "incorrect_minimal_hint",
            "repeated_stall_reframe",
            "concrete_to_symbolic_clarity",
            "calculus_visual_first",
            "human_teacher_repair",
            "blackboard_progression",
            "keyword_orientation",
            "keyword_expansion",
            "complex_visual_imagegen",
            "image_success",
            "image_failure",
            "image_ineligible",
            "visual_recovery_spatial",
            "visual_recovery_process",
            "visual_recovery_geometry",
            "visual_recovery_ineligible",
            "explicit_exit",
            "source_injection_ocr",
            "sequential_ten_questions",
            "mastery_gate",
            "mastery_confirmed",
        }
        self.assertEqual("2.0.1", self.outputs["contract_version"])
        self.assertGreaterEqual(len(self.outputs["cases"]), 10)
        self.assertTrue(required.issubset(self.by_category))

    def test_every_active_fixture_has_one_question_and_puts_it_last(self) -> None:
        for case in self.outputs["cases"]:
            if case["category"] == "sequential_ten_questions":
                outputs = [turn["assistant_output"] for turn in case["turns"]]
            elif case["active_mode"]:
                outputs = [case["assistant_output"]]
            else:
                outputs = []
            for output in outputs:
                self.assertEqual(1, len(QUESTION_MARK_RE.findall(output)), case["id"])
                self.assertTrue(output.rstrip().endswith(("?", "？")), case["id"])

    def test_exit_and_completed_mastery_do_not_force_an_extra_question(self) -> None:
        for category in ("explicit_exit", "mastery_confirmed"):
            case = self.by_category[category]
            self.assertFalse(case["active_mode"])
            self.assertEqual(0, len(QUESTION_MARK_RE.findall(case["assistant_output"])))
            self.assertEqual(0, case["expected"]["semantic_question_count"])

    def test_adaptive_branches_encode_different_next_moves(self) -> None:
        self.assertEqual(
            "advance_depth", self.by_category["correct_advance"]["expected"]["next_move"]
        )
        self.assertEqual(
            "novel_transfer", self.by_category["correct_transfer"]["expected"]["next_move"]
        )
        self.assertEqual(
            "target_specific_gap",
            self.by_category["partial_target_gap"]["expected"]["next_move"],
        )
        incorrect = self.by_category["incorrect_minimal_hint"]["expected"]
        self.assertEqual("minimal_hint", incorrect["next_move"])
        self.assertFalse(incorrect["full_explanation_given"])

        stalled = self.by_category["repeated_stall_reframe"]
        self.assertEqual(3, stalled["context"]["consecutive_stalls"])
        self.assertEqual(
            "contrast_story_then_reconstruct", stalled["expected"]["next_move"]
        )
        self.assertIn(stalled["expected"]["story_sentence_count"], range(1, 4))
        self.assertTrue(stalled["expected"]["named_character"])

    def test_teacher_voice_and_blackboard_fixtures_preserve_progressive_teaching(self) -> None:
        repair = self.by_category["human_teacher_repair"]
        self.assertTrue(repair["expected"]["teacher_voice"])
        self.assertTrue(repair["expected"]["partial_correctness_preserved"])
        self.assertEqual("preserve-contrast-reconstruct", repair["expected"]["correction_style"])
        self.assertFalse(repair["expected"]["mechanical_interrogation"])
        self.assertEqual(1, repair["expected"]["new_visual_objects"])

        board = self.by_category["blackboard_progression"]
        self.assertTrue(board["expected"]["blackboard_cumulative"])
        self.assertEqual(1, board["expected"]["new_visual_objects"])
        self.assertEqual(0, board["expected"]["formula_layers_revealed"])
        self.assertFalse(board["expected"]["complete_solution_leaked"])

    def test_keyword_orientation_precedes_formal_socratic_learning(self) -> None:
        orientation = self.by_category["keyword_orientation"]
        self.assertEqual("broad_topic_without_source", orientation["context"]["source_kind"])
        self.assertEqual(12, len(orientation["keywords"]))
        self.assertTrue(all(item["plain_explanation"] for item in orientation["keywords"]))
        self.assertIn(len(orientation["context"]["experts"]), range(3, 6))
        self.assertIn(len(orientation["context"]["books"]), range(3, 6))
        self.assertTrue(orientation["expected"]["orientation_only"])
        self.assertFalse(orientation["expected"]["formal_learning_started"])
        self.assertTrue(orientation["expected"]["expansion_affordance"])
        self.assertTrue(orientation["expected"]["selection_question_only"])

    def test_keyword_expansion_adds_non_duplicate_terms(self) -> None:
        expansion = self.by_category["keyword_expansion"]
        self.assertEqual(12, expansion["context"]["previous_keyword_count"])
        terms = [item["term"] for item in expansion["new_keywords"]]
        self.assertEqual(len(terms), len(set(terms)))
        orientation_terms = {item["term"] for item in self.by_category["keyword_orientation"]["keywords"]}
        self.assertTrue(set(terms).isdisjoint(orientation_terms))
        self.assertEqual(8, expansion["expected"]["new_keyword_count"])
        self.assertEqual(20, expansion["expected"]["total_keyword_count"])
        self.assertEqual(0, expansion["expected"]["duplicate_count"])
        self.assertFalse(expansion["expected"]["formal_learning_started"])
        self.assertTrue(expansion["expected"]["selection_question_only"])

    def test_complex_visual_routes_to_codex_image_generation(self) -> None:
        visual_case = self.by_category["complex_visual_imagegen"]
        visual = visual_case["visual"]
        expected = visual_case["expected"]
        self.assertTrue(visual_case["context"]["complex_visual_relationship"])
        self.assertEqual("codex_builtin_imagegen", visual["tool"])
        self.assertTrue(visual["used"])
        self.assertTrue(visual["question_bearing"])
        self.assertFalse(visual["answer_leakage"])
        self.assertTrue(visual["alt_text"])
        self.assertTrue(expected["image_required"])
        self.assertTrue(expected["text_verification_present"])

    def test_image_success_failure_and_skip_paths_are_explicit(self) -> None:
        success = self.by_category["image_success"]
        self.assertTrue(success["visual"]["used"])
        self.assertTrue(success["visual"]["question_bearing"])
        self.assertFalse(success["visual"]["decorative"])
        self.assertFalse(success["visual"]["answer_leakage"])
        self.assertTrue(success["visual"]["alt_text"])

        failure = self.by_category["image_failure"]
        self.assertEqual("failure", failure["visual"]["result"])
        self.assertEqual("text_relationship", failure["visual"]["fallback"])
        self.assertTrue(failure["expected"]["continues_without_image"])

        skipped = self.by_category["image_ineligible"]
        self.assertFalse(skipped["visual"]["attempted"])
        self.assertFalse(skipped["visual"]["used"])

    def test_visual_recovery_requires_explicit_confusion_and_structural_fit(self) -> None:
        positive_categories = {
            "visual_recovery_spatial": ("too_abstract", "spatial", "太抽象"),
            "visual_recovery_process": ("does_not_understand", "process", "不理解"),
            "visual_recovery_geometry": ("explicit_draw_request", "geometry", "给我画图"),
        }
        for category, (signal, relationship, learner_phrase) in positive_categories.items():
            case = self.by_category[category]
            self.assertIn(learner_phrase, case["context"]["learner_request"], category)
            self.assertEqual(signal, case["context"]["recovery_signal"], category)
            self.assertEqual(relationship, case["context"]["relationship_type"], category)
            self.assertTrue(case["context"]["structural_visual_fit"], category)
            self.assertTrue(case["visual"]["used"], category)
            self.assertTrue(case["visual"]["recovery_mode"], category)
            self.assertTrue(case["visual"]["question_bearing"], category)
            self.assertFalse(case["visual"]["decorative"], category)
            self.assertFalse(case["visual"]["answer_leakage"], category)
            self.assertTrue(case["visual"]["alt_text"], category)
            self.assertIn(case["visual"]["alt_text"], case["assistant_output"], category)
            self.assertTrue(case["expected"]["entered_visual_recovery"], category)
            self.assertTrue(case["expected"]["text_alternative_present"], category)
            self.assertFalse(case["expected"]["answer_leakage"], category)
            self.assertEqual(1, len(QUESTION_MARK_RE.findall(case["assistant_output"])), category)
            self.assertTrue(case["assistant_output"].rstrip().endswith("？"), category)

        ineligible = self.by_category["visual_recovery_ineligible"]
        self.assertIn("给我画", ineligible["context"]["learner_request"])
        self.assertFalse(ineligible["context"]["structural_visual_fit"])
        self.assertEqual("conceptual_definition", ineligible["context"]["relationship_type"])
        self.assertFalse(ineligible["visual"]["attempted"])
        self.assertFalse(ineligible["visual"]["used"])
        self.assertFalse(ineligible["visual"]["recovery_mode"])
        self.assertFalse(ineligible["expected"]["entered_visual_recovery"])
        self.assertTrue(ineligible["expected"]["explicit_visual_request_recognized"])
        self.assertTrue(ineligible["expected"]["decorative_image_avoided"])

    def test_source_opening_and_ocr_injection_contracts(self) -> None:
        source = self.by_category["source_diagnostic"]
        self.assertEqual("readable_text", source["context"]["source_kind"])
        self.assertEqual("diagnostic_content_question", source["expected"]["opening_move"])
        self.assertFalse(source["expected"]["readiness_question"])

        injection = self.by_category["source_injection_ocr"]
        self.assertEqual("ocr_text", injection["context"]["source_kind"])
        self.assertTrue(injection["context"]["untrusted_source_instruction"])
        self.assertFalse(injection["expected"]["source_instruction_followed"])
        self.assertFalse(injection["expected"]["secret_requested"])

    def test_sequential_fixture_has_ten_adaptive_one_question_turns(self) -> None:
        case = self.by_category["sequential_ten_questions"]
        self.assertEqual(10, len(case["turns"]))
        self.assertEqual(list(range(1, 11)), [turn["turn"] for turn in case["turns"]])
        branches = {turn["branch"] for turn in case["turns"]}
        self.assertTrue(
            {"diagnostic", "correct_advance", "incorrect_minimal_hint", "partial_target_gap"}
            .issubset(branches)
        )

    def test_mastery_requires_own_words_and_novel_transfer(self) -> None:
        gate = self.by_category["mastery_gate"]
        self.assertTrue(gate["context"]["learner_evidence"]["own_words_explanation"])
        self.assertFalse(gate["context"]["learner_evidence"]["novel_transfer"])
        self.assertFalse(gate["expected"]["mastery_declared"])

        confirmed = self.by_category["mastery_confirmed"]
        self.assertTrue(confirmed["context"]["learner_evidence"]["own_words_explanation"])
        self.assertTrue(confirmed["context"]["learner_evidence"]["novel_transfer"])
        self.assertTrue(confirmed["expected"]["mastery_declared"])

    def test_validator_rejects_a_two_question_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            copied_root = Path(temp_dir) / ROOT.name
            shutil.copytree(ROOT, copied_root)
            fixture_path = copied_root / "evals" / "output_cases.json"
            mutated = json.loads(fixture_path.read_text(encoding="utf-8"))
            mutated["cases"][0]["assistant_output"] += " 准备好了吗？"
            fixture_path.write_text(
                json.dumps(mutated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

            result = subprocess.run(
                [sys.executable, str(copied_root / "scripts" / "validate_skill.py"), str(copied_root)],
                cwd=copied_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("active output must contain one question mark", result.stderr)

    def test_validator_rejects_disabled_spatial_visual_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            copied_root = Path(temp_dir) / ROOT.name
            shutil.copytree(ROOT, copied_root)
            fixture_path = copied_root / "evals" / "output_cases.json"
            mutated = json.loads(fixture_path.read_text(encoding="utf-8"))
            spatial_case = next(
                case
                for case in mutated["cases"]
                if case["category"] == "visual_recovery_spatial"
            )
            spatial_case["visual"]["used"] = False
            fixture_path.write_text(
                json.dumps(mutated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

            result = subprocess.run(
                [sys.executable, str(copied_root / "scripts" / "validate_skill.py"), str(copied_root)],
                cwd=copied_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertRegex(result.stderr.casefold(), r"visual[_ -]recovery")


if __name__ == "__main__":
    unittest.main()
