# Scheduling

Run `competitor-intel scan` on a recurring schedule so briefings show up on their own instead of
waiting for someone to remember to ask.

## Windows Task Scheduler (PowerShell)

```powershell
$action  = New-ScheduledTaskAction -Execute 'claude' -Argument '-p "/competitor-intel scan"' -WorkingDirectory 'C:\path\to\your\project'
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 8am
Register-ScheduledTask -TaskName 'competitor-intel weekly' -Action $action -Trigger $trigger
```

`WorkingDirectory` must be the project that holds `competitor-intel/company.md` and
`competitor-intel/competitors.md` — the skill reads them relative to the current working
directory, not relative to the skill folder.

## cron (macOS/Linux)

```
0 8 * * 1 cd /path/to/your/project && claude -p "/competitor-intel scan"
```

Same rule: `cd` into the project first so the skill finds its `competitor-intel/` folder.

## Claude Desktop

Claude Desktop's own scheduled tasks feature can run the same prompt (`/competitor-intel scan`)
against the same project. Point it at the project the same way you would a manual run.

## Cloud routines — out of scope

Cloud-hosted scheduled routines are not covered here: whether that environment can reach
arbitrary competitor websites (or is blocked, rate-limited, or run from a shared IP that trips
anti-bot defenses more often than a normal desktop connection) is unverified. Don't assume
parity with a local run until someone has actually confirmed it.
