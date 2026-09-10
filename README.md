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

---

## Task 2 — Cumulative Payload

Task 2 extends the three-stage sequential chain by carrying the original input and all intermediate outputs forward in a single cumulative dictionary.

The state grows as the pipeline executes:

```text id="k7d4uq"
{"topic"}
     ↓
{"topic", "outline"}
     ↓
{"topic", "outline", "draft"}
     ↓
{"topic", "outline", "draft", "critique"}
```

### Implementation

The pipeline begins with:

```python id="h5edq5"
state = {
    "topic": topic
}
```

Each stage receives the same cumulative state and adds its own result:

```python id="dnclj2"
state["outline"] = outline_chain.invoke(state)

state["draft"] = draft_chain.invoke(state)

state["critique"] = critique_chain.invoke(state)
```

This ensures that later stages have access to both the original input and all previously generated values.

The execution state is created locally inside `run_chain()` rather than stored in a global variable. Each pipeline execution therefore maintains its own independent state.

### Cumulative State

During execution, the payload progresses through the following stages:

**Initial state**

```python id="tdh1gw"
{
    "topic": "AI agents"
}
```

**After outline**

```python id="czsw7u"
{
    "topic": "AI agents",
    "outline": "..."
}
```

**After draft**

```python id="bdh61r"
{
    "topic": "AI agents",
    "outline": "...",
    "draft": "..."
}
```

**Final state**

```python id="b82jq9"
{
    "topic": "AI agents",
    "outline": "...",
    "draft": "...",
    "critique": "..."
}
```

The final state dictionary is returned directly by the pipeline.

### Testing

Task 2 includes automated tests for both successful and invalid execution.

The success test verifies that the final returned dictionary contains the original topic along with all three intermediate outputs:

```text
topic
outline
draft
critique
```

The failure test verifies that an empty topic is rejected before pipeline execution.

Fake Runnables are used during testing so the tests remain deterministic and do not require external API calls.

### Guardrails

Task 2 reuses the shared project guardrails implemented in `guardrails.py`, including:

* Step limit
* Capped retries
* Per-call timeout
* Input token budget
* Input and output validation
* Environment-variable based secret handling

The shared `guardrail_evidence.py` and saved guardrail output provide project-level evidence for the implemented controls.

### Run Task 2

```bash id="0il6y8"
uv run python -m cumulative_payload.cumulative_payload
```

### Run Task 2 Tests

```bash id="ldxpt8"
uv run pytest tests/test_cumulative_payload.py -v
```

### Save Task 2 Output

```bash id="g8fcjy"
uv run python -m cumulative_payload.cumulative_payload > outputs/cumulative_payload.txt
```

### Save Test Output

```bash id="kh6y9b"
uv run pytest tests/test_cumulative_payload.py -v > outputs/test_cumulative_payload.txt
```

## Task 2 Result

Task 2 demonstrates explicit cumulative state management across a sequential pipeline. The original topic and every intermediate result are retained in one dictionary and passed forward to subsequent stages without relying on hidden global state.

