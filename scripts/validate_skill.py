#!/usr/bin/env python3
"""Deterministically validate the qiaomu-learning package.

This validator intentionally uses only the Python standard library so it can
run in a clean checkout without installing a YAML or test dependency.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


SKILL_NAME = "qiaomu-learning"
SKILL_VERSION = "2.0.0"

REQUIRED_FILES = (
    "SKILL.md",
    "README.md",
    "LICENSE",
    "manifest.json",
    "agents/interface.yaml",
    "references/socratic-protocol.md",
    "references/story-visual-learning.md",
    "references/teaching-clarity.md",
    "references/blackboard-teaching.md",
    "references/keyword-learning.md",
    "evals/trigger_cases.json",
    "evals/output_cases.json",
    "reports/prior-art-candidates.json",
    "reports/output-evidence.json",
    "scripts/validate_skill.py",
    "tests/test_skill_contract.py",
)

TRIGGER_BUCKETS = {"should_trigger", "should_not_trigger", "near_neighbor"}
OUTPUT_CATEGORIES = {
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

QUESTION_MARK_RE = re.compile(r"[?？]")
READINESS_RE = re.compile(
    r"(?:\bare you ready\b|\bready to (?:start|begin)\b|\bshall we begin\b|"
    r"\bwould you like to (?:start|begin)\b|准备好了吗|可以开始吗|要不要开始)",
    re.IGNORECASE,
)
COMPOUND_QUESTION_RE = re.compile(
    r"(?:\b(?:and|then)\s+(?:why|how|what|which|explain|give|apply)\b|"
    r"(?:并|以及|然后|再)(?:解释|说明|举例|回答|计算|应用|为什么|如何|怎么))",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(
    r"(?:\bTODO\b|\bTBD\b|\bFIXME\b|\bXXX\b|"
    r"\{\{[^{}]+\}\}|<(?:YOUR|INSERT)[^>]*>|\[INSERT[^\]]*\]|待补充|待完善)",
    re.IGNORECASE,
)
MAGIC_ORACLE_KEYS = {
    "exact_match",
    "expected_keyword",
    "expected_keywords",
    "must_contain",
    "required_phrase",
    "required_phrases",
    "trigger_regex",
}


def _load_text(path: Path, errors: list[str], label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{label}: cannot read {path}: {exc}")
        return ""


def _load_json(path: Path, errors: list[str], label: str) -> dict[str, Any]:
    text = _load_text(path, errors, label)
    if not text:
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"{label}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label}: top-level JSON value must be an object")
        return {}
    return value


def _contains_any(text: str, alternatives: Iterable[str]) -> bool:
    lowered = text.casefold()
    return any(alternative.casefold() in lowered for alternative in alternatives)


def _require_concept(
    errors: list[str], text: str, label: str, alternatives: Iterable[str]
) -> None:
    if not _contains_any(text, alternatives):
        errors.append(f"core contract: missing {label}")


def _frontmatter(markdown: str, errors: list[str]) -> str:
    if not markdown.startswith("---\n"):
        errors.append("identity: SKILL.md must start with YAML frontmatter")
        return ""
    end = markdown.find("\n---\n", 4)
    if end < 0:
        errors.append("identity: SKILL.md frontmatter is not closed")
        return ""
    return markdown[4:end]


def _question_count(text: str) -> int:
    return len(QUESTION_MARK_RE.findall(text))


def _question_is_last(text: str) -> bool:
    return text.rstrip().endswith(("?", "？"))


def _iter_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _iter_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_keys(nested)


def _validate_required_files(root: Path, errors: list[str]) -> None:
    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.is_file():
            errors.append(f"required files: missing {relative}")

    skill_files = sorted(path.relative_to(root).as_posix() for path in root.rglob("SKILL.md"))
    if skill_files != ["SKILL.md"]:
        errors.append(
            "required files: expected exactly one canonical root SKILL.md; "
            f"found {skill_files or 'none'}"
        )


def _validate_identity(
    skill_text: str,
    interface_text: str,
    manifest: dict[str, Any],
    errors: list[str],
) -> None:
    frontmatter = _frontmatter(skill_text, errors)
    name_match = re.search(r"(?m)^name:\s*['\"]?([^'\"\s]+)['\"]?\s*$", frontmatter)
    if not name_match or name_match.group(1) != SKILL_NAME:
        errors.append(f"identity: SKILL.md name must be {SKILL_NAME!r}")

    if not re.search(r"(?m)^description:\s*(?:\||>|\S)", frontmatter):
        errors.append("identity: SKILL.md frontmatter must include a description")

    version_match = re.search(r"(?m)^\s*version:\s*['\"]?([^'\"\s]+)['\"]?\s*$", frontmatter)
    if not version_match or version_match.group(1) != SKILL_VERSION:
        errors.append(f"identity: SKILL.md metadata version must be {SKILL_VERSION!r}")

    if manifest.get("name") != SKILL_NAME:
        errors.append(f"identity: manifest.json name must be {SKILL_NAME!r}")
    if manifest.get("version") != SKILL_VERSION:
        errors.append(f"identity: manifest.json version must be {SKILL_VERSION!r}")
    if manifest.get("copyright") != "Copyright (c) 向阳乔木":
        errors.append("identity: manifest.json must contain the canonical copyright notice")

    interface_markers = (
        "interface:",
        "display_name:",
        "default_prompt:",
        "mode: \"explicit-opt-in\"",
        "active_turn_contract:",
    )
    for marker in interface_markers:
        if marker not in interface_text:
            errors.append(f"identity: agents/interface.yaml is missing {marker!r}")


def _validate_readme(readme: str, errors: list[str]) -> None:
    required_phrases = {
        "skill name": (SKILL_NAME,),
        "version": (f"v{SKILL_VERSION}",),
        "one-question promise": (
            "只出现一个面向学习者的简洁问题",
            "每个有效回合只向学习者提出一个",
            "exactly one concise learner-facing question",
        ),
        "validator command": ("python3 scripts/validate_skill.py .",),
        "evidence boundary": ("missing evidence",),
        "copyright": ("Copyright (c) 向阳乔木",),
        "X contact": ("https://x.com/vista8",),
        "GitHub contact": ("https://github.com/joeseesun/",),
    }
    for label, alternatives in required_phrases.items():
        if not _contains_any(readme, alternatives):
            errors.append(f"README: missing {label}")

    placeholder = PLACEHOLDER_RE.search(readme)
    if placeholder:
        errors.append(f"README: unresolved placeholder token {placeholder.group(0)!r}")


def _validate_trigger_cases(data: dict[str, Any], errors: list[str]) -> None:
    if data.get("skill") != SKILL_NAME or data.get("contract_version") != SKILL_VERSION:
        errors.append("trigger eval: skill identity/version mismatch")
    if "semantic" not in str(data.get("evaluation_method", "")).casefold():
        errors.append("trigger eval: evaluation method must explicitly require semantic judgment")

    declared_buckets = data.get("buckets")
    if not isinstance(declared_buckets, dict) or set(declared_buckets) != TRIGGER_BUCKETS:
        errors.append(f"trigger eval: buckets must be exactly {sorted(TRIGGER_BUCKETS)}")

    cases = data.get("cases")
    if not isinstance(cases, list):
        errors.append("trigger eval: cases must be a list")
        return
    if len(cases) < 12:
        errors.append("trigger eval: at least 12 cases are required")

    ids: set[str] = set()
    by_bucket: dict[str, list[dict[str, Any]]] = {bucket: [] for bucket in TRIGGER_BUCKETS}
    for index, case in enumerate(cases):
        label = f"trigger eval case {index + 1}"
        if not isinstance(case, dict):
            errors.append(f"{label}: must be an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"{label}: missing non-empty id")
        elif case_id in ids:
            errors.append(f"trigger eval: duplicate id {case_id!r}")
        else:
            ids.add(case_id)

        bucket = case.get("bucket")
        if bucket not in TRIGGER_BUCKETS:
            errors.append(f"{label}: invalid bucket {bucket!r}")
        else:
            by_bucket[bucket].append(case)

        if case.get("language") not in {"zh-CN", "en"}:
            errors.append(f"{label}: language must be 'zh-CN' or 'en'")
        if not isinstance(case.get("user_prompt"), str) or not case["user_prompt"].strip():
            errors.append(f"{label}: user_prompt must be non-empty")
        concepts = case.get("evaluator_concepts")
        if not isinstance(concepts, list) or len(concepts) < 2 or not all(
            isinstance(item, str) and item.strip() for item in concepts
        ):
            errors.append(f"{label}: evaluator_concepts must contain at least two semantic concepts")
        if not isinstance(case.get("rationale"), str) or not case["rationale"].strip():
            errors.append(f"{label}: rationale must be non-empty")
        if not isinstance(case.get("expected_activation"), bool):
            errors.append(f"{label}: expected_activation must be boolean")

    for bucket, bucket_cases in by_bucket.items():
        if len(bucket_cases) < 4:
            errors.append(f"trigger eval: bucket {bucket!r} needs at least four cases")
        languages = {case.get("language") for case in bucket_cases}
        if languages != {"zh-CN", "en"}:
            errors.append(f"trigger eval: bucket {bucket!r} must cover Chinese and English")

    if any(case.get("expected_activation") is not True for case in by_bucket["should_trigger"]):
        errors.append("trigger eval: every should_trigger case must activate")
    if any(case.get("expected_activation") is not False for case in by_bucket["should_not_trigger"]):
        errors.append("trigger eval: every should_not_trigger case must not activate")
    near_values = {case.get("expected_activation") for case in by_bucket["near_neighbor"]}
    if near_values != {True, False}:
        errors.append("trigger eval: near_neighbor must include both activating and non-activating cases")

    forbidden_keys = MAGIC_ORACLE_KEYS.intersection(_iter_keys(data))
    if forbidden_keys:
        errors.append(
            "trigger eval: semantic cases must not use magic phrase or exact-match oracle keys: "
            + ", ".join(sorted(forbidden_keys))
        )

    _validate_meta_trigger_projection(data, cases, errors)


def _validate_meta_trigger_projection(
    data: dict[str, Any], cases: list[Any], errors: list[str]
) -> None:
    """Validate the qiaomu-meta-skill trigger_eval.py compatibility view."""

    threshold = data.get("recommended_threshold")
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or not 0 < threshold <= 1:
        errors.append("trigger eval meta schema: recommended_threshold must be a number in (0, 1]")

    concepts = data.get("positive_concepts")
    if not isinstance(concepts, dict) or not concepts:
        errors.append("trigger eval meta schema: positive_concepts must be a non-empty object")
        concepts = {}
    else:
        for concept, vocabulary in concepts.items():
            if not isinstance(concept, str) or not concept.strip():
                errors.append("trigger eval meta schema: concept names must be non-empty strings")
            if not isinstance(vocabulary, list) or len(vocabulary) < 2 or not all(
                isinstance(phrase, str) and phrase.strip() for phrase in vocabulary
            ):
                errors.append(
                    f"trigger eval meta schema: concept {concept!r} needs at least two non-empty phrases"
                )
            elif len({phrase.casefold() for phrase in vocabulary}) != len(vocabulary):
                errors.append(
                    f"trigger eval meta schema: concept {concept!r} contains duplicate vocabulary"
                )

    required_concepts = data.get("description_required_concepts")
    if not isinstance(required_concepts, list) or not required_concepts or not all(
        isinstance(item, str) and item for item in required_concepts
    ):
        errors.append(
            "trigger eval meta schema: description_required_concepts must be a non-empty string list"
        )
    elif not set(required_concepts).issubset(concepts):
        errors.append(
            "trigger eval meta schema: every required description concept must exist in positive_concepts"
        )

    negative_patterns = data.get("negative_patterns")
    if not isinstance(negative_patterns, list) or not negative_patterns or not all(
        isinstance(pattern, str) and pattern.strip() for pattern in negative_patterns
    ):
        errors.append("trigger eval meta schema: negative_patterns must be a non-empty string list")

    expected_projection: dict[str, dict[str, str]] = {
        "should_trigger": {},
        "should_not_trigger": {},
        "near_neighbor": {},
    }
    for case in cases:
        if not isinstance(case, dict):
            continue
        case_id = case.get("id")
        prompt = case.get("user_prompt")
        bucket = case.get("bucket")
        activation = case.get("expected_activation")
        if not isinstance(case_id, str) or not isinstance(prompt, str):
            continue
        if activation is True:
            projected_bucket = "should_trigger"
        elif bucket == "should_not_trigger":
            projected_bucket = "should_not_trigger"
        elif bucket == "near_neighbor":
            projected_bucket = "near_neighbor"
        else:
            continue
        expected_projection[projected_bucket][case_id] = prompt

    projected_families: set[str] = set()
    for bucket, expected_items in expected_projection.items():
        raw_items = data.get(bucket)
        if not isinstance(raw_items, list):
            errors.append(f"trigger eval meta schema: {bucket} must be a list")
            continue
        actual_items: dict[str, str] = {}
        for index, item in enumerate(raw_items, 1):
            if not isinstance(item, dict):
                errors.append(
                    f"trigger eval meta schema: {bucket} item {index} must be an object with text/family"
                )
                continue
            text = item.get("text")
            family = item.get("family")
            if not isinstance(text, str) or not text.strip() or not isinstance(family, str) or not family:
                errors.append(
                    f"trigger eval meta schema: {bucket} item {index} needs non-empty text and family"
                )
                continue
            if family in projected_families:
                errors.append(f"trigger eval meta schema: duplicate projected family {family!r}")
            projected_families.add(family)
            actual_items[family] = text
        if actual_items != expected_items:
            missing = sorted(set(expected_items) - set(actual_items))
            extra = sorted(set(actual_items) - set(expected_items))
            changed = sorted(
                family
                for family in set(actual_items).intersection(expected_items)
                if actual_items[family] != expected_items[family]
            )
            errors.append(
                f"trigger eval meta schema: {bucket} is not an exact projection of custom cases "
                f"(missing={missing}, extra={extra}, changed={changed})"
            )


def _validate_turn_text(text: Any, label: str, errors: list[str]) -> None:
    if not isinstance(text, str) or not text.strip():
        errors.append(f"{label}: assistant_output must be non-empty text")
        return
    count = _question_count(text)
    if count != 1:
        errors.append(f"{label}: active output must contain one question mark, found {count}")
    if not _question_is_last(text):
        errors.append(f"{label}: active output question must be last")
    readiness = READINESS_RE.search(text)
    if readiness:
        errors.append(f"{label}: contains readiness/permission question {readiness.group(0)!r}")
    compound = COMPOUND_QUESTION_RE.search(text)
    if compound:
        errors.append(f"{label}: appears to combine multiple learner tasks {compound.group(0)!r}")


def _case_by_category(cases: list[dict[str, Any]], category: str) -> dict[str, Any]:
    return next((case for case in cases if case.get("category") == category), {})


def _validate_output_cases(data: dict[str, Any], errors: list[str]) -> None:
    if data.get("skill") != SKILL_NAME or data.get("contract_version") != SKILL_VERSION:
        errors.append("output eval: skill identity/version mismatch")
    policy = data.get("question_policy", {})
    if not isinstance(policy, dict) or policy.get("active_turn_semantic_question_count") != 1:
        errors.append("output eval: question policy must require exactly one semantic question")
    if not isinstance(policy, dict) or policy.get("question_must_be_last") is not True:
        errors.append("output eval: question policy must put the question last")

    raw_cases = data.get("cases")
    if not isinstance(raw_cases, list):
        errors.append("output eval: cases must be a list")
        return
    cases = [case for case in raw_cases if isinstance(case, dict)]
    if len(raw_cases) < 10:
        errors.append("output eval: at least ten acceptance scenarios are required")
    if len(cases) != len(raw_cases):
        errors.append("output eval: every case must be an object")

    ids: set[str] = set()
    categories: set[str] = set()
    for index, case in enumerate(cases):
        label = f"output eval case {case.get('id') or index + 1}"
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"{label}: missing non-empty id")
        elif case_id in ids:
            errors.append(f"output eval: duplicate id {case_id!r}")
        else:
            ids.add(case_id)

        category = case.get("category")
        if not isinstance(category, str):
            errors.append(f"{label}: missing category")
        else:
            categories.add(category)
        if case.get("language") not in {"zh-CN", "en"}:
            errors.append(f"{label}: language must be 'zh-CN' or 'en'")
        concepts = case.get("evaluation_concepts")
        if not isinstance(concepts, list) or len(concepts) < 2:
            errors.append(f"{label}: needs at least two evaluation_concepts")

        if category == "sequential_ten_questions":
            turns = case.get("turns")
            if not isinstance(turns, list) or len(turns) != 10:
                errors.append(f"{label}: sequential fixture must contain exactly ten turns")
                continue
            for turn_index, turn in enumerate(turns, 1):
                if not isinstance(turn, dict):
                    errors.append(f"{label} turn {turn_index}: must be an object")
                    continue
                if turn.get("turn") != turn_index:
                    errors.append(f"{label} turn {turn_index}: turn numbers must be sequential")
                _validate_turn_text(turn.get("assistant_output"), f"{label} turn {turn_index}", errors)
            continue

        active_mode = case.get("active_mode")
        if not isinstance(active_mode, bool):
            errors.append(f"{label}: active_mode must be boolean")
            continue
        output = case.get("assistant_output")
        expected = case.get("expected")
        if not isinstance(expected, dict):
            errors.append(f"{label}: expected must be an object")
            continue
        if active_mode:
            _validate_turn_text(output, label, errors)
            if expected.get("semantic_question_count") != 1:
                errors.append(f"{label}: expected semantic_question_count must be 1")
            if expected.get("question_is_last") is not True:
                errors.append(f"{label}: expected question_is_last must be true")
        else:
            if not isinstance(output, str) or not output.strip():
                errors.append(f"{label}: inactive assistant_output must be non-empty")
            elif _question_count(output) != 0:
                errors.append(f"{label}: inactive exit/completion output must not force another question")
            if expected.get("semantic_question_count") != 0:
                errors.append(f"{label}: inactive expected semantic_question_count must be 0")

    missing_categories = OUTPUT_CATEGORIES - categories
    if missing_categories:
        errors.append("output eval: missing categories: " + ", ".join(sorted(missing_categories)))

    source = _case_by_category(cases, "source_diagnostic")
    if source.get("expected", {}).get("opening_move") != "diagnostic_content_question":
        errors.append("output eval: readable source must open with a diagnostic content question")

    keyword_orientation = _case_by_category(cases, "keyword_orientation")
    keyword_context = keyword_orientation.get("context", {})
    keyword_expected = keyword_orientation.get("expected", {})
    keyword_items = keyword_orientation.get("keywords")
    experts = keyword_context.get("experts")
    books = keyword_context.get("books")
    orientation_terms: set[str] = set()
    if not isinstance(keyword_items, list) or len(keyword_items) != 12:
        errors.append("output eval: keyword orientation must contain exactly 12 default keyword items")
    else:
        for index, item in enumerate(keyword_items, 1):
            if not isinstance(item, dict) or not item.get("term") or not item.get("plain_explanation"):
                errors.append(f"output eval: keyword item {index} needs a term and plain explanation")
            elif isinstance(item.get("term"), str):
                orientation_terms.add(item["term"])
    if not isinstance(experts, list) or not 3 <= len(experts) <= 5:
        errors.append("output eval: keyword orientation must recommend 3 to 5 experts")
    if not isinstance(books, list) or not 3 <= len(books) <= 5:
        errors.append("output eval: keyword orientation must recommend 3 to 5 books")
    if not (
        keyword_context.get("source_kind") == "broad_topic_without_source"
        and keyword_expected.get("orientation_only") is True
        and keyword_expected.get("formal_learning_started") is False
        and keyword_expected.get("keyword_count") == 12
        and keyword_expected.get("keyword_explanations_count") == 12
        and keyword_expected.get("expansion_affordance") is True
        and keyword_expected.get("selection_question_only") is True
    ):
        errors.append("output eval: keyword orientation must precede formal tutoring with one selection question")

    keyword_expansion = _case_by_category(cases, "keyword_expansion")
    expansion_context = keyword_expansion.get("context", {})
    expansion_expected = keyword_expansion.get("expected", {})
    expansion_items = keyword_expansion.get("new_keywords")
    if not isinstance(expansion_items, list) or not expansion_items:
        errors.append("output eval: keyword expansion must add at least one keyword")
    else:
        terms = [
            item.get("term")
            for item in expansion_items
            if isinstance(item, dict) and item.get("term")
        ]
        if len(terms) != len(set(terms)):
            errors.append("output eval: keyword expansion must not duplicate its own new terms")
        if not all(isinstance(item, dict) and item.get("term") and item.get("plain_explanation") for item in expansion_items):
            errors.append("output eval: expanded keyword items need terms and plain explanations")
        overlap = orientation_terms.intersection(terms)
        if overlap:
            errors.append(
                "output eval: keyword expansion must not repeat default terms: "
                + ", ".join(sorted(overlap))
            )
        if expansion_expected.get("new_keyword_count") != len(expansion_items):
            errors.append("output eval: keyword expansion count metadata must match its new items")
        expected_total = expansion_context.get("previous_keyword_count")
        if isinstance(expected_total, int):
            expected_total += len(expansion_items)
        if expansion_expected.get("total_keyword_count") != expected_total:
            errors.append("output eval: keyword expansion total count must equal previous plus new items")
        if expansion_context.get("requested") == "扩展关键词":
            if not isinstance(expected_total, int) or not 20 <= expected_total <= 25:
                errors.append(
                    "output eval: default keyword expansion should land at roughly 20 to 25 total terms"
                )
    if not (
        expansion_context.get("requested") in {"扩展关键词", "扩展到 25 个"}
        and expansion_context.get("previous_keyword_count") == 12
        and expansion_expected.get("duplicate_count") == 0
        and expansion_expected.get("formal_learning_started") is False
        and expansion_expected.get("selection_question_only") is True
    ):
        errors.append("output eval: keyword expansion must add non-duplicate terms before formal tutoring")

    complex_visual = _case_by_category(cases, "complex_visual_imagegen")
    complex_context = complex_visual.get("context", {})
    complex_visual_meta = complex_visual.get("visual", {})
    complex_expected = complex_visual.get("expected", {})
    if not (
        complex_context.get("complex_visual_relationship") is True
        and complex_visual_meta.get("tool") == "codex_builtin_imagegen"
        and complex_visual_meta.get("used") is True
        and complex_visual_meta.get("question_bearing") is True
        and complex_visual_meta.get("decorative") is False
        and complex_visual_meta.get("answer_leakage") is False
        and complex_visual_meta.get("alt_text")
        and complex_expected.get("image_required") is True
        and complex_expected.get("text_verification_present") is True
    ):
        errors.append(
            "output eval: complex multi-layer visual steps must route to Codex image generation "
            "with alt text, verification, and one non-leaking question"
        )

    correct_moves = {
        _case_by_category(cases, "correct_advance").get("expected", {}).get("next_move"),
        _case_by_category(cases, "correct_transfer").get("expected", {}).get("next_move"),
    }
    if correct_moves != {"advance_depth", "novel_transfer"}:
        errors.append("output eval: correct branches must cover advancement and transfer")

    partial = _case_by_category(cases, "partial_target_gap")
    if partial.get("expected", {}).get("next_move") != "target_specific_gap":
        errors.append("output eval: partial branch must target the identified gap")

    incorrect = _case_by_category(cases, "incorrect_minimal_hint")
    if (
        incorrect.get("expected", {}).get("next_move") != "minimal_hint"
        or incorrect.get("expected", {}).get("full_explanation_given") is not False
    ):
        errors.append("output eval: incorrect branch must provide a minimal hint, not the full answer")

    stalled = _case_by_category(cases, "repeated_stall_reframe")
    stalled_expected = stalled.get("expected", {})
    stalled_context = stalled.get("context", {})
    story_count = stalled_expected.get("story_sentence_count")
    if not isinstance(story_count, int) or not 1 <= story_count <= 3:
        errors.append("output eval: repeated-stall story must be one to three sentences")
    if (
        stalled_context.get("consecutive_stalls", 0) < 3
        or stalled_expected.get("next_move") != "contrast_story_then_reconstruct"
        or not stalled_expected.get("named_character")
    ):
        errors.append("output eval: third stall must reframe then ask one reconstruction question")

    image_success = _case_by_category(cases, "image_success")
    success_visual = image_success.get("visual", {})
    if not (
        success_visual.get("used") is True
        and success_visual.get("result") == "success"
        and success_visual.get("question_bearing") is True
        and success_visual.get("decorative") is False
        and success_visual.get("answer_leakage") is False
        and success_visual.get("alt_text")
    ):
        errors.append("output eval: successful image must be eligible, question-bearing, non-decorative, non-leaking, and accessible")

    image_failure = _case_by_category(cases, "image_failure")
    failure_visual = image_failure.get("visual", {})
    if not (
        failure_visual.get("attempted") is True
        and failure_visual.get("result") == "failure"
        and failure_visual.get("fallback") == "text_relationship"
        and image_failure.get("expected", {}).get("continues_without_image") is True
    ):
        errors.append("output eval: failed image generation must continue with a text relationship fallback")

    image_ineligible = _case_by_category(cases, "image_ineligible").get("visual", {})
    if image_ineligible.get("used") is not False or image_ineligible.get("attempted") is not False:
        errors.append("output eval: ineligible/decorative image case must skip generation")

    recovery_requirements = {
        "visual_recovery_spatial": ("too_abstract", "spatial"),
        "visual_recovery_process": ("does_not_understand", "process"),
        "visual_recovery_geometry": ("explicit_draw_request", "geometry"),
    }
    for category, (signal, relationship_type) in recovery_requirements.items():
        recovery = _case_by_category(cases, category)
        context = recovery.get("context", {})
        visual = recovery.get("visual", {})
        expected = recovery.get("expected", {})
        output = recovery.get("assistant_output", "")
        if not (
            context.get("recovery_signal") == signal
            and context.get("relationship_type") == relationship_type
            and context.get("structural_visual_fit") is True
            and visual.get("used") is True
            and visual.get("result") == "success"
            and visual.get("recovery_mode") is True
            and visual.get("question_bearing") is True
            and visual.get("decorative") is False
            and visual.get("answer_leakage") is False
            and isinstance(visual.get("alt_text"), str)
            and visual["alt_text"] in output
            and expected.get("entered_visual_recovery") is True
            and expected.get("text_alternative_present") is True
            and expected.get("answer_leakage") is False
        ):
            errors.append(
                f"output eval: {category} must switch an eligible confused learner "
                "to accessible, non-leaking visual recovery with one question"
            )

    recovery_ineligible = _case_by_category(cases, "visual_recovery_ineligible")
    recovery_ineligible_context = recovery_ineligible.get("context", {})
    recovery_ineligible_visual = recovery_ineligible.get("visual", {})
    recovery_ineligible_expected = recovery_ineligible.get("expected", {})
    if not (
        recovery_ineligible_context.get("structural_visual_fit") is False
        and recovery_ineligible_visual.get("attempted") is False
        and recovery_ineligible_visual.get("used") is False
        and recovery_ineligible_visual.get("recovery_mode") is False
        and recovery_ineligible_expected.get("entered_visual_recovery") is False
        and recovery_ineligible_expected.get("explicit_visual_request_recognized") is True
        and recovery_ineligible_expected.get("decorative_image_avoided") is True
    ):
        errors.append(
            "output eval: an explicit image request without structural fit must "
            "avoid decorative generation and continue with one concrete text scaffold"
        )

    explicit_exit = _case_by_category(cases, "explicit_exit")
    if explicit_exit.get("active_mode") is not False or explicit_exit.get("expected", {}).get("direct_answer_given") is not True:
        errors.append("output eval: explicit exit must leave active mode and provide the requested direct answer")

    injection = _case_by_category(cases, "source_injection_ocr")
    injection_expected = injection.get("expected", {})
    if not (
        injection.get("context", {}).get("source_kind") == "ocr_text"
        and injection.get("context", {}).get("untrusted_source_instruction") is True
        and injection_expected.get("source_instruction_followed") is False
        and injection_expected.get("secret_requested") is False
        and injection_expected.get("opening_move") == "diagnostic_content_question"
    ):
        errors.append("output eval: OCR/source-injection case must ignore embedded instructions and ask a content diagnostic")

    mastery_gate = _case_by_category(cases, "mastery_gate")
    gate_evidence = mastery_gate.get("context", {}).get("learner_evidence", {})
    gate_expected = mastery_gate.get("expected", {})
    if not (
        gate_evidence.get("own_words_explanation") is True
        and gate_evidence.get("novel_transfer") is False
        and gate_expected.get("mastery_declared") is False
        and gate_expected.get("requires_own_words") is True
        and gate_expected.get("requires_novel_transfer") is True
    ):
        errors.append("output eval: own words without novel transfer must not pass the mastery gate")

    mastery_confirmed = _case_by_category(cases, "mastery_confirmed")
    confirmed_evidence = mastery_confirmed.get("context", {}).get("learner_evidence", {})
    if not (
        confirmed_evidence.get("own_words_explanation") is True
        and confirmed_evidence.get("novel_transfer") is True
        and mastery_confirmed.get("expected", {}).get("mastery_declared") is True
    ):
        errors.append("output eval: mastery confirmation must require own-words and novel-transfer evidence")


def _validate_core_contract(
    skill_text: str,
    protocol_text: str,
    visual_text: str,
    errors: list[str],
) -> None:
    combined = "\n".join((skill_text, protocol_text, visual_text))
    requirements = {
        "one semantic learner-facing question per active turn": (
            "只有一个实质性的学习问题",
            "exactly one concise learner-facing question per active turn",
        ),
        "question-last rule": ("放在最后", "位于最后", "question must be last"),
        "no rhetorical/readiness/compound questions": (
            "准备好了吗",
            "修辞问句",
            "拼接了第二任务",
        ),
        "readable-source diagnostic opening": (
            "第一轮直接问一个内容诊断题",
            "第一问直接检查内容",
        ),
        "correct, partial, and incorrect adaptation": (
            "正确且理由充分",
            "部分正确",
            "错误或猜测",
        ),
        "repeated-stall reframe": (
            "再次卡住给边界对比",
            "连续失败说明问题或支架需要改变",
        ),
        "explicit exit to direct answer": (
            "停止提问 / 直接回答",
            "停止提问 / 直接告诉我",
            "immediately exit",
        ),
        "source-injection resistance": (
            "提示注入",
            "属于被分析内容",
            "never as agent instructions",
        ),
        "image eligibility gate": (
            "空间结构、因果链、顺序、几何",
            "依赖空间、因果、顺序、几何",
        ),
        "image text fallback": ("等价文字描述", "文字、ASCII", "text-only fallback"),
        "image answer-leak prevention": ("不标出正确选项", "不得把答案直接写在标签里"),
        "explicit visual recovery": (
            "显式困惑立即换模态",
            "下一次用户可见回复必须立即换模态",
        ),
        "human teacher voice": (
            "接住上一句",
            "保留 → 区分 → 重建",
            "真人老师会在必要时替学习者补半步",
        ),
        "cumulative blackboard progression": (
            "会累积的黑板",
            "每次只新增一个关键笔画",
            "逐层展开",
        ),
        "complex visual Codex image routing": (
            "两层以上相互作用的结构",
            "必须调用它",
            "复杂多层结构优先调用 Codex 内置生图",
        ),
        "visual recovery asks a stepped-down observation": (
            "从图上可直接观察的降阶问题",
            "把台阶降到一个可观察问题",
        ),
        "mastery needs own words and transfer": (
            "own_words=true",
            "transfer=true",
            "用自己的话解释",
            "新表面情境",
        ),
    }

    # Some requirements need every listed marker, while the rest accept synonyms.
    require_all = {
        "no rhetorical/readiness/compound questions",
        "correct, partial, and incorrect adaptation",
        "mastery needs own words and transfer",
    }
    for label, alternatives in requirements.items():
        if label in require_all:
            for marker in alternatives:
                if not _contains_any(combined, (marker,)):
                    errors.append(f"core contract: missing {label} marker {marker!r}")
        else:
            _require_concept(errors, combined, label, alternatives)


def _validate_evidence(data: dict[str, Any], errors: list[str]) -> None:
    if data.get("skill") != SKILL_NAME or data.get("contract_version") != SKILL_VERSION:
        errors.append("evidence report: skill identity/version mismatch")

    checks = data.get("recorded_checks")
    if not isinstance(checks, list) or not checks:
        errors.append("evidence report: recorded_checks must be a non-empty list")
    else:
        for index, check in enumerate(checks, 1):
            if not isinstance(check, dict):
                errors.append(f"evidence report: recorded check {index} must be an object")
                continue
            if check.get("evidence_type") != "recorded_static_fixture":
                errors.append(f"evidence report: check {index} must be labeled recorded_static_fixture")
            if check.get("status") != "pass":
                errors.append(f"evidence report: recorded static check {index} must have status 'pass'")
            if not check.get("evidence"):
                errors.append(f"evidence report: recorded static check {index} needs concrete evidence")

    missing = data.get("missing_evidence")
    required_dimensions = {
        "provider_backed",
        "human_blind_review",
        "real_learner_outcomes",
    }
    if not isinstance(missing, list):
        errors.append("evidence report: missing_evidence must be a list")
        return
    statuses = {
        item.get("dimension"): item.get("status")
        for item in missing
        if isinstance(item, dict)
    }
    if set(statuses) != required_dimensions:
        errors.append(
            "evidence report: missing_evidence dimensions must be exactly "
            + ", ".join(sorted(required_dimensions))
        )
    for dimension in required_dimensions:
        if statuses.get(dimension) != "missing evidence":
            errors.append(f"evidence report: {dimension} must be marked 'missing evidence'")


def validate_skill(root: Path) -> list[str]:
    """Return a deterministic list of validation errors for *root*."""

    root = root.resolve()
    errors: list[str] = []
    if not root.is_dir():
        return [f"root: not a directory: {root}"]

    _validate_required_files(root, errors)

    skill_text = _load_text(root / "SKILL.md", errors, "SKILL.md")
    readme_text = _load_text(root / "README.md", errors, "README.md")
    interface_text = _load_text(root / "agents/interface.yaml", errors, "agents/interface.yaml")
    protocol_text = _load_text(
        root / "references/socratic-protocol.md", errors, "references/socratic-protocol.md"
    )
    visual_text = _load_text(
        root / "references/story-visual-learning.md", errors, "references/story-visual-learning.md"
    )

    manifest = _load_json(root / "manifest.json", errors, "manifest.json")
    triggers = _load_json(root / "evals/trigger_cases.json", errors, "trigger_cases.json")
    outputs = _load_json(root / "evals/output_cases.json", errors, "output_cases.json")
    prior_art = _load_json(
        root / "reports/prior-art-candidates.json", errors, "prior-art-candidates.json"
    )
    evidence = _load_json(
        root / "reports/output-evidence.json", errors, "output-evidence.json"
    )

    _validate_identity(skill_text, interface_text, manifest, errors)
    _validate_readme(readme_text, errors)
    _validate_trigger_cases(triggers, errors)
    _validate_output_cases(outputs, errors)
    _validate_core_contract(skill_text, protocol_text, visual_text, errors)
    _validate_evidence(evidence, errors)

    if prior_art and (prior_art.get("ok") is not True or prior_art.get("complete") is not True):
        errors.append("prior-art report: research record must be marked ok and complete")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="skill package root (default: current directory)",
    )
    args = parser.parse_args(argv)
    root = Path(args.root)
    errors = validate_skill(root)
    if errors:
        print(f"FAIL {SKILL_NAME} v{SKILL_VERSION}: {len(errors)} error(s)", file=sys.stderr)
        for index, error in enumerate(errors, 1):
            print(f"  {index}. {error}", file=sys.stderr)
        return 1

    print(
        f"PASS {SKILL_NAME} v{SKILL_VERSION}: package structure, identity, "
        "README, trigger fixtures, output fixtures, evidence boundaries, and core invariants"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
