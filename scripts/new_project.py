"""Turn one approved GCP project request into terraform/project_<project id>.tf (+ a PR body).

Used by .github/workflows/project-request.yml; can also be run by hand:

    python scripts/new_project.py --ritm RITM0012345 --sctask SCTASK0012345 \
        --project-name rme-orders-nonprod --app-team-name RME --support-group "RME Support" \
        --technical-owner tom.lee@corp.com --budget-approver ann.wu@corp.com \
        --requested-for jane.doe@corp.com

    python scripts/new_project.py --from-env      # values from REQ_* environment variables

The project ID is always <prefix><project name> (prefix "syy-" in config/project-defaults.json),
the same rule as the CET Agent and the ServiceNow form. If the request also carries a
project_id, it must match; a mismatch is refused rather than silently changed.

Deterministic on purpose: no AI writes Terraform. The same request always produces the
same file, so re-running the workflow for a RITM is safe.

Result (printed, and written to $GITHUB_OUTPUT with --output-github):
    status = created | exists       exit code 0
    file, branch, project_id, module_name, pr_title
Invalid input or a clash with another request -> message on stderr, exit code 1.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TF_DIR = ROOT / "terraform"
DEFAULTS = ROOT / "config" / "project-defaults.json"

FIELDS = ["ritm", "sctask", "project_name", "project_id", "app_team_name", "support_group",
          "technical_owner", "budget_approver", "requested_for"]
OPTIONAL = {"project_id"}                       # worked out from project_name when empty
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,24}[a-z0-9]$")             # 3-26 chars: prefix + name <= 30
PROJECT_ID_RE = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")       # Google's rule: 6-30 chars
FORBIDDEN_WORDS = ("google", "ssl", "null", "undefined")             # Google refuses IDs with these
NOT_ALLOWED = {"test", "project", "gcp", "new", "temp", "my-project", "gcp-project", "new-project"}
TICKET_RE = {"ritm": re.compile(r"^RITM\d{7,10}$"), "sctask": re.compile(r"^SCTASK\d{7,10}$")}
LABEL_KEY_RE = re.compile(r"^[a-z][a-z0-9_-]{0,62}$")


class RequestError(ValueError):
    pass


# ---------------------------------------------------------------- validation
def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def validate(req, prefix="syy-"):
    """Check and normalise a request dict. Returns a cleaned copy or raises RequestError."""
    r = {k: str(req.get(k, "") or "").strip() for k in FIELDS}
    missing = [k for k in FIELDS if not r[k] and k not in OPTIONAL]
    if missing:
        raise RequestError(f"missing values: {', '.join(missing)}")
    for k, pattern in TICKET_RE.items():
        r[k] = r[k].upper()
        if not pattern.match(r[k]):
            raise RequestError(f"{k} looks wrong: {r[k]!r}")
    name = slug(r["project_name"])
    if name.startswith(slug(prefix) + "-"):
        raise RequestError(f"project_name {name!r} must not start with {prefix!r}; it is added for you")
    if not NAME_RE.match(name) or "--" in name:
        raise RequestError(f"project_name {name!r}: 3-26 chars, lowercase letters, numbers and single "
                           "hyphens, starting with a letter")
    if any(w in name for w in FORBIDDEN_WORDS):
        raise RequestError(f"project_name {name!r} contains a word Google doesn't allow in project IDs "
                           f"({', '.join(FORBIDDEN_WORDS)})")
    if name in NOT_ALLOWED:
        raise RequestError(f"project_name {name!r} is too generic")
    r["project_name"] = name
    expected = prefix + name
    if r["project_id"] and r["project_id"].lower() != expected:
        raise RequestError(f"project_id {r['project_id']!r} doesn't match the project name "
                           f"(expected {expected!r})")
    r["project_id"] = expected
    if not PROJECT_ID_RE.match(expected):
        raise RequestError(f"project_id {expected!r} breaks Google's rules (6-30 chars)")
    for k in ("technical_owner", "budget_approver", "requested_for"):
        r[k] = r[k].lower()
        if not EMAIL_RE.match(r[k]):
            raise RequestError(f"{k} is not a single valid email address: {r[k]!r}")
    for k in ("app_team_name", "support_group"):
        if len(r[k]) > 200 or not label_value(r[k]):
            raise RequestError(f"{k} can't be turned into a GCP label: {r[k]!r}")
    return r


# ---------------------------------------------------------------- rendering
def hcl_string(value):
    """Quote a value for HCL (escape \\ and \", and stop ${ } / %{ } templates)."""
    v = value.replace("\\", "\\\\").replace('"', '\\"')
    v = v.replace("${", "$${").replace("%{", "%%{")
    return f'"{v}"'


def label_value(value):
    """GCP label values: lowercase letters, digits, _ and -, at most 63 characters.
    Spaces and other characters become _, no doubled separators (company labelling rule):
    'Order Management' -> 'order_management', 'tom.lee@corp.com' -> 'tom_lee_corp_com'."""
    v = re.sub(r"[^a-z0-9_-]+", "_", value.lower())
    v = re.sub(r"_+", "_", re.sub(r"-+", "-", v)).strip("_-")
    return v[:63].rstrip("_-")


def module_name(project_id):
    return "project_" + project_id.replace("-", "_")


def display_name(project_name):
    """Project display name: 4-30 chars. The name itself if it fits, else the project ID."""
    return project_name if len(project_name) >= 4 else None


def render(r, defaults):
    """The Terraform file for one project."""
    name = module_name(r["project_id"])
    labels = {}
    for k, v in defaults.get("labels", {}).items():
        if not LABEL_KEY_RE.match(k):
            raise RequestError(f"label key {k!r} in config is not a valid GCP label key")
        labels[k] = label_value(v.format(**r))
    width = max((len(hcl_string(k)) for k in labels), default=0)
    label_lines = "\n".join(f"    {hcl_string(k).ljust(width)} = {hcl_string(v)}" for k, v in labels.items())
    apis = ", ".join(hcl_string(a) for a in defaults.get("activate_apis", []))
    shown = display_name(r["project_name"]) or r["project_id"]
    return f'''# GCP project requested in ServiceNow {r["ritm"]} / {r["sctask"]}
# Requested for: {r["requested_for"]}
# Technical owner: {r["technical_owner"]} | Budget approver: {r["budget_approver"]}
# Written by scripts/new_project.py. Change it through a new request, not by hand.
module "{name}" {{
  source = {hcl_string(defaults["module_source"])}

  project_id      = {hcl_string(r["project_id"])}
  name            = {hcl_string(shown)}
  folder_id       = {hcl_string(defaults["folder_id"])}
  billing_account = {hcl_string(defaults["billing_account"])}
  activate_apis   = [{apis}]

  labels = {{
{label_lines}
  }}
}}

output "{name}_number" {{
  description = "Project number of {r["project_id"]}"
  value       = module.{name}.number
}}
'''


def pr_body(r, file_rel):
    """PR description. The HTML comments are read back by close_requests.py after merge."""
    return f"""## New GCP project: `{r["project_id"]}`

Approved in ServiceNow by the requester's manager. Created by the project-request workflow.

| | |
|---|---|
| ServiceNow | {r["ritm"]} / {r["sctask"]} |
| Project name | {r["project_name"]} |
| Project ID | `{r["project_id"]}` (can't be changed later) |
| Requested for | {r["requested_for"]} |
| App / Team | {r["app_team_name"]} |
| Support group | {r["support_group"]} |
| Technical owner | {r["technical_owner"]} |
| Budget approver | {r["budget_approver"]} |
| File | `{file_rel}` |

### Reviewers (Cloud Engineering)
- [ ] Project ID, folder and billing account are right
- [ ] `terraform plan` (comment below) creates exactly **1** project (plus its API services) and changes nothing else
- [ ] Checks are green

Approvals from Cloud Engineering are required. Merging creates the project.

<!-- ritm: {r["ritm"]} -->
<!-- sctask: {r["sctask"]} -->
<!-- project: {r["project_id"]} -->
"""


# ---------------------------------------------------------------- main logic
def create(req, tf_dir=None, defaults=None):
    """Validate, then write the project file unless it already exists for this RITM."""
    tf_dir = TF_DIR if tf_dir is None else tf_dir
    defaults = defaults or json.loads(DEFAULTS.read_text(encoding="utf-8"))
    r = validate(req, prefix=defaults.get("project_id_prefix", "syy-"))
    path = Path(tf_dir) / f"project_{r['project_id']}.tf"
    content = render(r, defaults)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if f"ServiceNow {r['ritm']} " not in existing:
            raise RequestError(f"a project with ID {r['project_id']!r} already exists "
                               f"({path.name}, from another request)")
        status = "exists"                      # same RITM: re-run of the workflow, nothing to do
    else:
        path.write_text(content, encoding="utf-8")
        status = "created"
    rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    return {"status": status, "file": str(rel), "project_id": r["project_id"],
            "module_name": module_name(r["project_id"]),
            "branch": f"project/{r['ritm']}-{r['project_id']}",
            "pr_title": f"Add GCP project {r['project_id']} ({r['ritm']})",
            "body": pr_body(r, rel), "request": r}


def main(argv=None):
    p = argparse.ArgumentParser(description="Write terraform/project_<id>.tf for one request")
    for k in FIELDS:
        p.add_argument("--" + k.replace("_", "-"), dest=k)
    p.add_argument("--from-env", action="store_true", help="read REQ_<FIELD> environment variables")
    p.add_argument("--output-github", action="store_true", help="also write $GITHUB_OUTPUT")
    p.add_argument("--pr-body-file", default="pr_body.md")
    a = p.parse_args(argv)
    req = {k: (os.environ.get("REQ_" + k.upper(), "") if a.from_env else getattr(a, k)) for k in FIELDS}
    try:
        result = create(req)
    except RequestError as e:
        print(f"::error::{e}" if os.environ.get("GITHUB_ACTIONS") else f"Error: {e}", file=sys.stderr)
        return 1
    Path(a.pr_body_file).write_text(result["body"], encoding="utf-8")
    keys = ["status", "file", "project_id", "module_name", "branch", "pr_title"]
    for k in keys:
        print(f"{k}={result[k]}")
    if a.output_github and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
            for k in keys:
                out.write(f"{k}={result[k]}\n")
            out.write(f"pr_body={a.pr_body_file}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
