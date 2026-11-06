"""Tests for the generator and helper scripts (no GCP, GitHub or ServiceNow needed)."""
import json
import re
import sys
from pathlib import Path

import hcl2
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import close_requests  # noqa: E402
import new_project  # noqa: E402
import servicenow  # noqa: E402
import teams_notify  # noqa: E402

DEFAULTS = json.loads((ROOT / "config" / "project-defaults.json").read_text())
REQ = {"ritm": "RITM0012345", "sctask": "SCTASK0012345", "project_name": "rme-orders-nonprod",
       "project_id": "syy-rme-orders-nonprod", "app_team_name": "RME Order Management",
       "support_group": "RME Support", "technical_owner": "tom.lee@corp.com",
       "budget_approver": "ann.wu@corp.com", "requested_for": "jane.doe@corp.com"}
GCP_ID = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
GCP_LABEL = re.compile(r"^[a-z0-9_-]{0,63}$")


def _clean(x):
    """Make python-hcl2 output the same across versions (see aws-account-vending)."""
    if isinstance(x, list):
        return _clean(x[0]) if len(x) == 1 else [_clean(i) for i in x]
    if isinstance(x, dict):
        return {_clean(k): _clean(v) for k, v in x.items() if not str(k).startswith("__")}
    if isinstance(x, str) and len(x) >= 2 and x[0] == x[-1] == '"':
        return x[1:-1]
    return x


def test_creates_valid_terraform(tmp_path):
    r = new_project.create(REQ, tf_dir=tmp_path, defaults=DEFAULTS)
    assert r["status"] == "created" and r["branch"] == "project/RITM0012345-syy-rme-orders-nonprod"
    tf = _clean(hcl2.loads((tmp_path / "project_syy-rme-orders-nonprod.tf").read_text()))
    module = tf["module"]["project_syy_rme_orders_nonprod"]
    assert module["source"] == "./modules/gcp-project"
    assert module["project_id"] == "syy-rme-orders-nonprod"
    assert module["name"] == "rme-orders-nonprod"
    assert module["labels"]["technical_platformowner"] == "tom_lee_corp_com"
    assert module["labels"]["technical_applicationname"] == "rme_order_management"
    assert module["labels"]["servicenow_ritm"] == "ritm0012345"
    assert all(GCP_LABEL.match(v) for v in module["labels"].values())
    assert "project_syy_rme_orders_nonprod_number" in tf["output"]


def test_project_id_is_made_from_the_name_when_missing(tmp_path):
    r = new_project.create({**REQ, "project_id": "", "project_name": "Payments API"},
                           tf_dir=tmp_path, defaults=DEFAULTS)
    assert r["project_id"] == "syy-payments-api" and GCP_ID.match(r["project_id"])


def test_project_id_must_match_the_name(tmp_path):
    with pytest.raises(new_project.RequestError, match="doesn't match"):
        new_project.create({**REQ, "project_id": "syy-something-else"}, tf_dir=tmp_path, defaults=DEFAULTS)
    assert list(tmp_path.iterdir()) == []


def test_rerun_for_same_ritm_is_safe(tmp_path):
    new_project.create(REQ, tf_dir=tmp_path, defaults=DEFAULTS)
    assert new_project.create(REQ, tf_dir=tmp_path, defaults=DEFAULTS)["status"] == "exists"


def test_same_id_from_another_request_is_refused(tmp_path):
    new_project.create(REQ, tf_dir=tmp_path, defaults=DEFAULTS)
    with pytest.raises(new_project.RequestError, match="already exists"):
        new_project.create({**REQ, "ritm": "RITM0099999"}, tf_dir=tmp_path, defaults=DEFAULTS)


@pytest.mark.parametrize("field, value, message", [
    ("project_name", "GCP", "too generic"),
    ("project_name", "ab", "3-26"),
    ("project_name", "x" * 27, "3-26"),
    ("project_name", "9lives", "3-26"),
    ("project_name", "syy-payments", "must not start"),
    ("project_name", "my-google-app", "word Google"),
    ("project_name", "ssl-gateway", "word Google"),
    ("technical_owner", "a@x.com, b@x.com", "single valid email"),
    ("ritm", "12345", "looks wrong"),
    ("app_team_name", "!!!", "label"),
    ("support_group", "", "missing"),
])
def test_bad_requests_are_rejected(tmp_path, field, value, message):
    with pytest.raises(new_project.RequestError, match=message):
        new_project.create({**REQ, field: value, "project_id": ""}, tf_dir=tmp_path, defaults=DEFAULTS)
    assert list(tmp_path.iterdir()) == []


def test_longest_name_gives_a_valid_id(tmp_path):
    r = new_project.create({**REQ, "project_name": "a" * 26, "project_id": ""}, tf_dir=tmp_path,
                           defaults=DEFAULTS)
    assert len(r["project_id"]) == 30 and GCP_ID.match(r["project_id"])


def test_short_name_uses_the_id_as_display_name(tmp_path):
    new_project.create({**REQ, "project_name": "rme", "project_id": ""}, tf_dir=tmp_path, defaults=DEFAULTS)
    tf = _clean(hcl2.loads((tmp_path / "project_syy-rme.tf").read_text()))
    assert tf["module"]["project_syy_rme"]["name"] == "syy-rme"      # display names need 4+ chars


@pytest.mark.parametrize("raw, label", [
    ("Order Management", "order_management"),
    ("tom.lee@corp.com", "tom_lee_corp_com"),
    ("RME--Support__Team", "rme-support_team"),
    ("x" * 80, "x" * 63),
])
def test_label_values(raw, label):
    assert new_project.label_value(raw) == label


def test_hcl_string_escapes_templates():
    assert new_project.hcl_string('a"b${x}%{y}\\') == '"a\\"b$${x}%%{y}\\\\"'


def test_pr_body_markers_round_trip(tmp_path):
    r = new_project.create(REQ, tf_dir=tmp_path, defaults=DEFAULTS)
    assert close_requests.markers(r["body"]) == {"ritm": "RITM0012345", "sctask": "SCTASK0012345",
                                                 "project": "syy-rme-orders-nonprod"}


def test_close_requests_finds_project_number(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(close_requests.subprocess, "run", lambda cmd, check: calls.append(cmd))
    outputs = tmp_path / "outputs.json"
    outputs.write_text(json.dumps({"project_syy_rme_orders_nonprod_number": {"value": "123456789012"}}))
    body = new_project.pr_body(new_project.validate(REQ), "terraform/x.tf")
    prs = [{"body": body, "html_url": "https://github.com/o/r/pull/7"}, {"body": "unrelated PR"}]
    close_requests.main(["--sha", "abc", "--outputs", str(outputs)], prs=prs)
    sn = next(c for c in calls if c[1].endswith("servicenow.py"))
    assert sn[2:5] == ["close", "--sctask", "SCTASK0012345"] and "123456789012" in sn[-1]
    assert "syy-rme-orders-nonprod" in sn[-1]
    assert any(c[1].endswith("teams_notify.py") for c in calls)


def test_close_requests_practice_mode_needs_no_outputs(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(close_requests.subprocess, "run", lambda cmd, check: calls.append(cmd))
    outputs = tmp_path / "outputs.json"
    outputs.write_text("{}")
    body = new_project.pr_body(new_project.validate(REQ), "terraform/x.tf")
    close_requests.main(["--sha", "abc", "--outputs", str(outputs), "--practice"],
                        prs=[{"body": body, "html_url": "https://github.com/u/r/pull/1"}])
    sn = next(c for c in calls if c[1].endswith("servicenow.py"))
    assert "practice mode, no GCP" in sn[-1]


def test_teams_card_shape():
    c = teams_notify.card("Review needed", facts=[("Author", "bot")], url="https://x", button="Review")
    content = c["attachments"][0]["content"]
    assert content["type"] == "AdaptiveCard" and content["actions"][0]["url"] == "https://x"


def test_scripts_skip_quietly_without_secrets(monkeypatch, capsys):
    for k in ("SN_INSTANCE", "SN_USERNAME", "SN_PASSWORD", "TEAMS_WEBHOOK_URL"):
        monkeypatch.delenv(k, raising=False)
    assert servicenow.main(["note", "--sctask", "SCTASK0012345", "--text", "hi"]) == 0
    assert teams_notify.main(["--title", "hi"]) == 0
    assert capsys.readouterr().out.count("::warning::") == 2


def test_cli_from_env(monkeypatch, tmp_path):
    for k, v in REQ.items():
        monkeypatch.setenv("REQ_" + k.upper(), v)
    monkeypatch.setattr(new_project, "TF_DIR", tmp_path)
    monkeypatch.chdir(tmp_path)
    assert new_project.main(["--from-env"]) == 0
    assert (tmp_path / "project_syy-rme-orders-nonprod.tf").exists() and (tmp_path / "pr_body.md").exists()
