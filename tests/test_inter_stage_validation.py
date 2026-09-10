import pytest

from inter_stage_validation import inter_stage_validation

class FakeChain:
    def __init__(self, output):
        self.output = output

    def invoke(self, data):
        return self.output


class ShouldNotRun:
    def invoke(self, data):
        raise AssertionError(
            "Next stage should not have executed"
        )


def test_inter_stage_validation_success(monkeypatch):
    monkeypatch.setattr(
        inter_stage_validation,
        "outline_chain",
        FakeChain( "This is a valid generated outline.")
    )

    monkeypatch.setattr(
        inter_stage_validation,
        "draft_chain",
        FakeChain("This is a valid generated draft.")
    )

    monkeypatch.setattr(
        inter_stage_validation,
        "critique_chain",
        FakeChain("This is a valid generated critique."),
    )

    result = inter_stage_validation.run_chain("AI agents")

    assert result["outline"]
    assert result["draft"]
    assert result["critique"]


def test_invalid_outline_stops_draft(monkeypatch):
    monkeypatch.setattr(
        inter_stage_validation,
        "outline_chain",
        FakeChain("short"),
    )

    monkeypatch.setattr(
        inter_stage_validation,
        "draft_chain",
        ShouldNotRun(),
    )

    with pytest.raises(
        ValueError,
        match="outline output is too short",
    ):
        inter_stage_validation.run_chain(
            "AI agents"
        )