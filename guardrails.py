MAX_STEPS = 3
MAX_INPUT_TOKENS = 100


def validate_input(text: str) -> None:
    if not text or not text.strip():
        raise ValueError("Input cannot be empty")


def check_token_budget(text: str) -> None:
    estimated_tokens = len(text) // 4

    if estimated_tokens > MAX_INPUT_TOKENS:
        raise ValueError(
            f"Token budget rejected: estimated {estimated_tokens} tokens "
            f"exceeds limit of {MAX_INPUT_TOKENS}"
        )


def validate_output(stage: str, output: str) -> None:
    if not output or not output.strip():
        raise ValueError(
            f"Validation failed: {stage} produced empty output"
        )


def check_step_limit(step_count: int) -> None:
    if step_count >= MAX_STEPS:
        raise RuntimeError(
            f"Step limit reached: maximum {MAX_STEPS} stages allowed"
        )