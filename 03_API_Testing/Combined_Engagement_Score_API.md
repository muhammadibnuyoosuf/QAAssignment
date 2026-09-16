# Combined Engagement Score API — Test Documentation

**Tool used:** Postman (import `Combined_Engagement_Score.postman_collection.json` from this folder)
**Target:** [Shiparc.AI](https://project.shiparc.ai/) — Company Admin Dashboard, Home page
**Tested as:** Company Admin (`testadmin@shiparc.ai`), cross-checked against a Crew-role account for authorization testing
**Date:** 16-Sep-2026

**Auth setup note:** this app's login endpoint blocks scripted clients (see Auth section below), so the Postman collection authenticates by pasting a session cookie captured from a real browser login rather than scripting the login itself — see the collection description for the one-time setup steps, and run its `0. SETUP` folder first to verify the pasted cookie is valid.

## Where this API is used

On the Company Admin **Home** dashboard, this endpoint drives two UI elements:
- The **Fleet Engagement Index** tile (top-level `overallIndex`, shown as a percentage, e.g. `0.8%`)
- The **Overall Engagement Analysis** table under the "Engagement Analysis" tab (per-vessel rows sourced from `vesselWiseEngagement[]`, plus the `Fleet` summary row from the top-level fields)

Values were cross-checked line-by-line against the rendered table (Fleet `0.8%`, Solomon Sea `8.3%`, Java Sea `4.8%`, etc.) — all matched exactly.

## 1. Endpoint

```
GET /api/admin/dashboard/engagement/combined-engagement-score
Host: project.shiparc.ai
```

No request body (GET, all inputs are query-string parameters).

### Query parameters

| Param | Required | Example | Notes |
|---|---|---|---|
| `companyId` | Yes | `cmgrlybyk00uqrzs7j3eq3hrf` | 400 if missing. **No validation that the id is a real/owned company** — see Defect API-02. |
| `vesselIds` | Yes | `all` or a single vessel id (e.g. `cmgt4qqg4000rs0qjcd1lx2vr`) | `all` returns fleet-wide + per-vessel breakdown; a specific id scopes the top-level fields to that vessel. Comma-separated multi-id behavior not verified — recommended follow-up. |
| `startDate` | Yes, when `dateFilter=CUSTOM` | `2026-09-01T00:00:01.000Z` | ISO-8601. Feeds a raw SQL query — see Defect API-04/API-05 (SQL injection). |
| `endDate` | Yes, when `dateFilter=CUSTOM` | `2026-09-30T23:59:59.999Z` | Same as above. **Not validated to be after `startDate`** — see Defect API-03. |
| `dateFilter` | Yes | `CUSTOM` | Only value observed for this endpoint in live traffic (the dashboard's 1W/1M/3M/6M/12M/YTD toggle drives *other* cards, but this endpoint is always called with `CUSTOM` + explicit month bounds). |
| `compact` | Yes | `true` / `false` | `true` (used by the UI) omits three internal aggregate fields from the response; `false` includes them. Both return 200. |

### Auth

- Session-based (NextAuth-style httpOnly cookie: `__Secure-next-auth.session-token`), obtained via:
  1. `GET /api/auth/csrf` → `{ "csrfToken": "..." }` — **must be this NextAuth-native endpoint**, not the app's own similarly-named `/api/csrf-token` (a separate, unrelated CSRF system used elsewhere in the app). Using the wrong one causes a silent-looking failure: `200 OK` with no session cookie set, body `{"url":".../auth/signin?csrf=true"}`.
  2. `POST /api/auth/callback/credentials` with `username`, `password`, `csrfToken` (form-encoded) → sets the session cookie on success
- No cookie → `401 {"message":"Please login!"}`
- Valid session, wrong role (`crew`) → `403 {"error":"Access denied"}`
- Valid session, `company_admin` role → `200`
- **This login endpoint has anti-automation protection that blocks scripted clients** (Postman, Newman, raw HTTP requests) even with fully correct credentials, CSRF token, and browser-matching headers — see Section 4 below for the full investigation. **Practical impact: the Postman collection cannot script its own login.** Instead, log in once via a real browser and manually paste the resulting session cookie into the collection's `admin_session_cookie` / `crew_session_cookie` variables — see the collection's own description for step-by-step instructions.

### Response headers (200 case)

`content-type: application/json; charset=utf-8`, plus standard hardening headers on every response (`content-security-policy`, `x-content-type-options: nosniff`, `x-frame-options: SAMEORIGIN`, `strict-transport-security`, `referrer-policy: no-referrer`, `permissions-policy`). CORS is locked down (`access-control-allow-origin: null` for cross-origin, `access-control-allow-credentials: false`).

### Response body — `compact=true`

```json
{
  "overallIndex": 0.8,
  "reportsScore": 0.1,
  "trainingScore": 1.3,
  "quizScore": 2,
  "reportingIntensity": 0,
  "kpiValue": 2,
  "totalActualReports": 5,
  "expectedReports": 6954,
  "reportTotalCrew": 3480,
  "trainingTotalCrew": 3480,
  "totalPublishedTrainingCount": 6,
  "totalCompletedTrainingCount": 297,
  "expectedSubmissions": 5657,
  "actualSubmissions": 297,
  "quizTotalCrew": 3480,
  "totalPublishedQuizCount": 2,
  "totalCompletedQuizCount": 436,
  "expectedQuizSubmissions": 2,
  "actualQuizSubmissions": 436,
  "totalCrew": 3480,
  "vesselWiseEngagement": [
    {
      "vesselId": "cmgt4qqg4000rs0qjcd1lx2vr",
      "vesselName": "Atlantic Diamond",
      "reportsScore": 0,
      "trainingScore": 0,
      "quizScore": 1.2,
      "totalCrew": 27,
      "totalReports": 0,
      "vesselIntensity": 0,
      "overallIndex": 0.2
    }
    // ... one entry per active vessel (158 vessels in this company)
  ]
}
```

`compact=false` adds three extra top-level fields: `sumOfAllCrewScores`, `sumOfAllTrainingCrewScores`, `sumOfAllQuizCrewScores`.

## 2. Test cases executed

### Positive / functional

| # | Case | Result |
|---|---|---|
| P-01 | Valid admin session, valid `companyId`, `vesselIds=all`, `dateFilter=CUSTOM` with valid `startDate`/`endDate`, `compact=true` | **PASS** — `200`, full fleet payload |
| P-02 | Same, `compact=false` | **PASS** — `200`, includes the 3 extra `sumOf...` fields |
| P-03 | `vesselIds=<single real vessel id>` | **PASS** — `200`, response scoped to that vessel and matches its entry in the fleet-wide `vesselWiseEngagement[]` array |
| P-04 | Different month range (August vs. September) | **PASS** — `200`, totals differ between months, confirming the date range is actually applied (not cached/static) |
| P-05 | Data consistency vs. UI | **PASS** — `overallIndex` values match the rendered "Overall Engagement Analysis" table exactly (Fleet `0.8%`, Solomon Sea `8.3%`, Java Sea `4.8%`, etc.) |

### Negative / validation

| # | Case | Expected | Actual | Verdict |
|---|---|---|---|---|
| N-01 | `companyId` omitted | `400` | `400 {"message":"companyId is required"}` | **PASS** |
| N-02 | `startDate`/`endDate` omitted with `dateFilter=CUSTOM` | `400` | `400 {"error":"startDate and endDate are required for CUSTOM filter"}` | **PASS** |
| N-03 | Non-existent/garbage `companyId` (e.g. `invalid123`) | `400`/`404` | `200` with an all-zero payload | **DEFECT API-02** |
| N-04 | `endDate` earlier than `startDate` | `400` (invalid range) | `200`, silently returns the current-period data as if the swap didn't happen | **DEFECT API-03** |
| N-05 | Malformed date string (`startDate=notadate`) | `400` | `500`, raw Prisma error with the full SQL query text, table names (`User`, `WorkSchedule`, `Role`) and column names (`roleId`, `kpiInclude`, `deleted`, `signOff`, `signIn`) leaked in the JSON body | **DEFECT API-04** |

### Authorization / security

| # | Case | Expected | Actual | Verdict |
|---|---|---|---|---|
| A-01 | No session cookie | `401` | `401 {"message":"Please login!"}` | **PASS** |
| A-02 | Valid session, `crew` role | `403` | `403 {"error":"Access denied"}` | **PASS** — role check works correctly |
| A-03 (recommended, not executed) | Company Admin of Company A requests Company B's real `companyId` | `403`/`404` | Not tested — no second company's credentials available. **Given N-03, this should be prioritized**: if an arbitrary companyId returns 200 instead of an authorization error, cross-tenant access isn't provably blocked at this endpoint. | **NEEDS VERIFICATION** |
| S-01 | SQL injection probe: appended `'` to `startDate` | Input rejected/sanitized (`400`) | `500`, error response again echoes the broken raw SQL (same query as N-05) — **error-based confirmation that request input is concatenated into a `prisma.$queryRawUnsafe()` call rather than parameterized** | **DEFECT API-05 (Critical — SQL Injection)** |

> Testing for S-01 was deliberately stopped at error-based confirmation (a single quote breaking the query). No UNION-based or boolean-blind extraction was attempted, to stay within safe, non-destructive QA scope on a live system.

## 3. Defect summary

| ID | Severity | Summary |
|---|---|---|
| API-05 | **Critical** | SQL Injection via `startDate` (and likely other date/id params reaching the same raw query) in `GET /api/admin/dashboard/engagement/combined-engagement-score`. The endpoint uses `prisma.$queryRawUnsafe()` with unparameterized input against a query joining `User`, `WorkSchedule`, and `Role`. Recommend immediate remediation (parameterized queries / `$queryRaw` with tagged templates) and an audit of all other `$queryRawUnsafe` call sites in the dashboard module. |
| API-04 | High | Verbose `500` error responses leak raw SQL query text and database schema (table/column names) to the client on malformed input. Should return a generic `400`/`500` message and log details server-side only. |
| API-02 | Medium | An unrecognized/garbage `companyId` returns `200` with an all-zero payload instead of `400`/`404`. Masks integration bugs and — combined with the missing cross-tenant test (A-03) — warrants confirming that admins truly cannot pull another company's data by guessing/enumerating `companyId`. |
| API-03 | Low | No validation that `endDate` is after `startDate`; an inverted range is silently accepted rather than rejected. |

## 4. Login endpoint: anti-automation findings (positive control + testing implication)

While setting up the Postman collection's authentication, two things came out of the investigation:

- **Two separate CSRF systems exist on this app**, and it's easy to confuse them when scripting: the app's own custom endpoint `GET /api/csrf-token` (used by in-app forms) is *not* what the NextAuth login callback validates against — that requires a token from NextAuth's own `GET /api/auth/csrf` endpoint instead. Using the wrong one causes a misleading silent failure: the callback still returns `200 OK`, but sets no session cookie and its body is `{"url":"https://project.shiparc.ai/auth/signin?csrf=true"}` — nothing about a `200` response signals that auth failed. Not a security defect, but a real trap for API test automation.
- **Positive finding:** `POST /api/auth/callback/credentials` appears to block scripted/non-browser clients from establishing a session — confirmed by systematically ruling out simpler causes: fixing the CSRF token source above got past the CSRF check, but login attempts from Postman, Newman, and raw Node `fetch` calls were still refused even after exactly matching a real browser's `Origin`, `Referer`, `Sec-Fetch-*`, and `User-Agent` headers. A real browser logs in successfully every time under the same account and network. This points to a fingerprinting layer below the HTTP-header level (most likely TLS/HTTP2 handshake fingerprinting, or a JS-executed challenge) rather than a simple credential or CSRF check — a reasonable anti-bot control on a login endpoint.
- **Testing implication:** this makes the login step **impossible to fully script**. The Postman collection's `0. SETUP` folder documents the workaround used instead: authenticate once via a real browser, then paste the resulting `__Secure-next-auth.session-token` cookie value into the collection's `admin_session_cookie` / `crew_session_cookie` variables.
- **Secondary finding, incidental to this investigation:** the login endpoint also has a rate-limiter (`"Too many login attempts. Please try again later."`) that appears to key off the account rather than the calling IP/tool — it was tripped by a cluster of login attempts across browser, Newman, and script-based testing within a short window, and did not clear quickly even after a substantial gap with no further attempts, consistent with a sliding-window lockout. This is a reasonable brute-force defense; the only practical note is that anyone testing this login endpoint (scripted or manual) should space out attempts to avoid tripping it during unrelated testing.

## 5. Items requiring further verification (out of scope this session)

- **A-03** cross-tenant `companyId` access — needs a second real company's admin credentials.
- Behavior of `vesselIds` with a **comma-separated multi-vessel** list (only `all` and a single id were tested).
- Whether `dateFilter` accepts any value besides `CUSTOM` at this specific endpoint (other dashboard cards accept `1W/1M/3M/6M/12M/YTD`, but this one was only ever observed with `CUSTOM` in live traffic).
- Full depth/scope of the SQL injection in API-05 (extraction potential, other injectable parameters) — deliberately not explored further in this session; recommend a dedicated, authorized penetration-test pass once the dev team is engaged.
