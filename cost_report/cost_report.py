import os
import time

from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda
from langchain_openrouter import ChatOpenRouter

from guardrails import (check_step_limit, check_token_budget, validate_input, validate_output)

load_dotenv()

model = ChatOpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model=os.getenv("MODEL_NAME"),
    base_url=os.getenv("BASE_URL"),
    temperature=0,
    timeout=20_000,
    max_tokens=500,
)


def call_model(stage: str, prompt: str) -> dict:
    start_time = time.perf_counter()

    response = model.invoke(prompt)

    latency = time.perf_counter() - start_time

    output = response.content

    validate_output(stage, output)

    usage = response.usage_metadata or {}

    return {
        "output": output,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "latency": latency,
    }


def create_outline(state: dict) -> dict:
    prompt = (
        f"Write a 5-bullet outline about "
        f"{state['topic']}."
    )

    result = call_model("outline",prompt)

    state["outline"] = result["output"]
    state["metrics"]["outline"] = result

    return state


def create_draft(state: dict) -> dict:
    prompt = f"""
Using this outline:

{state["outline"]}

Write a short draft of about 150 words on {state["topic"]}.
"""

    result = call_model(
        "draft",
        prompt,
    )

    state["draft"] = result["output"]
    state["metrics"]["draft"] = result

    return state


def create_critique(state: dict) -> dict:
    prompt = f"""
Review the following draft about {state["topic"]}:

{state["draft"]}

List 3 concrete improvements that could make the draft better.
"""

    result = call_model(
        "critique",
        prompt,
    )

    state["critique"] = result["output"]
    state["metrics"]["critique"] = result

    return state


outline_chain = RunnableLambda(create_outline).with_retry(
    stop_after_attempt=3
)


draft_chain = RunnableLambda(create_draft).with_retry(
    stop_after_attempt=3
)


critique_chain = RunnableLambda(create_critique).with_retry(
    stop_after_attempt=3
)


def print_cost_report(metrics: dict) -> None:
    print("\n=== COST REPORT ===")

    print(
        f"{'Stage':<12}"
        f"{'Input':>10}"
        f"{'Output':>10}"
        f"{'Total':>10}"
        f"{'Latency(s)':>14}"
    )

    print("-" * 56)

    total_input = 0
    total_output = 0
    total_tokens = 0
    total_latency = 0.0

    for stage in ("outline", "draft", "critique"):
        data = metrics[stage]

        print(
            f"{stage.capitalize():<12}"
            f"{data['input_tokens']:>10}"
            f"{data['output_tokens']:>10}"
            f"{data['total_tokens']:>10}"
            f"{data['latency']:>14.2f}"
        )

        total_input += data["input_tokens"]
        total_output += data["output_tokens"]
        total_tokens += data["total_tokens"]
        total_latency += data["latency"]

    print("-" * 56)

    print(
        f"{'TOTAL':<12}"
        f"{total_input:>10}"
        f"{total_output:>10}"
        f"{total_tokens:>10}"
        f"{total_latency:>14.2f}"
    )


def run_chain(topic: str) -> dict:
    validate_input(topic)
    check_token_budget(topic)

    state = {
        "topic": topic,
        "metrics": {},
    }

    step_count = 0

    check_step_limit(step_count)
    state = outline_chain.invoke(state)
    step_count += 1

    check_step_limit(step_count)
    state = draft_chain.invoke(state)
    step_count += 1

    check_step_limit(step_count)
    state = critique_chain.invoke(state)
    step_count += 1

    print(
        f"\nCompleted {step_count}/3 allowed stages"
    )

    print_cost_report(
        state["metrics"]
    )

    return state


if __name__ == "__main__":
    result = run_chain(
        "token budgeting for AI agents"
    )

    print("\n=== FINAL OUTPUT ===")

    print("\nOUTLINE:")
    print(result["outline"])

    print("\nDRAFT:")
    print(result["draft"])

    print("\nCRITIQUE:")
    print(result["critique"])