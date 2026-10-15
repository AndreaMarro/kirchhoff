"""La provenienza di una lezione installata non richiede Git al runtime."""

import importlib

from kirchhoff.pipeline.failure import Failure


DIVIDER = "V1 b 0 12 volt\nR1 b a 100 ohm\nR2 a 0 220 ohm\n? voltage R2"
lesson = importlib.import_module("kirchhoff.pipeline.lesson")
resolve = importlib.import_module("kirchhoff.pipeline.resolve")


def test_packaged_revision_precedes_git_and_rejects_corrupt_metadata(tmp_path, monkeypatch):
    metadata = tmp_path / "_build_source_sha.txt"
    metadata.write_text("a" * 40 + "\n", encoding="ascii")
    monkeypatch.delenv("KIRCHHOFF_SOURCE_SHA", raising=False)
    monkeypatch.setattr(resolve.resources, "files", lambda _: tmp_path)
    monkeypatch.setattr(resolve.subprocess, "run", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("Git called")))
    assert resolve._source_sha(None) == "a" * 40
    assert lesson.create_lesson(DIVIDER)["source_sha"] == "a" * 40
    metadata.write_text("not-a-revision", encoding="ascii")
    failed = resolve._source_sha(None)
    assert isinstance(failed, Failure)
    assert "metadato" in failed.messaggio


def test_lesson_reports_missing_revision_as_operational_failure(monkeypatch):
    monkeypatch.setattr(lesson, "_source_sha", lambda _: Failure("resolve", "revisione assente"))
    result = lesson.create_lesson(DIVIDER)
    assert result == {"outcome": "failure", "message": "revisione assente"}
