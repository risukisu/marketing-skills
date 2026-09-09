#!/usr/bin/env python3
"""
LinkedIn Ads budget calculator (AdConversion "burn the pond" model).

Two modes:

  forward  - you know your audience; how much budget do you need?
             required monthly budget to reach <penetration>% of an audience
             at a given frequency and CPM.

  reverse  - you know your budget; how big an audience can you afford?
             max audience size you can saturate at a given penetration,
             frequency, and CPM for a fixed monthly budget.

Core formula (forward):
    impressions = audience * (penetration/100) * frequency
    monthly_budget = (impressions / 1000) * CPM

The model also reports a sane daily budget and the number of campaigns that
budget can actually support without diluting below the $50/day floor - because
on LinkedIn, spreading a small budget across many campaigns is the #1 way to
starve every campaign of the volume it needs to exit the learning phase.

Usage:
    python budget_calc.py forward --audience 85000 --cpm 20 --frequency 3 --penetration 80
    python budget_calc.py reverse --budget 5000 --cpm 45 --frequency 3 --penetration 80
    python budget_calc.py reverse --budget 5000            # uses defaults

Defaults reflect AdConversion starting points: CPM $45 (mid of the $20-90
typical range), frequency 3, penetration 80%.
"""

import argparse
import sys

DAYS_PER_MONTH = 30.4
DAILY_FLOOR = 50       # absolute minimum daily budget per campaign
DAILY_START = 100      # recommended starting daily budget per campaign
AUDIENCE_SWEET_SPOT = 250_000  # above this, tighten the audience further


def money(x: float) -> str:
    return f"${x:,.0f}"


def campaign_capacity(monthly_budget: float) -> str:
    daily = monthly_budget / DAYS_PER_MONTH
    at_floor = int(daily // DAILY_FLOOR)
    at_start = int(daily // DAILY_START)
    return (
        f"  Daily budget:        {money(daily)}/day "
        f"(monthly / {DAYS_PER_MONTH})\n"
        f"  Campaigns you can run: {at_start} at the {money(DAILY_START)}/day "
        f"starting point, {at_floor} at the {money(DAILY_FLOOR)}/day floor.\n"
        f"  -> Consolidate. Fewer, well-fed campaigns learn faster than many "
        f"starved ones."
    )


def forward(audience, cpm, frequency, penetration):
    pen = penetration / 100.0
    impressions = audience * pen * frequency
    monthly = (impressions / 1000.0) * cpm

    print("FORWARD: budget needed to saturate this audience")
    print("-" * 56)
    print(f"  Audience size:       {audience:,}")
    print(f"  CPM:                 {money(cpm)}")
    print(f"  Frequency:           {frequency}x")
    print(f"  Penetration target:  {penetration}%")
    print(f"  Impressions needed:  {impressions:,.0f}")
    print(f"  REQUIRED MONTHLY:    {money(monthly)}")
    print()
    print(campaign_capacity(monthly))
    print()
    if audience > AUDIENCE_SWEET_SPOT:
        print(f"  ! Audience > {AUDIENCE_SWEET_SPOT:,}. Unless it is genuinely "
              f"on-point, tighten it\n    (account list + titles) so the "
              f"impression itself stays valuable.")
    print(f"  Note: a $10 swing in CPM moves the budget a lot - CPM is the "
          f"vanity\n  metric that actually matters here. Re-run with your real "
          f"CPM once you have it.")


def reverse(budget, cpm, frequency, penetration):
    pen = penetration / 100.0
    denom = pen * frequency * (cpm / 1000.0)
    max_audience = budget / denom if denom else 0

    print("REVERSE: audience you can afford on this budget")
    print("-" * 56)
    print(f"  Monthly budget:      {money(budget)}")
    print(f"  CPM:                 {money(cpm)}")
    print(f"  Frequency:           {frequency}x")
    print(f"  Penetration target:  {penetration}%")
    print(f"  MAX AUDIENCE SIZE:   {max_audience:,.0f}")
    print()
    print(campaign_capacity(budget))
    print()
    if max_audience > AUDIENCE_SWEET_SPOT:
        print(f"  Your budget can cover a large audience, but bigger is not "
              f"better on\n  LinkedIn. Keep it under ~{AUDIENCE_SWEET_SPOT:,} "
              f"and let precision, not reach, win.")
    else:
        print(f"  This sits in the healthy zone (under {AUDIENCE_SWEET_SPOT:,}). "
              f"Build it from an\n  account list + job titles for maximum "
              f"precision.")


def main():
    p = argparse.ArgumentParser(description="LinkedIn Ads budget calculator")
    sub = p.add_subparsers(dest="mode", required=True)

    f = sub.add_parser("forward", help="audience -> required budget")
    f.add_argument("--audience", type=int, required=True)
    f.add_argument("--cpm", type=float, default=45)
    f.add_argument("--frequency", type=float, default=3)
    f.add_argument("--penetration", type=float, default=80)

    r = sub.add_parser("reverse", help="budget -> max audience")
    r.add_argument("--budget", type=float, required=True)
    r.add_argument("--cpm", type=float, default=45)
    r.add_argument("--frequency", type=float, default=3)
    r.add_argument("--penetration", type=float, default=80)

    a = p.parse_args()
    if a.mode == "forward":
        forward(a.audience, a.cpm, a.frequency, a.penetration)
    else:
        reverse(a.budget, a.cpm, a.frequency, a.penetration)


if __name__ == "__main__":
    main()
