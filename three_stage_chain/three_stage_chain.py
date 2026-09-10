import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openrouter import ChatOpenRouter

from guardrails import (check_step_limit,check_token_budget,validate_input,validate_output)


load_dotenv()


model = ChatOpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model=os.getenv("MODEL_NAME"),
    base_url=os.getenv("BASE_URL"),
    temperature=0,
    timeout=20_000,
    max_tokens=300,
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
Review the following draft:

{draft}

List 3 concrete improvements that could make the draft better.
"""
)


outline_chain = (outline_prompt| model| StrOutputParser()).with_retry(
    stop_after_attempt=3
)


draft_chain = (draft_prompt| model| StrOutputParser()).with_retry(
    stop_after_attempt=3
)


critique_chain = (critique_prompt| model| StrOutputParser()).with_retry(
    stop_after_attempt=3
)


def run_chain(topic: str) -> dict:
    validate_input(topic)
    check_token_budget(topic)

    step_count = 0

    check_step_limit(step_count)

    outline = outline_chain.invoke(
        {"topic": topic}
    )

    validate_output("outline", outline)
    step_count += 1

    check_step_limit(step_count)

    draft = draft_chain.invoke(
        {
            "topic": topic,
            "outline": outline,
        }
    )

    validate_output("draft", draft)
    step_count += 1

    check_step_limit(step_count)

    critique = critique_chain.invoke(
        {
            "draft": draft,
        }
    )

    validate_output("critique", critique)
    step_count += 1

    print(f"\nCompleted {step_count}/3 allowed stages")

    return {
        "topic": topic,
        "outline": outline,
        "draft": draft,
        "critique": critique,
    }


if __name__ == "__main__":
    result = run_chain("token budgeting for AI agents")

    print("\n=== OUTLINE ===")
    print(result["outline"])

    print("\n=== DRAFT ===")
    print(result["draft"])

    print("\n=== CRITIQUE ===")
    print(result["critique"])
