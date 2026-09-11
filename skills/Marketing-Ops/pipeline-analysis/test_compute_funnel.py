# test_compute_funnel.py — stdlib test runner (pytest not installed in workspace Python)
# Run: $CLAUDE_SYSTEM/tools/python/python.exe test_compute_funnel.py
import os, sys
import compute_funnel as cf

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "calibration.json")
_FX = cf.load(FIX)            # load() also applies the fixture's `crm` block to the module
NB = _FX["funnels"][0]        # New Business  (client config lives in the fixture, not the engine)
AM = _FX["funnels"][1]        # Account Management


def test_helpers():
    assert cf.ym("2026-04-15T10:19:21Z") == "2026-04"
    assert cf.ym(None) is None
    assert cf.days("2026-02-05", "2026-02-19") == 14
    assert cf.days("2026-02-05", None) is None
    p = {"start": "2026-01-01", "end": "2026-06-30"}
    assert cf.in_period("2026-04-15T00:00:00Z", p) is True
    assert cf.in_period("2025-09-01", p) is False


def test_fixture_loads():
    data = cf.load(FIX)
    assert len(data["deals"]) == 10 and len(data["tickets"]) == 6


def test_classify_excludes():
    data = cf.load(FIX)
    p, mx = data["period"], data["manual_excludes"]
    by_id = {d["id"]: d for d in data["deals"]}
    assert cf.classify_deal(by_id["d_nb_won"], NB, p, mx) == (True, None)
    assert cf.classify_deal(by_id["d_renewal"], NB, p, mx)[1] == "renewal/existing-business"
    assert cf.classify_deal(by_id["d_prior"], NB, p, mx)[1] == "createdate outside period"
    assert cf.classify_deal(by_id["d_sub"], NB, p, mx)[1] == "sub-deal (manual)"
    # AM keeps renewals (exclude_renewals False) and ignores NB deals
    assert cf.classify_deal(by_id["d_am_won"], AM, p, mx) == (True, None)
    assert cf.classify_deal(by_id["d_nb_won"], AM, p, mx)[1] == "other funnel"


def test_reached_sql():
    by_id = {d["id"]: d for d in cf.load(FIX)["deals"]}
    assert cf.reached_sql(by_id["d_nb_won"], NB) is True       # stage closedwon in sql_plus
    assert cf.reached_sql(by_id["d_nb_lost"], NB) is True      # lost, but sql_entry present
    assert cf.reached_sql(by_id["d_nb_flight"], NB) is False   # MQL stage, no sql_entry
    assert cf.reached_sql(by_id["d_am_prospect"], AM) is True  # prospect stage but sql_entry present


def test_nb_cohorts_and_funnel():
    data = cf.load(FIX)
    coh = cf.mql_cohorts(data, NB)
    assert coh["by_month"] == {"2026-01": 1, "2026-02": 2, "2026-04": 1}
    assert sorted(d["id"] for d in coh["included"]) == ["d_cross", "d_nb_flight", "d_nb_lost", "d_nb_won"]
    f = cf.funnel_outcomes(data, NB)
    assert f["mql"] == 4
    assert f["reached_sql"] == 3                    # won, lost(sql_entry), cross
    assert f["won"] == 1 and f["lost"] == 1         # 910000042 counted as lost (cross-pipeline)
    assert f["revenue_won"] == 50000 and f["revenue_lost"] == 200000
    assert f["in_flight"] == 2 and f["open_pipeline"] == 250000   # flight 150k + cross 100k
    assert f["win_rate"] == 0.5


def test_am_cohorts_and_funnel():
    data = cf.load(FIX)
    coh = cf.mql_cohorts(data, AM)
    assert coh["by_month"] == {"2026-02": 1, "2026-03": 1, "2026-04": 1}
    f = cf.funnel_outcomes(data, AM)
    assert f["mql"] == 3
    assert f["reached_sql"] == 2                    # am_won + am_prospect
    assert f["won"] == 1 and f["lost"] == 0
    assert f["revenue_won"] == 195540
    assert f["open_pipeline"] == 262000             # flight 92k + prospect 170k


def test_velocity():
    data = cf.load(FIX)
    v = cf.velocity(data, NB)
    # ticket->MQL: won 14, flight 2, cross 67 (lost has no ticket_createdate) -> [2,14,67] median 14
    assert v["ticket_to_mql"]["n"] == 3 and v["ticket_to_mql"]["median"] == 14
    # mql->sql: won 10, cross 44, lost 0 -> [0,10,44] median 10
    assert v["mql_to_sql"]["n"] == 3 and v["mql_to_sql"]["median"] == 10
    assert v["sql_to_won"]["n"] == 1 and v["sql_to_won"]["median"] == 31
    vam = cf.velocity(data, AM)
    assert vam["ticket_to_mql"]["n"] == 0           # AM deals have no originating lead tickets
    assert vam["sql_to_won"]["median"] == 19        # am_won 2026-04-16 -> 2026-05-05


def test_ticket_side_split():
    data = cf.load(FIX)
    cnb = cf.ticket_cohorts(data, NB)
    assert cnb["2026-02"] == {"created": 1, "mql": 1, "prospect": 0, "closed": 0, "open": 0}
    assert cnb["2026-03"]["closed"] == 1 and cnb["2026-06"]["open"] == 1
    cam = cf.ticket_cohorts(data, AM)
    assert cam["2026-02"]["mql"] == 1 and cam["2026-04"]["open"] == 1
    snb = cf.sources(data, NB)
    assert snb["Inbound"]["tickets"] == 2 and snb["Inbound"]["mql"] == 1 and snb["Inbound"]["qualified"] == 2
    assert "Cross-sell" not in snb                  # AM source must not leak into NB


def test_flags():
    data = cf.load(FIX)
    fl = cf.flags(data, NB)
    types = {f["type"] for f in fl}
    assert "renewal_excluded" in types and "manual_subdeal" in types
    assert any(f["type"] == "prior_period_reentry" and f["id"] == "d_prior" for f in fl)
    assert any(f["type"] == "cross_period_lead" and f["id"] == "d_cross" for f in fl)
    assert cf.flags(data, AM) == []                 # AM fixture has no exclusions/flags


def test_conversions_and_analyze():
    data = cf.load(FIX)
    a = cf.analyze(data)
    assert set(a["funnels"]) == {"nb", "am"}
    cnb = a["funnels"]["nb"]["conversions"]
    assert cnb["ticket_to_mql"] == 0.25     # 1 MQL-stage of 4 NB tickets
    assert cnb["mql_to_sql"] == 0.75        # 3 of 4
    assert cnb["sql_to_won"] == 0.3333      # 1 of 3
    cam = a["funnels"]["am"]["conversions"]
    assert cam["mql_to_sql"] == 0.6667      # 2 of 3
    assert cam["sql_to_won"] == 0.5         # 1 of 2


def test_map_reason():
    assert cf.map_reason("Rates too high")[0] == "E"
    assert cf.map_reason("In-house") == ("D", "Product/Strategy")
    assert cf.map_reason("Budget too small")[0] == "F"
    assert cf.map_reason("Not responsive")[0] == "C"
    assert cf.map_reason("Other reason") == ("Unattributed", None)
    assert cf.map_reason(None) == ("Unattributed", None)
    assert cf.map_reason("") == ("Unattributed", None)


def test_leak_events_and_pnl():
    data = cf.load(FIX)
    ev = cf.leak_events(data, NB)
    assert len(ev) == 1                      # only d_nb_lost is Lost in NB cohort
    e = ev[0]
    assert e["id"] == "d_nb_lost" and e["mode"] == "D" and e["amount"] == 200000
    assert e["gate"] == "sql+"               # d_nb_lost has sql_entry
    pnl = cf.leak_pnl(data, NB)
    assert pnl["D"]["count"] == 1 and pnl["D"]["eur"] == 200000 and pnl["D"]["owner"] == "Product/Strategy"
    assert cf.leak_pnl(data, AM) == {}       # AM fixture has no lost deals


def test_flow_gates():
    data = cf.load(FIX)
    fg = {g["gate"]: g for g in cf.flow_gates(data, NB)}
    # cohort: d_nb_won (won->Close), d_nb_flight (Opportunity only), d_nb_lost (SQL, lost), d_cross (SQL, open)
    assert fg["Opportunity"]["reached"] == 4
    assert fg["SQL"]["reached"] == 3            # won, lost, cross reached SQL
    assert fg["Proposal"]["reached"] == 1       # only the won deal (counted through all gates)
    assert fg["Negotiation"]["reached"] == 1
    assert fg["Close"]["reached"] == 1          # only the won deal reaches Close (lost leaked earlier)
    assert fg["SQL"]["leaked_here"] == 1        # d_nb_lost leaked at SQL
    # reached must be monotonic non-increasing across the spine
    reached_seq = [g["reached"] for g in cf.flow_gates(data, NB)]
    assert reached_seq == sorted(reached_seq, reverse=True)
    assert cf.deepest_gate({"id": "x"}, NB) == "Opportunity"


def test_accept_gate():
    data = cf.load(FIX)
    ag = cf.accept_gate(data, NB)
    # NB tickets: t_nb1 MQL(accept), t_nb2 Prospect(accept), t_nb3 Closed(reject), t_nb4 New(pending)
    assert ag["leads"] == 4 and ag["accepted"] == 2 and ag["rejected"] == 1 and ag["pending"] == 1
    assert ag["accept_rate"] == 0.5 and ag["reject_rate"] == 0.25
    assert ag["by_source"]["Inbound"]["accepted"] == 2
    assert cf.accept_gate(data, AM) is None       # AM enters at Opportunity


def test_execution_flags():
    data = cf.load(FIX)
    ef = cf.execution_flags(data, NB, silent_days=30)
    # d_nb_flight: open (appointmentscheduled), last entry 2026-04-10, period end 2026-06-30 -> >30d silent
    assert any(x["id"] == "d_nb_flight" for x in ef["went_silent"])
    # d_nb_lost has loss_reason "In-house" (mode D, not Unattributed) -> not unexplained
    assert all(x["id"] != "d_nb_lost" for x in ef["unexplained_losses"])
    assert cf.execution_flags(data, AM) is None


def test_throughput_two_lens():
    data = cf.load(FIX)
    tp = cf.throughput(data, NB)
    # d_cross: created 2026-02 (MQL), sql_entry 2026-04 (SQL) -> different months
    assert tp["mql_created"].get("2026-02") == 2      # d_nb_won + d_cross created Feb
    assert tp["sql_converted"].get("2026-04") == 1    # d_cross first SQL-entry lands in April (throughput)
    # meanwhile the cohort lens counts d_cross's conversion in its Feb MQL cohort:
    conv = cf.conversions(data, NB)
    assert conv["mql_to_sql_n"] == (3, 4)             # cohort-anchored, unchanged


def test_resolve_targets():
    tobj = cf.load(os.path.join(os.path.dirname(__file__), "fixtures", "targets_test.json"))
    # period ending Jun -> only the Jan-effective "orig" applies
    assert cf.resolve_targets(tobj, "2026-06-30")["label"] == "orig"
    # period ending Aug -> the Jul-effective "reset" is now the latest applicable
    assert cf.resolve_targets(tobj, "2026-08-31")["label"] == "reset"
    # explicit revision override
    assert cf.resolve_targets(tobj, "2026-12-31", "orig")["won_eur_nb"] == 1000000
    # unknown label errors
    try:
        cf.resolve_targets(tobj, "2026-12-31", "nope"); assert False
    except ValueError:
        pass
    # no revision applies yet
    assert cf.resolve_targets(tobj, "2025-06-30") is None


def test_throughput_vs_target():
    data = cf.load(FIX)
    tp = cf.throughput(data, NB)
    tobj = cf.load(os.path.join(os.path.dirname(__file__), "fixtures", "targets_test.json"))
    rev = cf.resolve_targets(tobj, "2026-06-30")           # "orig": mql all 1
    tvt = cf.throughput_vs_target(tp, rev)
    feb = next(r for r in tvt["mql"] if r["month"] == "2026-02")
    assert feb["target"] == 1 and feb["actual"] == 2       # 2 MQLs created Feb vs target 1
    assert len(tvt["mql"]) == 12
    assert cf.throughput_vs_target(tp, None) is None


def test_reverse_funnel():
    data = cf.load(FIX)
    ad = cf.avg_won_deal_size(data["deals"], NB)
    assert ad["avg"] == 50000 and ad["n"] == 1 and ad["low_confidence"] is True   # only d_nb_won
    tobj = {"revisions": [{"label": "t", "effective_from": "2026-01-01",
                            "mql": None, "sql": None, "leads": None,
                            "won_eur_nb": 2500000, "won_eur_am": None}]}
    rev = cf.resolve_targets(tobj, "2026-06-30")
    rf = cf.reverse_funnel(data, NB, rev)
    # rates: sql_to_won 0.3333, mql_to_sql 0.75, ticket_to_mql 0.25; avg 50000
    # req_won=50, req_sql=150.0, req_mql=200.0, req_leads=800.0
    assert rf["required"]["won"] == 50.0
    assert rf["required"]["sql"] == 150.0
    assert rf["required"]["mql"] == 200.0
    assert rf["required"]["leads"] == 800.0
    assert rf["confidence"] == "low"
    assert cf.reverse_funnel(data, AM, rev) is None


def test_verdict_and_analyze_wiring():
    data = cf.load(FIX)
    tobj = cf.load(os.path.join(os.path.dirname(__file__), "fixtures", "targets_test.json"))
    a = cf.analyze(data, targets_obj=tobj)
    assert a["targets_revision"] == "orig"                     # period ends 2026-06-30
    nb = a["funnels"]["nb"]
    assert "flow_gates" in nb and "leak_pnl" in nb and "reverse_funnel" in nb
    assert "throughput" in nb and "throughput" in a["funnels"]["am"]
    assert nb["verdict"]["primary_constraint"]["mode"] == "A"  # 4 MQLs vs required 200 -> volume is the binding constraint (exercises the A/volume path)
    assert "flow_gates" not in a["funnels"]["am"]              # AM stays condensed
    # backward-compatible: analyze() with no targets still works
    a0 = cf.analyze(data)
    assert set(a0["funnels"]) == {"nb", "am"} and a0["targets_revision"] is None


def test_execution_flags_unexplained_inclusion():
    # synthetic data (not the shared fixture): one NB deal, lost with a blank/Unattributed
    # reason -> must land in unexplained_losses (the C-inference inclusion path)
    data = {
        "period": {"start": "2026-01-01", "end": "2026-06-30"},
        "deals": [{"id": "x_lost_blank", "name": "blank-reason loss", "pipeline": "default",
                   "createdate": "2026-02-01", "stage": "00000000-0000-4000-8000-00000000a002",
                   "amount_home": 40000, "mql_entry": "2026-02-01", "sql_entry": "2026-02-10",
                   "loss_reason": "Other reason"}],
        "tickets": [],
    }
    ef = cf.execution_flags(data, NB)
    ids = [x["id"] for x in ef["unexplained_losses"]]
    assert "x_lost_blank" in ids
    assert any(x["amount"] == 40000 for x in ef["unexplained_losses"])


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e!r}")
        except Exception as e:
            failed += 1
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
