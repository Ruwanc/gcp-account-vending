# gcp-account-vending

Creates GCP projects from approved ServiceNow requests, through a reviewed Terraform PR.
The GCP twin of `aws-account-vending`: same flow, same scripts, same safety rules.

```
CET Agent / ServiceNow portal
        │  RITM (Cloud provider = GCP project)
        ▼
ServiceNow
  1. approval: requester's manager ──rejected──► RITM closed, requester told
        │ approved
  2. SCTASK created under the RITM, assigned to Cloud Engineering
  3. POST /repos/<owner>/gcp-account-vending/dispatches  (event "gcp-project-request";
     repo from system property cet.github.gcp_repo)
        ▼
GitHub Actions: project-request.yml
  writes terraform/project_syy-<name>.tf ─► branch project/<RITM>-syy-<name> ─► PR
  SCTASK → Work in Progress + PR link
        ▼
GitHub Actions: terraform-pr.yml (every PR)
  Teams card to CET ─ validate (tests, fmt, validate, tflint, checkov) ─ plan as PR comment
        ▼
Ruleset on master: approvals, code owners (Cloud Engineering), checks green
        ▼  merge
GitHub Actions: terraform-apply.yml
  terraform apply (GCP via Workload Identity) ─► SCTASK Closed Complete with project number ─► Teams
```

The **project ID** is always `syy-<project name>`: the same rule in the CET Agent, the
ServiceNow form and `scripts/new_project.py`. If a request carries a project ID that doesn't
match the name, it's refused rather than changed. Project IDs are unique across all of Google
Cloud and can't be changed, so the plan (or the apply) fails if the ID is already taken.

No AI writes Terraform here: `scripts/new_project.py` turns the request into the same file
every time, and people approve it.

## Layout

```
gcp-account-vending/
├── terraform/                     root stack (one state, GCS backend)
│   ├── versions.tf · providers.tf · backend.tf
│   ├── projects.tf                note only; projects are the project_*.tf files
│   ├── project_<project id>.tf    one per project, written by new_project.py
│   └── modules/gcp-project/       sample module (swap for your real module)
├── config/project-defaults.json   module source, ID prefix, folder, billing account, APIs, labels
├── scripts/
│   ├── new_project.py             request -> project file + PR body (validated, idempotent)
│   ├── servicenow.py              SCTASK work note / start / close
│   ├── teams_notify.py            card to the CET Teams channel
│   └── close_requests.py          after apply: close SCTASKs with the project numbers
├── tests/test_scripts.py          29 tests, no GCP/GitHub/ServiceNow needed
├── .github/
│   ├── workflows/project-request.yml · terraform-pr.yml · terraform-apply.yml
│   ├── CODEOWNERS                 @YOUR-ORG/cloud-engineering
│   └── rulesets/master.json · master-personal.json   2 approvals (company) · 1 (personal test)
└── docs/
    └── gcp-setup.md               the GCP side: service accounts, Workload Identity, state bucket
```

## Labels

GCP labels are stricter than AWS tags: lowercase letters, digits, `_` and `-`, at most 63
characters. `new_project.py` converts each value: spaces and other characters become `_`, and
doubled separators are removed. For example, `Order Management` becomes `order_management`
and `tom.lee@corp.com` becomes `tom_lee_corp_com`. The label keys are in
`config/project-defaults.json`. The full owner emails stay in the comment at the top of each
project file and in the PR.

## Try it first on a personal GitHub account

Public repo, no GCP (practice mode), you approve. Leave the `GCP_*` variables unset and
practice mode stays on: everything runs up to and including the merge, but no project is created.

## Set up for real (once)

1. **Repo and team:** `YOUR-ORG/gcp-account-vending` (private), default branch `master`.
   Team `cloud-engineering` with write access; set it in `.github/CODEOWNERS`.
2. **Settings:** `config/project-defaults.json` (folder ID, billing account, APIs, label keys,
   `module_source` if you have a project module) and `terraform/backend.tf` (state bucket).
3. **GitHub App:** install the same `cet-account-bot` app on this repo too. Set repo
   variable `ACCOUNT_BOT_APP_ID` and secret `ACCOUNT_BOT_PRIVATE_KEY`.
4. **GCP:** follow [docs/gcp-setup.md](docs/gcp-setup.md). Then set repo variables
   `GCP_WIF_PROVIDER`, `GCP_PLAN_SA` and `GCP_APPLY_SA`; practice mode turns off by itself.
   Also create the `production` environment.
5. **Teams and ServiceNow:** secrets `TEAMS_WEBHOOK_URL`, `SN_INSTANCE`, `SN_USERNAME` and
   `SN_PASSWORD`, as in aws-account-vending.
6. **ServiceNow → GitHub:**
   - Set system property `cet.github.gcp_repo` to `YOUR-ORG/gcp-account-vending`.
   - Make sure ServiceNow's GitHub credential can reach this repo. With the dispatch GitHub
     App, that means installing the app on this repo.
   - See the "ServiceNow Changes for GCP Project Requests" document.
7. **Ruleset** (after the first PR has run, so the check names exist):
   `gh api repos/YOUR-ORG/gcp-account-vending/rulesets --method POST --input .github/rulesets/master.json`

## Test it without ServiceNow

Actions → **project-request** → *Run workflow*. Fill in the fields (made-up RITM and SCTASK
numbers are fine); the project ID is made from the name. Or locally:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
python scripts/new_project.py --ritm RITM0000001 --sctask SCTASK0000001 --project-name demo-sbx \
  --app-team-name Demo --support-group "Demo Support" --technical-owner a@corp.com \
  --budget-approver b@corp.com --requested-for c@corp.com   # writes terraform/project_syy-demo-sbx.tf
```

## Safety built in

- **Request values can't run as code:** they reach the shell only through environment
  variables, and `new_project.py` checks every value before writing HCL.
- **Re-running is safe:** a re-run for the same RITM finds the open PR. A second request for an
  existing project ID is refused.
- **Projects can't be deleted by accident:** the module sets `deletion_policy = "PREVENT"` and
  `prevent_destroy`, and creates no default network.
- **Least privilege:** plan and apply use separate service accounts through Workload Identity,
  with no keys stored. The apply service account can only be used from the `production`
  environment after a merge.
- **Failures are reported:** ServiceNow gets a work note when the automation fails, and Teams
  gets a card when apply fails.
