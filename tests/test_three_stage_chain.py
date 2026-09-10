import pytest

from three_stage_chain import three_stage_chain


class FakeChain:
    def __init__(self, output):
        self.output = output

    def invoke(self, data):
        return self.output


def test_three_stage_chain_success(monkeypatch):
    monkeypatch.setattr(
        three_stage_chain,
        "outline_chain",
        FakeChain(
            "1. Introduction\n"
            "2. Components\n"
            "3. Tools\n"
            "4. Memory\n"
            "5. Conclusion"
        ),
    )

    monkeypatch.setattr(
        three_stage_chain,
        "draft_chain",
        FakeChain(
            "AI agents are systems that can reason, use tools, "
            "and perform tasks based on user goals."
        ),
    )

    monkeypatch.setattr(
        three_stage_chain,
        "critique_chain",
        FakeChain(
            "Add examples, improve clarity, and explain tool usage."
        ),
    )

    result = three_stage_chain.run_chain("AI agents")

    assert result["topic"] == "AI agents"
    assert result["outline"]
    assert result["draft"]
    assert result["critique"]


def test_three_stage_chain_empty_topic():
    with pytest.raises(
        ValueError,
        match="Input cannot be empty",
    ):
        three_stage_chain.run_chain("")


def test_three_stage_chain_invalid_output(monkeypatch):
    monkeypatch.setattr(
        three_stage_chain,
        "outline_chain",
        FakeChain(""),
    )

    with pytest.raises(
        ValueError,
        match="outline produced empty output",
    ):
        three_stage_chain.run_chain("AI agents")