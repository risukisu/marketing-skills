# Data connections: GA4 and Search Console MCP servers

Several skills in this library read live data instead of asking you for numbers. They do it
through two MCP (Model Context Protocol) servers that run on your machine. Neither is vendored
here; you install them once, point Claude Code at them, and the skills detect them at run time.

| Server | What it gives you | Skills that use it |
|---|---|---|
| **analytics-mcp** (Google Analytics 4) | Traffic, acquisition, engagement, conversions, funnels, realtime, property metadata | `/seo-report` (required), `/seo-google`, `/content-strategy` and `/cro` data hooks |
| **gsc** (Google Search Console) | Queries, clicks, impressions, CTR, positions, URL inspection, sitemaps, IndexNow, quick wins, cannibalization, content decay | `/seo-report` (optional), `/seo-google`, `/content-strategy` data hooks |

Every skill that can use these servers also works without them. When the tools aren't loaded, the
skill asks you for the numbers or labels them unknown; it never blocks on a missing connection.

Both servers are read-mostly. The GSC server can submit URLs and sitemaps when you give it a scope
that allows it; keep the default read-only scope unless you need that.

## Google Analytics 4: `analytics-mcp`

Google's official server: [googleanalytics/google-analytics-mcp](https://github.com/googleanalytics/google-analytics-mcp)
(Apache-2.0, Python). Published on PyPI as `analytics-mcp`.

**Versions.** This library is tested against 0.7.0 (2026-07-29), which exposes nine tools including
`run_funnel_report` and `run_conversions_report`. The 0.4 to 0.6 line fixed stdio deadlocks and a
Windows subprocess handle issue, so don't run anything older than 0.6. Release notes: <https://github.com/googleanalytics/google-analytics-mcp/releases>.

**Install**

1. Python 3.10 or newer. Then either `pipx install analytics-mcp` (upstream's recommendation) or
   `python -m pip install analytics-mcp` into a Python you control. Upgrade later with
   `pip install --upgrade analytics-mcp`.
2. In a Google Cloud project, enable the **Google Analytics Admin API** and the
   **Google Analytics Data API**.
3. Create Application Default Credentials for a Google account that can read your GA4 property,
   with the read-only scope:

   ```powershell
   gcloud auth application-default login `
     --scopes https://www.googleapis.com/auth/analytics.readonly,https://www.googleapis.com/auth/cloud-platform `
     --client-id-file client_secret.json
   ```

   The command prints the path of the saved credentials JSON. Keep that file outside any repo.
4. Add the server to the `.mcp.json` in the folder you launch Claude Code from:

   ```json
   {
     "mcpServers": {
       "analytics-mcp": {
         "type": "stdio",
         "command": "analytics-mcp",
         "env": {
           "GOOGLE_APPLICATION_CREDENTIALS": "C:/path/to/authorized_user.json",
           "GOOGLE_CLOUD_PROJECT": "your-gcp-project-id"
         }
       }
     }
   }
   ```

   On Windows, `command` can be the full path to `Scripts\analytics-mcp.exe` inside your Python
   install. If you move that Python later, reinstall the package with
   `pip install --force-reinstall --no-deps analytics-mcp` so the wrapper picks up the new path.
5. Start a new Claude Code session. You should see `mcp__analytics-mcp__*` tools. Ask
   "list my GA4 properties" to confirm.

## Google Search Console: `gsc`

Community server by Suganthan Mohanadasan:
[Suganthan-Mohanadasan/Suganthans-GSC-MCP](https://github.com/Suganthan-Mohanadasan/Suganthans-GSC-MCP)
(Apache-2.0, Node.js). Runs locally; your data goes from your machine to Google and nowhere else.

**Versions.** This library is tested against v2.5.1 (29 tools). Notable in the 2.3 to 2.5 line: a setup wizard (v2.3), image SEO tools (v2.3 and v2.5), a fix for
`sc-domain:` properties in the sitemaps tools, and updated Google client libraries that resolve a
service-account token failure on Node 22 and newer, most visible on Windows (v2.5.1). Changelog is
at the bottom of the upstream README.

**Install**

1. Node.js 18 or newer.
2. Clone and build:

   ```powershell
   git clone https://github.com/Suganthan-Mohanadasan/Suganthans-GSC-MCP.git
   cd Suganthans-GSC-MCP
   npm install
   npm run build
   ```

3. Auth, pick one:
   - **OAuth (a person's account).** In Google Cloud, create an OAuth client of type
     **Desktop app** and download the client secrets JSON. First run opens a browser sign-in and
     caches a token locally.
   - **Service account.** Create a service account, download its key, and add the service
     account's email to the Search Console property as a user.
4. Add the server to `.mcp.json`:

   ```json
   {
     "mcpServers": {
       "gsc": {
         "type": "stdio",
         "command": "node",
         "args": ["C:/path/to/Suganthans-GSC-MCP/dist/index.js"],
         "env": {
           "GSC_AUTH_MODE": "oauth",
           "GSC_OAUTH_SECRETS_FILE": "C:/path/to/client_secret.json",
           "GSC_SITE_URLS": "sc-domain:example.com,sc-domain:another.com"
         }
       }
     }
   }
   ```

   Use `GSC_SITE_URL` for one property or `GSC_SITE_URLS` for several. For a service account,
   set `GSC_AUTH_MODE` to `service_account` and `GSC_KEY_FILE` to the key path instead of the
   OAuth secrets file. `GSC_SCOPES=readonly` keeps URL submission disabled.
5. Start a new session and ask for a "site snapshot" of one property to confirm.

**Two Google accounts on one machine.** The upstream server caches its OAuth token in one fixed
location, so a second account signs in over the first. We run a small local patch that adds a
`GSC_TOKEN_PATH` environment variable to point each account at its own token file. The patch is
additive and not upstream at the time of writing; if you need it, apply the same idea (read the
token path from an environment variable, fall back to the default) or run one server per account
from separate clones.

## Keeping credentials out of the repo

Credential files, token caches, and client secrets never belong in a skills repo or any project
repo. Keep them in a folder outside version control and reference them by absolute path from
`.mcp.json`. The `.mcp.json` itself holds paths and IDs only.
