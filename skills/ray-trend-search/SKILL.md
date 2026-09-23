---
name: ray-trend-search
description: Use for recent trend research across X, Reddit, YouTube, Hacker News, Polymarket, Douyin, video accounts, and the public web, especially requests mentioning latest discussions, last N days, hot videos, community sentiment, trend checks, or topic references. Orchestrates local Grok for X and Reddit, last30days for supported indexes, and public-web verification with strict date and evidence boundaries. Do not use for stable facts, local-knowledge-base-only retrieval, or writing from already complete research.
---

# Ray Trend Search

Build a defensible recent-trend map even when individual platform connectors fail. Treat every source as a separately observable channel. Never turn a failed connector or an empty query into a claim that nobody is discussing the topic.

## Completion contract

A run is complete only when it:

1. states the requested time window and platforms;
2. reports each requested source as `ok`, `degraded`, `unavailable`, or `not_requested`;
3. uses short, source-specific queries rather than one long bilingual query everywhere;
4. keeps only items inside the requested window in the recent-results section;
5. provides direct links for material claims, or explicitly says a direct link could not be recovered;
6. separates visible facts, third-party observations, inference, and unknowns;
7. cross-checks the strongest trend claim against a primary or independent source when one exists.

## Choose a mode

- `quick`: default for topic ideation. Run one focused X search, one short YouTube/index search, and public-web verification. Add Reddit only when explicitly requested or clearly material.
- `deep`: use for reports, controversial claims, or requests naming multiple platforms. Search X and Reddit separately, recover missing Reddit permalinks, inspect primary sources, and compare results across sources.

## Workflow

### 1. Define the research target

Extract:

- the core topic;
- the exact date window, defaulting to the last 30 days;
- requested platforms;
- whether the user wants a trend map, evidence, sentiment, hot videos, or content ideas.

If the date window is longer than 30 days, use Grok and public-web search for the full period. The last30days collector accepts at most 30 days.

### 2. Probe local source readiness

Run:

```bash
python3 <skill-dir>/scripts/source_probe.py
```

Use the probe to decide which routes are available. It does not prove that a platform will return results; it only checks whether the local route exists.

Important distinctions:

- `grok_preflight_failed` inside a restricted environment is not automatically a login failure. If the local Grok command works outside that restriction, retry with the required local permission.
- A successful last30days probe does not mean every connector is usable. Read its per-source status.
- Never display credentials, cookies, tokens, or raw authorization errors to the user.

### 3. Build source-specific queries

Create separate queries before searching:

- **X:** a concise topic phrase plus the decision, complaint, release, or practice being discussed.
- **Reddit:** the product or practice name plus concrete user-language such as `production`, `failed`, `worth it`, `workflow`, or `experience`.
- **YouTube:** 3–6 words, normally one language, with no long list of synonyms.
- **Public web:** the entity plus a specific event or claim; prefer official sources for facts and targeted site search for missing platform links.
- **Douyin / video accounts:** a short Chinese keyword phrase. Treat public search results as a sample, not an official popularity ranking.

Do not send one mixed Chinese-English paragraph to all sources.

### 4. Route each source

#### X

Use the existing Grok search wrapper. Locate it in this order:

1. sibling Ray skill: `<skills-dir>/ray-multimodel/scripts/run_search.py`;
2. `~/.codex/skills/codex-grok-search/scripts/run_search.py`;
3. `~/.agents/skills/codex-grok-search/scripts/run_search.py`.

Example:

```bash
python3 <grok-wrapper> run --platform x --depth quick --since 30d "Find recent X discussions about <topic>. Return direct post links, visible dates, visible engagement, and disagreements."
```

Use `--depth deep` for higher-stakes research. Preserve the wrapper's `limitations` and `cross_checks` fields.

#### Reddit

For `deep` mode or an explicit Reddit request, run a separate Grok search:

```bash
python3 <grok-wrapper> run --platform reddit --depth deep --since 30d "Find recent Reddit discussions about <topic>. Return direct submission permalinks and explain any date uncertainty."
```

If Grok finds discussion content but cannot recover direct Reddit permalinks, use a targeted public-web query such as:

```text
site:reddit.com/r/*/comments <topic keywords>
```

Only count a Reddit item when its direct URL and date can be checked. Otherwise retain it as an unverified lead, not evidence.

#### YouTube, Hacker News, and Polymarket

Use the strict collector, which calls the existing last30days script only for supported routes and then enforces the requested date window:

```bash
python3 <skill-dir>/scripts/collect_last30.py \
  --topic "<core topic>" \
  --video-query "<short YouTube query>" \
  --days 30 \
  --mode quick \
  --output /private/tmp/ray-trend-search.json
```

The collector deliberately excludes last30days X and Reddit routes. Its `background` section contains old or undated items and must not be counted as recent activity.

#### Public web and primary sources

Use public-web search after platform discovery to:

- verify product launches, company announcements, research, and policy changes;
- recover direct Reddit links when possible;
- find independent context for a strong platform claim;
- distinguish a real trend from a small cluster of repeated posts.

For technical claims, prefer official documentation or primary research. For company claims, prefer the company's original announcement and independently reported evidence where available.

#### Douyin and video accounts

These platforms do not have a reliable local connector in this skill. When explicitly requested, use their accessible public search surfaces or browser search. Report:

- the exact keywords used;
- which engagement numbers were publicly visible;
- that the result is a public sample rather than the platform's complete or official ranking.

If access is login-walled or metrics are hidden, mark the source `degraded`; do not substitute unrelated web articles and call them platform trends.

### 5. Normalize evidence

Use these evidence levels:

1. **Direct platform evidence:** direct post/video URL, checkable date, and visible engagement when present.
2. **Primary source:** official announcement, documentation, filing, or original research.
3. **Independent report:** reputable third-party account that can be checked.
4. **Inference:** a conclusion drawn from several items; always label it as inference.

Never invent engagement values. Never treat search-result order as a popularity score.

### 6. Report the result

Use this compact structure unless the user requests another format:

1. **一句话判断** — what is actually rising, disputed, or still uncertain.
2. **来源状态** — requested source, status, evidence count, and limitation.
3. **关键发现** — 3–7 findings with date, source, direct link, visible signal, and why it matters.
4. **交叉判断** — what multiple sources agree on, where they conflict, and what may be sampling bias.
5. **可用选题** — only when requested; give a small ranked set with hook, evidence anchor, and risk.
6. **未知项** — missing links, hidden metrics, inaccessible sources, or facts that still require confirmation.

## Failure rules

- Empty X results after a failed connector mean `unavailable`, not “X has no discussion.”
- Empty Reddit results without direct permalinks mean `degraded`, not “Reddit has no discussion.”
- Old YouTube videos may be useful background, but cannot be counted inside a recent window.
- If a source is blocked by the execution environment, retry through the allowed local route before declaring it unavailable.
- If only one source supports a trend claim, call it a signal or lead, not a trend.
- If an item's date cannot be checked, move it to background or unknowns.

See [source-routing.md](references/source-routing.md) for the routing and fallback matrix.
