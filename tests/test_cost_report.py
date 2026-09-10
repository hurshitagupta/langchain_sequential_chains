import pytest

from cost_report import cost_report


def fake_call_model(stage, prompt):
    return {
        "output": f"Valid {stage} output",
        "input_tokens": 10,
        "output_tokens": 20,
        "total_tokens": 30,
        "latency": 0.5,
    }


def test_cost_report_success(monkeypatch):
    monkeypatch.setattr(
        cost_report,
        "call_model",
        fake_call_model,
    )

    result = cost_report.run_chain(
        "AI agents"
    )

    assert result["outline"] == "Valid outline output"
    assert result["draft"] == "Valid draft output"
    assert result["critique"] == "Valid critique output"

    assert result["metrics"]["outline"]["total_tokens"] == 30
    assert result["metrics"]["draft"]["total_tokens"] == 30
    assert result["metrics"]["critique"]["total_tokens"] == 30

    assert result["metrics"]["outline"]["latency"] == 0.5


def test_cost_report_empty_topic():
    with pytest.raises(
        ValueError,
        match="Input cannot be empty",
    ):
        cost_report.run_chain("")