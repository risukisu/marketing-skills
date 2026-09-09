# GA4 MCP Query Reference for SEO Reports

This file contains the exact GA4 MCP tool calls needed for each section of the SEO report.

**IMPORTANT:** Despite the tool documentation saying to use snake_case (protobuf format), the API actually requires **camelCase** field names for dimensions and metrics. For example, use `pagePathPlusQueryString` NOT `pagePathPlusQueryString`. The snake_case versions return a 400 error. All examples below use the correct camelCase format.

## Table of Contents

1. [Setup: Discover Property ID](#setup)
2. [Organic Traffic Overview](#organic-traffic)
3. [Landing Page Performance](#landing-pages)
4. [Content Engagement Signals](#engagement)
5. [Device Breakdown](#devices)
6. [New vs Returning Users](#user-types)
7. [Top Organic Queries (if GSC available)](#search-queries)
8. [Period Comparison](#comparison)
9. [Common Dimensions & Metrics](#reference)

---

## Setup: Discover Property ID {#setup}

Before running reports, identify the GA4 property:

```
Tool: mcp__analytics-mcp__get_account_summaries
Parameters: {}
```

Then get property details:

```
Tool: mcp__analytics-mcp__get_property_details
Parameters: { "property_id": "<ID from above>" }
```

---

## Organic Traffic Overview {#organic-traffic}

### Total organic sessions (last 90 days)

```json
{
  "property_id": "<ID>",
  "date_ranges": [
    { "start_date": "90daysAgo", "end_date": "today" }
  ],
  "dimensions": ["sessionDefaultChannelGroup"],
  "metrics": ["sessions", "totalUsers", "newUsers", "engagementRate", "averageSessionDuration"],
  "dimension_filter": {
    "filter": {
      "field_name": "sessionDefaultChannelGroup",
      "string_filter": {
        "match_type": "EXACT",
        "value": "Organic Search"
      }
    }
  }
}
```

### Organic traffic by week (trend)

```json
{
  "property_id": "<ID>",
  "date_ranges": [
    { "start_date": "90daysAgo", "end_date": "today" }
  ],
  "dimensions": ["week", "sessionDefaultChannelGroup"],
  "metrics": ["sessions", "totalUsers"],
  "dimension_filter": {
    "filter": {
      "field_name": "sessionDefaultChannelGroup",
      "string_filter": {
        "match_type": "EXACT",
        "value": "Organic Search"
      }
    }
  },
  "order_bys": [{ "dimension": { "dimensionName": "week" } }]
}
```

### Organic traffic by source (Google vs Bing vs others)

```json
{
  "property_id": "<ID>",
  "date_ranges": [
    { "start_date": "90daysAgo", "end_date": "today" }
  ],
  "dimensions": ["sessionSource"],
  "metrics": ["sessions", "totalUsers", "engagementRate"],
  "dimension_filter": {
    "filter": {
      "field_name": "sessionDefaultChannelGroup",
      "string_filter": {
        "match_type": "EXACT",
        "value": "Organic Search"
      }
    }
  },
  "order_bys": [{ "metric": { "metricName": "sessions" }, "desc": true }]
}
```

---

## Landing Page Performance {#landing-pages}

### Top landing pages from organic search

```json
{
  "property_id": "<ID>",
  "date_ranges": [
    { "start_date": "90daysAgo", "end_date": "today" }
  ],
  "dimensions": ["landingPagePlusQueryString"],
  "metrics": [
    "sessions",
    "totalUsers",
    "engagementRate",
    "averageSessionDuration",
    "conversions",
    "bounceRate"
  ],
  "dimension_filter": {
    "filter": {
      "field_name": "sessionDefaultChannelGroup",
      "string_filter": {
        "match_type": "EXACT",
        "value": "Organic Search"
      }
    }
  },
  "order_bys": [{ "metric": { "metricName": "sessions" }, "desc": true }],
  "limit": 30
}
```

### Pages with high traffic but low engagement (content quality red flags)

Run the top landing pages query above, then filter in analysis for:
- Pages where `engagementRate` < 0.40 AND `sessions` > threshold (top 25% of traffic)
- Pages where `bounceRate` > 0.70 AND `sessions` > threshold
- Pages where `averageSessionDuration` < 30 seconds

These signal content that attracts clicks but doesn't satisfy user intent — a key Google quality signal.

---

## Content Engagement Signals {#engagement}

### Engagement by page path (all traffic, for content quality assessment)

```json
{
  "property_id": "<ID>",
  "date_ranges": [
    { "start_date": "90daysAgo", "end_date": "today" }
  ],
  "dimensions": ["pagePathPlusQueryString"],
  "metrics": [
    "screenPageViews",
    "totalUsers",
    "engagementRate",
    "averageSessionDuration",
    "userEngagementDuration"
  ],
  "order_bys": [{ "metric": { "metricName": "screenPageViews" }, "desc": true }],
  "limit": 50
}
```

### Events that signal content satisfaction

```json
{
  "property_id": "<ID>",
  "date_ranges": [
    { "start_date": "90daysAgo", "end_date": "today" }
  ],
  "dimensions": ["eventName"],
  "metrics": ["eventCount", "totalUsers"],
  "order_bys": [{ "metric": { "metricName": "eventCount" }, "desc": true }],
  "limit": 20
}
```

Look for: scroll events, file_download, click events, form_submit — these indicate content that users find useful.

---

## Device Breakdown {#devices}

### Mobile vs Desktop organic performance

```json
{
  "property_id": "<ID>",
  "date_ranges": [
    { "start_date": "90daysAgo", "end_date": "today" }
  ],
  "dimensions": ["deviceCategory"],
  "metrics": [
    "sessions",
    "totalUsers",
    "engagementRate",
    "averageSessionDuration",
    "bounceRate"
  ],
  "dimension_filter": {
    "filter": {
      "field_name": "sessionDefaultChannelGroup",
      "string_filter": {
        "match_type": "EXACT",
        "value": "Organic Search"
      }
    }
  }
}
```

Mobile-first indexing means poor mobile engagement is a direct ranking signal. Flag if mobile engagementRate is significantly lower than desktop.

---

## New vs Returning Users {#user-types}

### Organic user loyalty

```json
{
  "property_id": "<ID>",
  "date_ranges": [
    { "start_date": "90daysAgo", "end_date": "today" }
  ],
  "dimensions": ["newVsReturning"],
  "metrics": ["sessions", "totalUsers", "engagementRate", "averageSessionDuration"],
  "dimension_filter": {
    "filter": {
      "field_name": "sessionDefaultChannelGroup",
      "string_filter": {
        "match_type": "EXACT",
        "value": "Organic Search"
      }
    }
  }
}
```

A healthy SEO presence shows some returning organic users — people who found you via search and came back directly or via brand search.

---

## Period Comparison {#comparison}

### Month-over-month organic comparison

```json
{
  "property_id": "<ID>",
  "date_ranges": [
    { "start_date": "30daysAgo", "end_date": "today" },
    { "start_date": "60daysAgo", "end_date": "31daysAgo" }
  ],
  "dimensions": ["sessionDefaultChannelGroup"],
  "metrics": ["sessions", "totalUsers", "engagementRate"],
  "dimension_filter": {
    "filter": {
      "field_name": "sessionDefaultChannelGroup",
      "string_filter": {
        "match_type": "EXACT",
        "value": "Organic Search"
      }
    }
  }
}
```

### Year-over-year (if sufficient data)

Same structure, but with:
```json
"date_ranges": [
  { "start_date": "30daysAgo", "end_date": "today" },
  { "start_date": "395daysAgo", "end_date": "366daysAgo" }
]
```

---

## Common Dimensions & Metrics Reference {#reference}

### Useful dimensions for SEO analysis
| Dimension | Description |
|-----------|-------------|
| `sessionDefaultChannelGroup` | Channel grouping (Organic Search, Direct, etc.) |
| `sessionSource` | Traffic source (google, bing, etc.) |
| `sessionMedium` | Traffic medium (organic, cpc, etc.) |
| `landingPagePlusQueryString` | First page of session with query params |
| `pagePathPlusQueryString` | Page path with query params |
| `deviceCategory` | desktop, mobile, tablet |
| `country` | User country |
| `newVsReturning` | New visitor vs returning |
| `week` | ISO week for trend analysis |
| `date` | Date for daily granularity |
| `pageReferrer` | Referring URL |
| `pageTitle` | HTML title of page |

### Useful metrics for SEO analysis
| Metric | Description |
|--------|-------------|
| `sessions` | Total sessions |
| `totalUsers` | Unique users |
| `newUsers` | First-time users |
| `engagementRate` | % of engaged sessions (>10s, conversion, or 2+ pages) |
| `averageSessionDuration` | Avg time per session |
| `bounceRate` | % single-page, non-engaged sessions |
| `screenPageViews` | Total page views |
| `conversions` | Conversion events |
| `eventCount` | Total events |
| `userEngagementDuration` | Total engagement time |

### Date range shortcuts
- `today`, `yesterday`
- `NdaysAgo` (e.g., `30daysAgo`, `90daysAgo`, `365daysAgo`)
- Explicit dates: `YYYY-MM-DD`
