from __future__ import annotations

import json
from pathlib import Path

from src.learning import memory_gateway_feedback as feedback


def test_parse_worktree_list_parses_porcelain_blocks() -> None:
    raw = "\n".join(
        [
            "worktree /repo",
            "HEAD abc123",
            "branch refs/heads/main",
            "",
            "worktree /repo/.worktrees/task-a",
            "HEAD def456",
            "branch refs/heads/task-a",
            "",
        ]
    )

    entries = feedback.parse_worktree_list(raw)

    assert len(entries) == 2
    assert entries[0]["worktree"] == "/repo"
    assert entries[1]["branch"] == "refs/heads/task-a"


def test_resolve_thumbgate_paths_prefers_canonical_checkout_feedback_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:
    canonical_root = tmp_path / "repo"
    canonical_root.mkdir()
    (canonical_root / ".thumbgate").mkdir()
    worktree_root = canonical_root / ".worktrees" / "task-a"
    worktree_root.mkdir(parents=True)

    monkeypatch.setattr(feedback, "_find_project_root", lambda _: worktree_root)
    monkeypatch.setattr(feedback, "_select_canonical_root", lambda _: canonical_root)

    paths = feedback.resolve_thumbgate_paths(worktree_root)

    assert paths.project_root == worktree_root
    assert paths.canonical_root == canonical_root
    assert paths.feedback_dir == canonical_root / ".thumbgate"
    assert paths.legacy_feedback_dir == canonical_root / ".rlhf"


def test_select_relevant_lessons_prefers_high_signal_command_matches(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    feedback_dir = project_root / ".thumbgate"
    feedback_dir.mkdir()

    entries = [
        {
            "title": "SUCCESS: Snapshot manifest writer must append a trailing newline",
            "content": "Keep docs/assets/snapshots/latest.json formatter-clean before git push.",
            "category": "learning",
            "tags": ["snapshot", "ci", "push", "trunk"],
            "timestamp": "2026-04-08T23:02:30.897Z",
            "occurrences": 2,
        },
        {
            "title": "SUCCESS: OpenRouter observability route coverage",
            "content": "Verify actual runtime routes before claiming visibility.",
            "category": "learning",
            "tags": ["observability"],
            "timestamp": "2026-04-08T21:01:31.034Z",
            "occurrences": 1,
        },
    ]
    (feedback_dir / "memory-log.jsonl").write_text(
        "\n".join(json.dumps(entry) for entry in entries) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        feedback,
        "resolve_thumbgate_paths",
        lambda _: feedback.ThumbgatePaths(
            project_root=project_root,
            canonical_root=project_root,
            feedback_dir=feedback_dir,
            legacy_feedback_dir=project_root / ".rlhf",
            prevention_rules=feedback_dir / "prevention-rules.md",
            summary_path=feedback_dir / "feedback-summary.json",
            feedback_log=feedback_dir / "feedback-log.jsonl",
            memory_log=feedback_dir / "memory-log.jsonl",
            recent_lesson_path=feedback_dir / "recent-lesson.json",
        ),
    )

    lessons = feedback.select_relevant_lessons(project_root, command="git push origin branch")

    assert len(lessons) == 1
    assert "Snapshot manifest writer must append a trailing newline" in lessons[0].title
