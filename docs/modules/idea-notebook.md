# Algorithm Idea Notebook

## Status

Implemented and verified as a passive, local-only Algorithm Control submodule.

## Purpose

Give the user one place inside the existing Algorithm Control GUI to write, edit, tag, archive, restore, and review free-form algorithm ideas without turning those notes into executable definitions or inputs.

## Responsibilities

- Keep immutable note identity and UTC creation/update timestamps.
- Validate non-empty titles and bodies and normalize duplicate tags deterministically.
- List active notes and optionally archived notes.
- Save the complete note collection to a dedicated local JSON file using atomic replacement.
- Expose a small service and Store Protocol so persistence can be tested independently from the GUI.
- Present note editing in the `算法 Idea 笔记` page of the existing Algorithm Control application.

## Non-responsibilities

- It does not register a component, Factor, Market Factor, Decision, Risk rule, strategy, or proposal.
- It does not calculate a Factor, create a TradeIntent, run a Pipeline or Backtest, or call Portfolio Accounting or Execution.
- It does not read Market History, SQLite, broker, account, position, order, or fill data.
- It does not convert, apply, activate, publish, or execute note content.
- It is not a credential or secret store. API keys, passwords, authorization data, and account-sensitive information must not be entered.

## Public interfaces

`IdeaNote`, `IdeaNoteStatus`, `IdeaNoteStore`, `InMemoryIdeaNoteStore`, `JsonIdeaNoteStore`, `IdeaNotebookService`, and `IdeaNotebookPanel`.

These interfaces are internal to the Algorithm Control feature; they are deliberately not re-exported as algorithm-domain contracts.

## Inputs

User-entered title, plain-text body, comma-separated tags, archive/restore action, and the optional `include archived` view setting.

## Outputs

Validated read-only `IdeaNote` values for display. There is no algorithm, simulation, risk, accounting, or trading output.

## Dependencies

The model/service/store use only the Python standard library. The presentation panel additionally uses PySide6 and the notebook's own public objects. It must not import other QuantTrade business modules or `AlgorithmControlController`.

## Side effects

Production composition persists notes at `runtime/algorithm_control/idea_notes.json`. The ignored file is separate from component state, Factor/Decision definitions, Backtesting results, Market History SQLite, Portfolio Accounting, and any future execution state.

## Failure modes

- Empty title/body, invalid status, naive timestamps, or update time before creation: rejected with `ValueError`; nothing is saved.
- Unknown note identity: rejected with `KeyError`.
- Invalid JSON or unsupported schema version: loading fails visibly; the file is not silently rewritten.
- File-system write failure: propagated to the GUI error boundary; no algorithm or trading workflow is resumed or approved.

## Configuration

No product configuration, financial default, algorithm setting, trading permission, or environment flag is added. The persistence path is supplied by the Algorithm Control composition root.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/algorithm_control/test_idea_notebook.py tests/architecture/test_algorithm_control_boundaries.py
```

Tests cover create/update/persistence/archive/restore, invalid input, the passive GUI workflow, and prohibited business-module dependencies. They use temporary files and no network or account.

## Known limitations

- Plain text and simple tags only; no rich text, attachment, search, export, sync, collaboration, encryption, or proposal conversion.
- One local JSON file is intended for a single local application process, not concurrent multi-process editing.
- Archived notes remain in local history and are restored explicitly; deletion is intentionally not exposed in phase one.
