# Active Telemetry & Cognitive Friction Engine Component Specification

## Purpose
The Active Telemetry & Cognitive Friction Engine captures local developer editor focus time (similar to WakaTime) and projects it onto the codebase Abstract Syntax Tree (AST). By correlating active coding duration with AST node complexity, commit churn, and revert frequencies, it surfaces cognitive friction hotspots—identifying sections of the architecture that cause developer frustration, excessive context switching, or refactoring friction.

## System Dependencies
- **Editor Extension / CLI Daemon (`packages/telemetry-client`)**: Lightweight local heartbeat emitter for VS Code, JetBrains, and Neovim sending pulses every 120 seconds.
- **FastAPI (`routers/telemetry.py`)**: High-throughput heartbeat receiver, pulse deduplication, and AST node mapper.
- **Redis Time-Series Cache**: Ingestion buffer for rapid heartbeat aggregation before flushing to relational storage.
- **PostgreSQL / SQLAlchemy**: Relational storage of session intervals, file focus durations, and AST node aggregate metrics.
- **React Flow (`apps/web`)**: Focus time heatmap shader, developer flow timeline, and personal privacy-first pulse dashboard.

## Big-O Algorithmic Complexity

| Operation | Time Complexity | Space Complexity | Description |
|---|---|---|---|
| Heartbeat Ingestion & Mapping | $O(1)$ | $O(1)$ | Constant-time lookup of active file path to AST node ID in Redis cache |
| Heartbeat Interval Aggregation | $O(H)$ | $O(H)$ | Merging $H$ raw pulse events into continuous active coding intervals ($\Delta t \le 120\text{s}$) |
| Cognitive Friction Index (CFI) | $O(N)$ | $O(N)$ | Computing friction scores across $N$ modified AST nodes |
| Canvas Heatmap Shader Projection| $O(V)$ | $O(V)$ | Normalizing active minutes across visible canvas graph vertices $V$ |

## Cognitive Friction Index (CFI) Formulation

The Cognitive Friction Index ($\text{CFI}$) quantifies developer struggle within a specific codebase node $v$:

$$\text{CFI}(v) = \alpha \cdot \frac{\text{ActiveMinutes}(v)}{\max(1, \text{LOC\_Changed}(v))} + \beta \cdot \text{UndoRevertCount}(v) + \gamma \cdot \text{CyclomaticComplexity}(v)$$

Where:
- $\alpha = 0.45$: Weight for time-to-LOC ratio (excessive time spent producing few lines indicates high cognitive overhead).
- $\beta = 0.35$: Weight for editor undo/revert frequency within file $v$.
- $\gamma = 0.20$: Normalized architectural complexity weight.

## Privacy & Local-First Guarantees
- **Zero Keystroke Logging**: The telemetry engine records only file focus timestamps, cursor line offsets, and AST node IDs. No source code text or variable names are transmitted over heartbeat streams.
- **Local Masking & Anonymization**: Individual developer focus time is stored strictly locally or anonymized before aggregation into team metrics.
- **Exclusion Filters**: Developers can configure `.telemetryignore` to exempt sensitive files, personal scripts, or private branches from telemetry tracking.

