import pytest

from cumulative_payload import cumulative_payload


class FakeChain:
    def __init__(self, output):
        self.output = output

    def invoke(self, data):
        return self.output


def test_cumulative_payload_success(monkeypatch):
    monkeypatch.setattr(
        cumulative_payload,
        "outline_chain",
        FakeChain("Generated outline"),
    )

    monkeypatch.setattr(
        cumulative_payload,
        "draft_chain",
        FakeChain("Generated draft"),
    )

    monkeypatch.setattr(
        cumulative_payload,
        "critique_chain",
        FakeChain("Generated critique"),
    )

    result = cumulative_payload.run_chain(
        "AI agents"
    )

    assert result["topic"] == "AI agents"
    assert result["outline"] == "Generated outline"
    assert result["draft"] == "Generated draft"
    assert result["critique"] == "Generated critique"


def test_cumulative_payload_empty_topic():
    with pytest.raises(
        ValueError,
        match="Input cannot be empty",
    ):
        cumulative_payload.run_chain("")