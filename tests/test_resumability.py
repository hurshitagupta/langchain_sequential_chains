import pytest

from resumability import resumability


class FakeChain:
    def __init__(self, output):
        self.output = output

    def invoke(self, data):
        return self.output


class FailingChain:
    def invoke(self, data):
        raise RuntimeError("Simulated draft failure")


class ShouldNotRun:
    def invoke(self, data):
        raise AssertionError(
            "Completed stage was executed again"
        )


def test_resumability_success(monkeypatch, tmp_path):
    monkeypatch.setattr(
        resumability,"STATE_FILE",tmp_path / "state.json",
    )

    monkeypatch.setattr(
        resumability,"outline_chain",FakeChain("This is a valid generated outline."),
    )

    monkeypatch.setattr(
        resumability, "draft_chain", FakeChain("This is a valid generated draft."),
    )

    monkeypatch.setattr(
        resumability,"critique_chain", FakeChain("This is a valid generated critique."),
    )

    result = resumability.run_chain(
        "AI agents"
    )

    assert result["outline"]
    assert result["draft"]
    assert result["critique"]

    assert resumability.STATE_FILE.exists()


def test_resume_after_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(
        resumability,
        "STATE_FILE",
        tmp_path / "state.json",
    )

    # First run:outline succeeds, draft fails
    monkeypatch.setattr(
        resumability,"outline_chain",FakeChain("This is a valid saved outline."),
    )

    monkeypatch.setattr(
        resumability,"draft_chain",FailingChain(),
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated draft failure",
    ):
        resumability.run_chain("AI agents")

    # Second run: outline must NOT execute again
    monkeypatch.setattr(
        resumability,"outline_chain",ShouldNotRun(),
    )

    monkeypatch.setattr(
        resumability, "draft_chain", FakeChain("This is the resumed valid draft."),
    )

    monkeypatch.setattr(
        resumability,"critique_chain",FakeChain("This is the resumed valid critique."),
    )

    result = resumability.run_chain(
        "AI agents"
    )

    assert result["outline"] == "This is a valid saved outline."
    assert result["draft"] == "This is the resumed valid draft."
    assert result["critique"] == "This is the resumed valid critique."