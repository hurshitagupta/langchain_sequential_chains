# LangChain Sequential Chains

This assessment focuses on building multi-stage sequential pipelines using LangChain. The pipeline is developed incrementally across the tasks, starting with a basic three-stage chain and later adding cumulative state, validation, resumability, and stage-level measurements.

## Task 1 — Three-Stage Chain

Task 1 implements a sequential pipeline consisting of three separate LangChain Runnables:

```text
Topic → Outline → Draft → Critique
```

Each stage consumes information produced by the previous stage and performs a separate model call.

### Implementation

The pipeline contains three independent Runnables:

* **Outline Chain** — generates a 5-bullet outline for the provided topic.
* **Draft Chain** — uses the original topic and generated outline to create a short draft.
* **Critique Chain** — reviews the generated draft and provides three concrete improvements.

Each stage is constructed using:

```text
ChatPromptTemplate → ChatOpenRouter → StrOutputParser
```

The output of one stage is explicitly passed to the next stage rather than combining the entire workflow into a single prompt.

The final result contains:

```text
topic
outline
draft
critique
```

### Guardrails

The project uses shared guardrails that can be reused by the sequential-chain tasks.

The controls currently implemented are:

* **Step limit** — limits the pipeline to a maximum of three stages.
* **Retry** — LangChain's `with_retry()` provides capped retry attempts for Runnable failures.
* **Timeout** — model calls have a configured per-call timeout.
* **Token budget** — oversized input is rejected before model execution using an estimated input-token limit.
* **Validation** — empty user input and empty model outputs are rejected.
* **Secret hygiene** — API credentials are loaded from environment variables and are not hardcoded in source files.

Guardrail behaviour for step limits, retries, token-budget rejection, and validation is demonstrated through the shared `guardrail_evidence.py` script.

### Testing

Task 1 contains automated tests covering:

* Successful execution of all three stages.
* Rejection of empty input.
* Rejection of invalid/empty stage output.

Fake Runnables are used in the tests so that the test suite remains deterministic and does not depend on external model calls.

### Run Task 1

```bash
uv run python -m three_stage_chain.three_stage_chain
```

### Run Task 1 Tests

```bash
uv run pytest tests/test_three_stage_chain.py -v
```

### Save Task 1 Output

```bash
uv run python -m three_stage_chain.three_stage_chain > outputs/three_stage_chain_output.txt
```

### Save Test Output

```bash
uv run pytest tests/test_three_stage_chain.py -v > outputs/test_three_stage_chain.txt
```

### Guardrail Evidence

Run the shared guardrail evidence:

```bash
uv run python guardrail_evidence.py
```

Save the evidence:

```bash
uv run python guardrail_evidence.py > outputs/guardrail_evidence.txt
```

## Task 1 Result

Task 1 demonstrates a working three-stage sequential chain where the outline, draft, and critique are implemented as separate Runnables. Each stage executes in sequence, model output is validated before being used or returned, and the implementation includes shared controls for step limits, retries, timeouts, token budgeting, validation, and secret hygiene.
