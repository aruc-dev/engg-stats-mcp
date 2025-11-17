

## Project: Engineering Stats – Live MCP Analytics

### High-level goal

Build a **set of MCP servers in Python** (GitHub, Jira, Confluence) that expose engineer activity analytics as tools.
These tools will be consumed by an **AI agent inside VS Code or Windsurf** via the MCP protocol.

For Option A there is **no database** – all metrics are computed **on the fly from the external APIs**.

---

## Tech stack

* **Language:** Python 3.10+
* **MCP:** Official **Python MCP SDK** (`mcp` package)
* **HTTP layer:** FastAPI or Flask (Copilot can choose one; FastAPI is preferred)
* **HTTP transport for MCP:** HTTP endpoint per server (e.g. `/mcp`) that the MCP server uses as its transport
* **HTTP clients:** `httpx` or `requests` to call:

  * GitHub REST API
  * Jira Cloud REST API
  * Confluence Cloud REST API
* **Config:** `.env` file + `python-dotenv` to load API keys

---

## Repo structure (Python)

Single repo with three MCP servers and shared clients:

```text
engg-stats-mcp/
  pyproject.toml        # or setup.cfg / requirements.txt
  .env

  mcp_github/
    __init__.py
    server.py

  mcp_jira/
    __init__.py
    server.py

  mcp_confluence/
    __init__.py
    server.py

  shared/
    __init__.py
    github_client.py
    jira_client.py
    confluence_client.py
    date_utils.py
```

Key requirements:

* Use `.env` + `python-dotenv` to load environment variables.
* Shared clients should wrap authentication, base URLs, pagination, and error handling.

---

## Environment variables

Each service gets its own configuration:

```env
# GitHub
GITHUB_TOKEN=...
GITHUB_MCP_PORT=4001

# Jira (Atlassian Cloud)
JIRA_BASE_URL=https://<org>.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_API_TOKEN=...
JIRA_MCP_PORT=4002

# Confluence (Atlassian Cloud)
CONFLUENCE_BASE_URL=https://<org>.atlassian.net/wiki
CONFLUENCE_EMAIL=you@company.com     # can reuse JIRA_EMAIL
CONFLUENCE_API_TOKEN=...             # can reuse JIRA_API_TOKEN
CONFLUENCE_MCP_PORT=4003
```

Each server must:

* Validate required env vars at startup.
* Log a clear, human-readable error and exit if something is missing.

---

## Common MCP server pattern (Python)

For each of `mcp_github`, `mcp_jira`, `mcp_confluence`:

* Create an MCP server object (e.g. `server = McpServer(name="github-eng-activity", version="0.1.0")`).
* Register tools using the Python SDK (e.g. decorator or `register_tool` function).
* Define input and output schemas using **pydantic** models or simple dict validation.
* Wrap the MCP server in a FastAPI (or Flask) app:

  * Expose a `POST /mcp` endpoint.
  * Use the MCP SDK’s HTTP transport to handle the request and generate the response.
* Each tool should return:

  * A **structured JSON object** (for the LLM).
  * A text payload containing a pretty-printed version of that JSON for humans.

Example shape (conceptual):

```python
result = {
    "login": login,
    "from": from_date,
    "to": to_date,
    "prsAuthored": prs_authored,
    "prsMerged": prs_merged,
    "avgPrCycleHours": avg_cycle_hours,
    "reviewsGiven": reviews_given,
    "commentsWritten": comments_written,
}

return {
    "structuredContent": result,
    "content": [
        {"type": "text", "text": json.dumps(result, indent=2)}
    ],
}
```

---

## GitHub MCP server requirements (Python)

**File:** `mcp_github/server.py`
**Client helper:** `shared/github_client.py`

### GitHub client helper

Implement a small `GitHubClient` class that:

* Accepts `token: str` as constructor arg.
* Uses `httpx` or `requests` to call `https://api.github.com`.
* Adds headers:

  * `Authorization: Bearer <token>`
  * `Accept: application/vnd.github+json`
* Provides methods to:

  * Search PRs by author + date range.
  * Fetch PR details (for merge status and timestamps).
  * Fetch PR reviews for a user.

It should handle:

* Non-2xx responses by raising informative exceptions.
* Pagination (loop until no `next` or until a safe cap like 200 items per call).

### Tool: `github_engineer_activity`

**Purpose:** Summarize PR and review activity for a GitHub user over a time range.

**Input**

```python
{
  "login": str,         # GitHub username, e.g. "alice"
  "from": str,          # ISO date string "YYYY-MM-DD"
  "to": str,            # ISO date string "YYYY-MM-DD"
  "repos": Optional[List[str]]  # optional list of "owner/repo" strings to filter
}
```

**Output**

```python
{
  "login": str,
  "from": str,
  "to": str,
  "prsAuthored": int,
  "prsMerged": int,
  "avgPrCycleHours": Optional[float],  # None if no merged PRs
  "reviewsGiven": int,
  "commentsWritten": int,
}
```

**Behavior (MVP):**

* Search PRs authored by `login` in the date range (`from..to`), optionally constrained to the provided repos.
* Count:

  * `prsAuthored`: total authored in range.
  * `prsMerged`: authored PRs that have a `merged_at` timestamp.
  * `avgPrCycleHours`: average hours between `created_at` and `merged_at` for merged PRs.
* Fetch reviews written by `login` in the same range, count:

  * `reviewsGiven`: number of review events.
  * `commentsWritten`: total review comments.

If no PRs or reviews found, return zeros and `None` for `avgPrCycleHours`.

---

## Jira MCP server requirements (Python)

**File:** `mcp_jira/server.py`
**Client helper:** `shared/jira_client.py`

### Jira client helper

Implement a `JiraClient` class that:

* Accepts `base_url`, `email`, `api_token`.
* Uses `httpx` or `requests` with basic auth for Jira Cloud.
* Provides methods:

  * `search_issues(jql: str)` – returns issues plus status history if requested.
  * Optionally helper for fetching issue transitions / changelog (for reopened detection and lead time).

### Tool: `jira_engineer_activity`

**Purpose:** Summarize Jira issue activity for a single engineer over a time range.

**Input**

```python
{
  "userEmailOrAccountId": str,
  "from": str,           # ISO date "YYYY-MM-DD"
  "to": str,             # ISO date "YYYY-MM-DD"
  "jqlExtra": Optional[str],  # extra JQL filter (project, labels, etc.)
}
```

**Output**

```python
{
  "user": str,
  "from": str,
  "to": str,
  "issuesAssigned": int,
  "issuesResolved": int,
  "reopenedCount": int,
  "avgLeadTimeHours": Optional[float],  # None if no resolved issues
}
```

**Behavior (MVP):**

* Build JQL that covers:

  * Issues assigned to the user within the `[from, to]` window, plus any `jqlExtra`.
* Define:

  * `issuesAssigned`: count of issues that had `assignee = user` and were created or assigned in that window.
  * `issuesResolved`: count of issues that transitioned to a “Done/Resolved” status in that window.
  * `reopenedCount`: issues that had a transition from Done/Resolved back to an active status.
  * `avgLeadTimeHours`: average `(resolved_at - created_at)` in hours for issues resolved in the window.

Don’t worry about perfect Jira status semantics; good-enough approximations are fine for v1.

---

## Confluence MCP server requirements (Python)

**File:** `mcp_confluence/server.py`
**Client helper:** `shared/confluence_client.py`

### Confluence client helper

Implement a `ConfluenceClient` class that:

* Accepts `base_url`, `email`, `api_token`.
* Uses `httpx` or `requests` with basic auth.
* Provides methods:

  * Search content by creator and date range.
  * List page history (for updates).
  * List comments by user and date range.

### Tool: `confluence_engineer_activity`

**Purpose:** Summarize Confluence activity for a single user over a time range.

**Input**

```python
{
  "userEmailOrAccountId": str,
  "from": str,           # ISO date
  "to": str,             # ISO date
  "spaceKey": Optional[str],  # optional Confluence space key filter
}
```

**Output**

```python
{
  "user": str,
  "from": str,
  "to": str,
  "pagesCreated": int,
  "pagesUpdated": int,
  "commentsWritten": int,
}
```

**Behavior (MVP):**

* `pagesCreated`: count of pages where the user is the creator and `created` in range (optionally filtered by space).
* `pagesUpdated`: count of edits/updates made by the user in range.
* `commentsWritten`: count of comments authored by the user in range.

Simplified approximations are fine for v1.

---

## Structured response format (all servers)

Each tool must return a response that includes:

1. **Structured JSON** – exactly matching the output schema (so the LLM can reliably parse).
2. **Human-readable text** – pretty-printed JSON for easy inspection.

Example pattern (pseudo-code):

```python
result = {...}  # dict with the fields above

return {
    "structuredContent": result,
    "content": [
        {"type": "text", "text": json.dumps(result, indent=2)}
    ]
}
```

---

## IDE integration (VS Code / Windsurf)

Assumptions:

* You will manually configure MCP clients in the IDE to point to these HTTP servers:

  * GitHub MCP:

    * Name: `github-eng-activity`
    * URL: `http://localhost:4001/mcp`
  * Jira MCP:

    * Name: `jira-eng-activity`
    * URL: `http://localhost:4002/mcp`
  * Confluence MCP:

    * Name: `confluence-eng-activity`
    * URL: `http://localhost:4003/mcp`

* The IDE agent will use natural language prompts like:

  * “Get GitHub activity for `alice` from 2025-11-01 to 2025-11-15.”
  * “Compare Jira activity for `alice@company.com` and `bob@company.com` in the last 2 weeks.”
  * “Summarize Confluence contributions for `alice` this month in the ZTA space.”

Tools must be simple and deterministic so the LLM can chain them together predictably.

---

## Non-functional requirements

* Clear logging:

  * Log external API URL, status code, and error body on failures.
* Rate limits:

  * Detect 429 responses and return a readable error message in the MCP response (don’t crash the server).
* Robust:

  * A failure in one external API call should cause that tool call to fail gracefully, without bringing down the whole MCP server process.
* No persistent storage:

  * **All metrics are computed live** from GitHub/Jira/Confluence per request.

