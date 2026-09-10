import time

from langchain_core.runnables import RunnableLambda

from guardrails import (check_step_limit,check_token_budget,validate_output)



def step_limit_evidence():
    print("\n=== STEP LIMIT EVIDENCE ===")

    try:
        check_step_limit(3)

    except RuntimeError as error:
        print(error)


def token_budget_evidence():
    print("\n=== TOKEN BUDGET EVIDENCE ===")

    try:
        long_input = "A" * 1000
        check_token_budget(long_input)

    except ValueError as error:
        print(error)


def validation_evidence():
    print("\n=== VALIDATION EVIDENCE ===")

    try:
        validate_output("outline", "")

    except ValueError as error:
        print(error)
        print("Invalid output quarantined and not passed to next stage")


retry_attempt = 0


def unstable_call(data):
    global retry_attempt

    retry_attempt += 1

    print(f"Retry attempt {retry_attempt}")

    if retry_attempt < 3:
        raise ValueError("Temporary model failure")

    return "Call succeeded"


def retry_evidence():
    print("\n=== RETRY EVIDENCE ===")

    retry_chain = RunnableLambda(
        unstable_call
    ).with_retry(
        retry_if_exception_type=(ValueError,),
        stop_after_attempt=3,
    )

    result = retry_chain.invoke({})

    print(result)


def slow_call():
    time.sleep(3)
    return "Finished"



if __name__ == "__main__":
    step_limit_evidence()
    token_budget_evidence()
    validation_evidence()
    retry_evidence()
