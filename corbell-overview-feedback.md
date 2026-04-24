# Corbell Overview And Feedback

## What Corbell Is

Corbell is a local-first architecture intelligence tool for backend teams working across multiple repositories.

Its main job is to turn a set of repos and design docs into a usable engineering context layer:

- a service and method graph stored in SQLite
- a semantic embedding index over code and docs
- generated technical design specs from PRDs or feature descriptions
- review and decomposition tooling for those specs
- export surfaces for tools like Linear and Jira
- an MCP server so external AI tools can query the same architecture context

In practical terms, it is trying to solve this problem:

> "We have a multi-repo system, the architectural knowledge is fragmented, and we want new specs and AI-assisted implementation to reflect how the system actually works."

## Main Goal

The application's main goal is to reduce architectural drift when planning new work.

Instead of asking an LLM to write a design doc from a PRD in a vacuum, Corbell builds context from:

- configured repositories in `corbell-data/workspace.yaml`
- scanned service dependencies and method relationships
- code embeddings for semantic retrieval
- prior design docs, ADRs, and RFCs
- explicit constraints captured in specs

That context is then fed into spec generation, review, decomposition, export, and MCP access.

## How It Works

### 1. Workspace configuration

The user initializes a workspace and lists services in `corbell-data/workspace.yaml`.

Corbell resolves service repo paths, chooses storage backends, defines the spec output folder, and selects the LLM provider. This is handled in `corbell/core/workspace.py`.

### 2. Graph build

`corbell graph build --methods` scans each configured repository and creates a graph in SQLite.

The graph builder looks for:

- service entrypoint patterns
- database usage patterns
- queue usage patterns
- HTTP call patterns
- optional method-level structure

This logic lives mainly in `corbell/core/graph/builder.py`, with storage handled by the graph store implementation.

### 3. Embeddings build

`corbell embeddings build` walks the repos, extracts code chunks, embeds them, and stores them for semantic retrieval.

The extractor in `corbell/core/embeddings/extractor.py` uses:

- Python AST extraction for Python functions, classes, and methods
- generic overlapping line-based chunks for most other file types

This embedding store is then used heavily during spec generation and architecture context retrieval.

### 4. Document pattern learning

`corbell docs scan` and `corbell docs learn` find ADRs, RFCs, design docs, and related markdown, then extract reusable decisions and patterns.

This allows Corbell to inject a team's historical design preferences into future specs instead of treating every feature as a blank slate.

### 5. Spec generation

This is the center of the product.

`corbell spec new` takes a PRD or inline feature description and:

- generates semantic search queries from the PRD
- auto-discovers relevant services with embeddings
- pulls graph context
- retrieves real code snippets
- injects learned design patterns
- asks the configured LLM to produce a full technical design doc

The core implementation is in `corbell/core/spec/generator.py`.

There is also an `--existing` mode that describes the current system even without a PRD.

### 6. Review and decomposition

Once a spec exists:

- `corbell spec review` checks graph consistency and required structure, then writes a `.review.md` sidecar
- `corbell spec approve` marks it approved
- `corbell spec decompose` converts an approved spec into parallel task tracks in YAML

This is a practical bridge from architecture planning into execution.

### 7. Export and MCP

Corbell can export tasks to tools like Linear and Jira, and it can also expose its context through MCP so IDE agents or other AI tools can query the architecture graph and semantic index directly.

The MCP surface in `corbell/core/mcp/server.py` exposes tools such as:

- `graph_query`
- `get_architecture_context`
- `code_search`
- `list_services`

### 8. Local UI

`corbell ui serve` launches a lightweight local UI that reads directly from the SQLite store and presents a graph browser with service details, dependencies, flows, and constraints.

The UI server is implemented in `corbell/core/ui/server.py`.

## What The Product Is Really Trying To Be

Corbell is not just a diagramming tool and not just a prompt wrapper around an LLM.

It is trying to be a local architecture operating layer for engineering teams:

- part repo scanner
- part architecture graph
- part semantic retrieval system
- part design-doc generator
- part AI context provider

The strongest idea in the product is that specs should be generated from real code and real historical decisions, not just from PRD text.

## What I Think It Does Well

### 1. The core product idea is strong

The repo has a coherent thesis: use the existing codebase and design history to improve specs and downstream engineering execution.

That is materially better than "generate a design doc from a prompt" tools.

### 2. The workflow is end-to-end

The CLI covers the full chain:

- initialize workspace
- build architecture context
- generate spec
- review it
- decompose it
- export tasks
- expose the same context to AI clients over MCP

That makes the product feel like a system instead of a disconnected collection of features.

### 3. Local-first is the right default

Using local repos plus a local SQLite store is a very good fit for the problem.

It lowers setup friction and keeps the tool usable without requiring a hosted platform.

### 4. There is a useful fallback story

If no LLM is configured, Corbell still produces template-mode outputs. That makes the tool more robust than systems that simply fail closed when credentials are missing.

### 5. The MCP angle is strategically smart

Exposing architecture and code-search context to Cursor, Claude Desktop, or similar tools makes the product more useful than a standalone CLI.

That is probably one of the most valuable long-term features in the repo.

## Where I Think The Product Is Weak Or Risky

### 1. A lot of the graph extraction is heuristic

The graph builder relies heavily on string-pattern detection for service types, databases, queues, and HTTP calls.

That is fast and practical, but it will produce false positives and false negatives in real production codebases, especially if teams use wrappers, internal frameworks, unconventional layouts, or generated code.

This does not make the feature bad, but it does mean the graph should be treated as "useful inferred context," not guaranteed truth.

### 2. Non-Python embedding extraction is shallow

The embedding extractor is much richer for Python than for other languages.

For Python, it uses AST-based extraction of functions and classes. For many other languages, it falls back to generic overlapping text blocks.

That means semantic retrieval quality is likely to be noticeably better in Python-heavy repos than in polyglot environments, even though the product is positioned as multi-language.

### 3. A lot of responsibility is concentrated in a few large files

`corbell/core/spec/generator.py` is the heart of the product, and it is doing a lot:

- prompt design
- service discovery
- graph retrieval
- embedding retrieval
- context shaping
- output generation
- template fallback behavior

That makes iteration fast in the short term, but it will get harder to reason about and extend safely if the product grows.

### 4. The UI is useful but intentionally narrow

The UI is a lightweight local browser over SQLite, which is appropriate, but it currently feels like a convenience inspection layer rather than a deeply interactive analysis environment.

That may be fine if the real product is CLI + MCP, but if the UI becomes a primary surface, it will likely need stronger filtering, graph explanation, provenance, and confidence indicators.

### 5. Trust and explainability matter here

Because Corbell is generating architecture docs and influencing execution plans, users will care a lot about:

- why a service was selected
- why a file was retrieved
- how confident the dependency graph is
- whether a claim came from code, docs, or heuristic inference

Some of that is present, but I think the product would benefit from making provenance and confidence more explicit.

## My Overall Assessment

Corbell has a real product idea, not just a demo idea.

The strongest part of the repo is that the features reinforce each other:

- graph build makes embeddings more useful
- embeddings make spec generation more grounded
- design-doc learning makes generation less generic
- review and decomposition make the output actionable
- MCP makes the same context reusable outside the CLI

That is a solid architecture for the product itself.

My main caution is accuracy and maintainability:

- accuracy, because many discovery paths are heuristic
- maintainability, because some central modules are growing into large orchestration files

## Recommended Next Improvements

If I were prioritizing the next phase of the product, I would focus on:

1. Better provenance in outputs
   - Mark whether each architectural claim came from graph inference, embedding retrieval, explicit docs, or LLM synthesis.

2. Stronger non-Python parsing
   - Improve method and symbol extraction for TypeScript, Go, Java, and other advertised languages so retrieval quality matches the product positioning.

3. Confidence and explanation in graph results
   - Show users why Corbell believes a dependency exists and what code pattern created that edge.

4. Break up `SpecGenerator`
   - Split retrieval, prompt assembly, context pruning, and output writing into smaller units so the core of the product stays maintainable.

5. Sharper UI value
   - If the UI is meant to matter, make it a decision-support surface rather than just a graph viewer.

## Bottom Line

Corbell's main goal is to help engineering teams generate architecture-aware technical design documents and downstream execution artifacts from real codebase context.

It already does that in a meaningful way.

The repo is strongest where it treats architecture as retrievable local context rather than as a static document.

Its biggest risks are inference quality in heterogeneous codebases and the growing complexity of its core orchestration logic.
