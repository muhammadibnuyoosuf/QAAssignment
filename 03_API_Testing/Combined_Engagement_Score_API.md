# Combined Engagement Score API — Test Documentation

**Tool used:** Postman (import `Combined_Engagement_Score.postman_collection.json` from this folder)
**Target:** [Shiparc.AI](https://project.shiparc.ai/) — Company Admin Dashboard, Home page
**Tested as:** Company Admin (`testadmin@shiparc.ai`), cross-checked against a Crew-role account for authorization testing
**Date:** 16-Sep-2026

## Where this API is used

On the Company Admin **Home** dashboard, this endpoint drives two UI elements:
- The **Fleet Engagement Index** tile (top-level `overallIndex`, shown as a percentage, e.g. `0.8%`)
- The **Overall Engagement Analysis** table under the "Engagement Analysis" tab (per-vessel rows sourced from `vesselWiseEngagement[]`, plus the `Fleet` summary row from the top-level fields)

Values were cross-checked against the rendered table (Fleet `0.8%`, Solomon Sea `8.3%`, etc.) — matched exactly.

## 1. Endpoint

```
GET /api/admin/dashboard/engagement/combined-engagement-score
Host: project.shiparc.ai
```

No request body (GET, all inputs are query-string parameters).

### Query parameters

| Param | Required | Example | Notes |
|---|---|---|---|
| `companyId` | Yes | `cmgrlybyk00uqrzs7j3eq3hrf` | Identifies the company whose fleet data to return. |
| `vesselIds` | Yes | `all` | `all` returns fleet-wide totals plus a per-vessel breakdown. |
| `startDate` | Yes, when `dateFilter=CUSTOM` | `2026-09-01T00:00:01.000Z` | ISO-8601 start of the reporting period. |
| `endDate` | Yes, when `dateFilter=CUSTOM` | `2026-09-30T23:59:59.999Z` | ISO-8601 end of the reporting period. |
| `dateFilter` | Yes | `CUSTOM` | Only value observed for this endpoint in live traffic. |
| `compact` | Yes | `true` | Trims a few internal aggregate fields from the response. |

### Auth

- Session-based (NextAuth-style httpOnly cookie: `__Secure-next-auth.session-token`), obtained by logging in via `POST /api/auth/callback/credentials` with a valid CSRF token from `GET /api/auth/csrf`.
- No cookie → `401 {"message":"Please login!"}`
- Valid session, wrong role (`crew`) → `403 {"error":"Access denied"}`
- Valid session, `company_admin` role → `200`
- For Postman testing, the session cookie is captured once from a real browser login and pasted into the collection's `admin_session_cookie` / `crew_session_cookie` variables — see the collection description for the setup steps, and run `0. SETUP` first to confirm it authenticates.

### Response headers (200 case)

`content-type: application/json; charset=utf-8`, plus standard hardening headers on every response (`content-security-policy`, `x-content-type-options: nosniff`, `x-frame-options: SAMEORIGIN`, `strict-transport-security`, `referrer-policy: no-referrer`, `permissions-policy`).

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
    // ... one entry per active vessel
  ]
}
```

## 2. Test cases executed

| # | Case | Expected | Actual | Result |
|---|---|---|---|---|
| P-01 | Valid admin session, valid `companyId`, `vesselIds=all`, `dateFilter=CUSTOM` with valid `startDate`/`endDate` | `200` with fleet engagement data | `200`, correct schema, `overallIndex` and `vesselWiseEngagement[]` present | **PASS** |
| N-01 | `companyId` omitted | `400` | `400 {"message":"companyId is required"}` | **PASS** |
| A-01 | No session cookie | `401` | `401 {"message":"Please login!"}` | **PASS** |
| A-02 | Valid session, `crew` role | `403` | `403 {"error":"Access denied"}` | **PASS** |

**Data consistency check:** the `overallIndex` and per-vessel values returned by the API were cross-checked against the "Overall Engagement Analysis" table rendered on the Home dashboard and matched exactly (Fleet `0.8%`, Solomon Sea `8.3%`, etc.), confirming the API is the actual data source for that UI section.

## 3. Recommended follow-up testing

- Additional positive coverage: `compact=false` response shape, single-vessel filtering (`vesselIds=<id>`), and different date ranges.
- Additional negative coverage: missing `startDate`/`endDate`, malformed date values, and an inverted date range (`endDate` before `startDate`).
- Cross-tenant check: a Company Admin from one company requesting another company's `companyId`, to confirm data isolation between tenants.
