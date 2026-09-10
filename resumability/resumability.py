import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter

from guardrails import (check_step_limit,check_token_budget,validate_input,validate_output)

load_dotenv()

STATE_FILE = Path("state.json")

model = ChatOpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model=os.getenv("MODEL_NAME"),
    base_url=os.getenv("BASE_URL"),
    temperature=0,
    timeout=20_000,
    max_tokens=500,
)

outline_prompt = ChatPromptTemplate.from_template(
    "Write a 5-bullet outline about {topic}."
)

draft_prompt = ChatPromptTemplate.from_template(
    """
Using this outline:

{outline}

Write a short draft of about 150 words on {topic}.
"""
)

critique_prompt = ChatPromptTemplate.from_template(
    """
Review the following draft about {topic}:

{draft}

List 3 concrete improvements that could make the draft better.
"""
)


outline_chain = ( outline_prompt | model | StrOutputParser()).with_retry(
    stop_after_attempt=3
)


draft_chain = ( draft_prompt | model | StrOutputParser()).with_retry(
    stop_after_attempt=3
)


critique_chain = ( critique_prompt | model | StrOutputParser()).with_retry(
    stop_after_attempt=3
)

def validate_stage(stage: str, output: str) -> None:
    validate_output(stage, output)

    if len(output.strip()) < 10:
        raise ValueError(
            f"Validation failed: {stage} output is too short"
        )

    print(f"{stage.capitalize()} validation passed")


def save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(state, indent=2),
        encoding="utf-8",
    )

    print("State saved")


def load_state(topic: str) -> dict:
    if STATE_FILE.exists():
        state = json.loads(
            STATE_FILE.read_text(encoding="utf-8")
        )

        if state.get("topic") == topic:
            print("Loaded saved state")
            return state

    return {
        "topic": topic
    }


def run_chain(topic: str) -> dict:
    validate_input(topic)
    check_token_budget(topic)

    state = load_state(topic)

    step_count = 0

    if "outline" in state:
        print("Skipping outline - already completed")

    else:
        check_step_limit(step_count)

        print("Running outline...")

        state["outline"] = outline_chain.invoke(state)

        validate_stage("outline", state["outline"])

        step_count += 1
        save_state(state)

    if "draft" in state:
        print("Skipping draft - already completed")

    else:
        check_step_limit(step_count)

        print("Running draft...")

        state["draft"] = draft_chain.invoke(state)

        validate_stage("draft", state["draft"])

        step_count += 1
        save_state(state)

    if "critique" in state:
        print("Skipping critique - already completed")

    else:
        check_step_limit(step_count)

        print("Running critique...")

        state["critique"] = critique_chain.invoke(state)

        validate_stage("critique",state["critique"])

        step_count += 1
        save_state(state)

    print("\nPipeline completed")

    return state


if __name__ == "__main__":
    result = run_chain(
        "token budgeting for AI agents"
    )

    print("\n=== FINAL STATE ===")

    for key, value in result.items():
        print(f"\n{key.upper()}:")
        print(value)