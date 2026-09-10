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

---

## Task 3 — Inter-Stage Validation

Task 3 extends the cumulative sequential pipeline by adding a validation gate between each stage.

The pipeline now follows:

```text
Outline → Validate → Draft → Validate → Critique → Validate
```

A stage must produce valid output before the following stage is allowed to execute.

### Implementation

A stage-level validation function is used to check every generated result:

```python
def validate_stage(stage: str, output: str) -> None:
    validate_output(stage, output)

    if len(output.strip()) < 10:
        raise ValueError(
            f"Validation failed: {stage} output is too short"
        )

    print(f"{stage.capitalize()} validation passed")
```

The shared `validate_output()` guardrail first rejects empty output. The additional stage validation rejects output that is too short to be considered usable.

Validation occurs immediately after every model call and before the following Runnable executes.

For example:

```text
Outline generated
      ↓
Outline validated
      ↓
Draft generated
      ↓
Draft validated
      ↓
Critique generated
      ↓
Critique validated
```

If validation fails at any point, an exception stops the pipeline and the next stage is not executed.

### Testing

Task 3 includes a success case where all three stages return valid output and complete successfully.

The failure case deliberately makes the outline return an invalid short value. The draft stage is replaced with a `ShouldNotRun` fake that raises an assertion if it is called.

This verifies that an invalid outline stops execution before the draft stage rather than allowing invalid intermediate data to continue through the pipeline.

### Evidence

A successful execution produced:

```text
Outline validation passed
Draft validation passed
Critique validation passed

Completed 3/3 allowed stages
```

This demonstrates that each generated stage result was validated before execution continued.

### Run Task 3

```bash
uv run python -m inter_stage_validation.inter_stage_validation
```

### Run Task 3 Tests

```bash
uv run pytest tests/test_inter_stage_validation.py -v
```

### Save Task 3 Output

```bash
uv run python -m inter_stage_validation.inter_stage_validation > outputs/inter_stage_validation.txt
```

### Save Test Output

```bash
uv run pytest tests/test_inter_stage_validation.py -v > outputs/test_inter_stage_validation.txt
```

## Task 3 Result

Task 3 demonstrates inter-stage validation in the sequential pipeline. Every generated result is checked before it can become input to the following stage, preventing invalid intermediate output from propagating through the chain.

---

## Task 4 — Resumability

Task 4 extends the sequential pipeline by persisting successfully completed stage results. If execution fails at a later stage, the saved state can be loaded and the pipeline can continue without rerunning stages that have already completed successfully.

### Implementation

Pipeline state is persisted in a JSON file:

```text id="vmrh77"
state.json
```

Two functions handle persistence:

```python id="0azny8"
save_state(state)
load_state(topic)
```

After each stage completes and passes validation, the cumulative state is saved:

```text id="i0hl7q"
Outline
   ↓
Validate
   ↓
Save state

Draft
   ↓
Validate
   ↓
Save state

Critique
   ↓
Validate
   ↓
Save state
```

Saving occurs **after validation**, ensuring that invalid stage output is not treated as a successful checkpoint.

### Resume Behaviour

When the pipeline starts, it checks for previously saved state:

```python id="zjdtpw"
state = load_state(topic)
```

Before executing each stage, the pipeline checks whether that stage already exists in the saved state.

For example:

```python id="gk03wi"
if "outline" in state:
    print("Skipping outline - already completed")
```

The same mechanism is used for the draft and critique stages.

Conceptually, a failed execution can therefore behave as:

```text id="78sr13"
First execution:

Topic
  ↓
Outline ✓
  ↓
Validate ✓
  ↓
Save
  ↓
Draft ✗
  ↓
STOP
```

The saved state still contains the successfully generated outline.

On the next execution:

```text id="sqzkt6"
Load saved state
      ↓
Outline already exists → Skip
      ↓
Draft → Continue
      ↓
Critique → Continue
```

This allows recovery to resume from the last successfully completed stage rather than restarting the complete pipeline.

### Topic Safety

Saved state is reused only when its topic matches the requested topic:

```python id="uh4bc8"
if state.get("topic") == topic:
```

If the topic is different, a new state is created. This prevents intermediate results from an unrelated previous pipeline run from being reused.

### Testing

Task 4 includes automated tests for successful execution and failure recovery.

The success test verifies that:

* Outline, draft, and critique are generated.
* The final cumulative state contains all stage results.
* The state file is successfully persisted.

The resumability failure test simulates a draft-stage failure after the outline has completed.

The test then invokes the pipeline again with the saved state and verifies that the previously completed outline is not executed again. The draft and critique stages continue from the saved checkpoint.

A `ShouldNotRun` fake is used for the outline during the resumed execution. If the pipeline incorrectly attempts to regenerate the completed outline, the test fails.

This provides automated evidence that recovery **resumes rather than restarts**.

### Guardrails

Task 4 continues to use the shared project guardrails:

* Step limit for newly executed stages
* Capped Runnable retries
* Per-call model timeout
* Input token budget
* Input validation
* Inter-stage output validation
* Environment-variable based secret handling

Only successfully validated stage results are persisted.

### Run Task 4

```bash id="45ggby"
uv run python -m resumability.resumability
```

### Run Task 4 Tests

```bash id="b5zuxz"
uv run pytest tests/test_resumability.py -v
```

### Save Task 4 Output

```bash id="ihdq8g"
uv run python -m resumability.resumability > outputs/resumability.txt
```

### Save Test Output

```bash id="x8c4ny"
uv run pytest tests/test_resumability.py -v > outputs/test_resumability.txt
```

## Task 4 Result

Task 4 implements resumability using persisted cumulative state. Each successfully validated stage is saved immediately, and previously completed stages are skipped when matching state is loaded. The automated failure test demonstrates that execution can continue from the last successful stage instead of restarting the complete sequential pipeline.

---

## Task 5 — Cost Report

Task 5 extends the sequential pipeline with stage-level measurements for token usage and latency.

Each model call is measured independently so that the resource usage of the outline, draft, and critique stages can be compared.

### Implementation

A shared `call_model()` function handles each model invocation and records its measurements.

Latency is measured using:

```python id="85ul0i"
start_time = time.perf_counter()
response = model.invoke(prompt)
latency = time.perf_counter() - start_time
```

Token usage is collected from the model response metadata:

```python id="1yk6az"
usage = response.usage_metadata or {}
```

For every stage, the following values are recorded:

* Input tokens
* Output tokens
* Total tokens
* Latency

The measurements are stored inside the cumulative state under the `metrics` dictionary.

### Separate Runnables

The three stages remain separate LangChain Runnables:

```python id="kbhc9l"
outline_chain = RunnableLambda(create_outline)
draft_chain = RunnableLambda(create_draft)
critique_chain = RunnableLambda(create_critique)
```

Each stage performs its own model call and adds both its generated output and measurement data to the cumulative state.

### Cost Report

After all three stages complete, `print_cost_report()` displays the measurements in a table:

```text id="8fd4qx"
Stage            Input    Output     Total    Latency(s)
--------------------------------------------------------
Outline             ...       ...       ...          ...
Draft               ...       ...       ...          ...
Critique            ...       ...       ...          ...
--------------------------------------------------------
TOTAL               ...       ...       ...          ...
```

The total row aggregates token usage and latency across the complete sequential pipeline.

The report focuses on the measurements required by the assessment rather than using a hardcoded monetary price for a specific model.

### Testing

Task 5 includes automated success and failure tests.

The success test uses a deterministic fake model-call function with fixed token and latency values. It verifies that:

* All three sequential stages complete.
* Each stage produces output.
* Token measurements are stored for each stage.
* Latency is recorded in the metrics.
* The cumulative state contains the generated results and measurement information.

The failure test verifies that an empty topic is rejected before the sequential pipeline begins.

Fake measurement data is used in automated tests so they remain deterministic and do not depend on API availability or variable model latency.

### Guardrails

Task 5 continues to use the shared project guardrails:

* Step limit
* Capped retries
* Per-call timeout
* Input token budget
* Output validation
* Secret hygiene through environment variables

The shared guardrail evidence demonstrates the implemented step-limit, retry, token-budget, and validation controls.

### Run Task 5

```bash id="6ncv44"
uv run python -m cost_report.cost_report
```

### Run Task 5 Tests

```bash id="vfrq1b"
uv run pytest tests/test_cost_report.py -v
```

### Save Task 5 Output

```bash id="nv0b06"
uv run python -m cost_report.cost_report > outputs/cost_report.txt
```

### Save Test Output

```bash id="ebxf7n"
uv run pytest tests/test_cost_report.py -v > outputs/test_cost_report.txt
```

## Task 5 Result

Task 5 adds measurable stage-level reporting to the sequential pipeline. Token usage and latency are captured independently for the outline, draft, and critique stages and presented in a consolidated table, providing numerical evidence of the execution cost of each stage.

