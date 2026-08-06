import json

from fusionhelper import telemetry


def test_record_appends_one_json_line(tmp_path):
    path = tmp_path / "t.jsonl"
    out = telemetry.record_entry(script="box.py", verdict="pass", executes=1,
                                 preflight_attempts=2, rules_fired=["R2", "R4"],
                                 notes="", path=path)
    assert out == path
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["script"] == "box.py"
    assert entry["verdict"] == "pass"
    assert entry["executes"] == 1
    assert entry["preflight_attempts"] == 2
    assert entry["rules_fired"] == ["R2", "R4"]
    assert entry["ts"].endswith("+00:00") or entry["ts"].endswith("Z")


def test_env_var_overrides_default_path(tmp_path, monkeypatch):
    target = tmp_path / "override.jsonl"
    monkeypatch.setenv("FH_TELEMETRY", str(target))
    telemetry.record_entry(script="a.py", verdict="fail", executes=3)
    assert target.is_file()


def test_summarize_math(tmp_path):
    path = tmp_path / "t.jsonl"
    telemetry.record_entry(script="a.py", verdict="pass", executes=1,
                           rules_fired=["R4"], path=path)
    telemetry.record_entry(script="b.py", verdict="pass", executes=3,
                           rules_fired=["R4", "R2"], path=path)
    telemetry.record_entry(script="c.py", verdict="abandoned", executes=5, path=path)
    s = telemetry.summarize(path)
    assert s["sessions"] == 3
    assert s["first_execute_green"] == 1
    assert s["mean_executes"] == 3.0
    assert s["rule_counts"] == {"R4": 2, "R2": 1}


def test_cli_record_then_summary(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("FH_TELEMETRY", str(tmp_path / "t.jsonl"))
    rc = telemetry.main(["record", "--script", "box.py", "--verdict", "pass",
                         "--executes", "1", "--preflight-attempts", "0",
                         "--rules-fired", "R2,R4"])
    assert rc == 0
    rc = telemetry.main(["summary"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "sessions: 1" in out
    assert "first-execute green: 1/1" in out


def test_cli_summary_with_no_file_reports_zero_sessions(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("FH_TELEMETRY", str(tmp_path / "missing.jsonl"))
    assert telemetry.main(["summary"]) == 0
    assert "sessions: 0" in capsys.readouterr().out


def test_summarize_skips_corrupt_line(tmp_path):
    path = tmp_path / "t.jsonl"
    telemetry.record_entry(script="a.py", verdict="pass", executes=1, path=path)
    telemetry.record_entry(script="b.py", verdict="pass", executes=1, path=path)
    with path.open("a", encoding="utf-8") as f:
        f.write("{not valid json, truncated\n")
    s = telemetry.summarize(path)
    assert s["sessions"] == 2
    assert s["skipped_lines"] == 1


def test_render_summary_omits_skipped_line_row_when_zero():
    rendered = telemetry._render_summary({
        "sessions": 1, "first_execute_green": 1, "mean_executes": 1.0,
        "rule_counts": {}, "skipped_lines": 0,
    })
    assert "skipped lines" not in rendered


def test_render_summary_shows_skipped_line_row_when_nonzero():
    rendered = telemetry._render_summary({
        "sessions": 2, "first_execute_green": 1, "mean_executes": 1.0,
        "rule_counts": {}, "skipped_lines": 1,
    })
    assert "skipped lines: 1" in rendered
