# Source routing and fallback matrix

| Source | Primary route | Fallback | Counts as recent evidence when | Common failure |
|---|---|---|---|---|
| X | Local Grok wrapper with `--platform x` | Targeted public-web search for a known post or claim | Direct post URL and checkable publication time are present | Browser cookies absent; a restricted process cannot read the local Grok session |
| Reddit | Local Grok wrapper with `--platform reddit` | Targeted `site:reddit.com/.../comments` public-web search | Direct submission permalink and checkable date are present | Login wall, fetch block, or snippet without a permalink |
| YouTube | Strict collector over last30days and yt-dlp | Public YouTube search or public-web search | Video URL and upload date fall inside the requested window | Overlong query; older results retained by the upstream soft date fallback |
| Hacker News | Strict collector over last30days | HN search or public-web search | Direct item URL and date fall inside the window | Sparse matching results |
| Polymarket | Strict collector over last30days | Direct market page | Market is active and relevant to the research question | Keyword relevance can be weak |
| Public web | Agent web search | Direct browsing of known primary sources | Publication or update date is checkable | Reposts and marketing copy are mistaken for independent evidence |
| Douyin | Accessible public platform/browser search | Public-web discovery of a known video | Direct video page, visible date, and visible signal are available | Login wall and incomplete public metrics |
| Video accounts | Accessible public platform/browser search | Public-web discovery of a known post | Direct post or account evidence can be checked | No complete public ranking and limited public indexing |

## Status meanings

- `ok`: the route ran and returned checkable evidence.
- `degraded`: the route ran partially, or results lack direct links, dates, or visible metrics.
- `unavailable`: the route could not run after a reasonable retry.
- `not_requested`: the source was outside the requested scope.

An `ok` source may still have zero relevant recent results. State that as “searched successfully, no qualifying results found,” not as proof of absence.
