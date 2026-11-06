# GCP setup (for the real pipeline)

What a GCP admin sets up once, so GitHub Actions can plan and create projects without stored
keys. Replace the values in `<>`. Run it in Cloud Shell or anywhere `gcloud` is logged in as
an organisation admin.

```bash
ORG_ID=<organisation id>                 # gcloud organizations list
FOLDER_ID=<folder id for new projects>   # numeric
BILLING=<billing account id>             # XXXXXX-XXXXXX-XXXXXX
ADMIN_PROJECT=<existing project for automation, e.g. syy-cet-automation>
REPO=<github owner>/gcp-account-vending
STATE_BUCKET=<globally unique bucket name>
```

## 1. State bucket (versioned)

```bash
gcloud storage buckets create gs://$STATE_BUCKET --project $ADMIN_PROJECT \
  --location <region> --uniform-bucket-level-access
gcloud storage buckets update gs://$STATE_BUCKET --versioning
```

Put the bucket name in `terraform/backend.tf`.

## 2. Two service accounts

```bash
gcloud iam service-accounts create gcp-vending-plan  --project $ADMIN_PROJECT --display-name "GCP vending: plan"
gcloud iam service-accounts create gcp-vending-apply --project $ADMIN_PROJECT --display-name "GCP vending: apply"
PLAN_SA=gcp-vending-plan@$ADMIN_PROJECT.iam.gserviceaccount.com
APPLY_SA=gcp-vending-apply@$ADMIN_PROJECT.iam.gserviceaccount.com
```

| Service account | Role | On |
|---|---|---|
| plan | Browser (`roles/browser`) | the folder |
| plan | Storage Object Viewer | the state bucket |
| apply | Project Creator (`roles/resourcemanager.projectCreator`) | the folder |
| apply | Billing Account User (`roles/billing.user`) | the billing account |
| apply | Service Usage Admin (`roles/serviceusage.serviceUsageAdmin`) | the folder |
| apply | Storage Object Admin | the state bucket |

```bash
gcloud resource-manager folders add-iam-policy-binding $FOLDER_ID --member serviceAccount:$PLAN_SA  --role roles/browser
gcloud resource-manager folders add-iam-policy-binding $FOLDER_ID --member serviceAccount:$APPLY_SA --role roles/resourcemanager.projectCreator
gcloud resource-manager folders add-iam-policy-binding $FOLDER_ID --member serviceAccount:$APPLY_SA --role roles/serviceusage.serviceUsageAdmin
gcloud billing accounts add-iam-policy-binding $BILLING --member serviceAccount:$APPLY_SA --role roles/billing.user
gcloud storage buckets add-iam-policy-binding gs://$STATE_BUCKET --member serviceAccount:$PLAN_SA  --role roles/storage.objectViewer
gcloud storage buckets add-iam-policy-binding gs://$STATE_BUCKET --member serviceAccount:$APPLY_SA --role roles/storage.objectAdmin
```

The plan job runs with `-lock=false`, so read access to the state is enough for it.

## 3. Workload Identity Federation (GitHub → GCP, no keys)

```bash
gcloud iam workload-identity-pools create github --project $ADMIN_PROJECT --location global \
  --display-name "GitHub Actions"
gcloud iam workload-identity-pools providers create-oidc gcp-account-vending \
  --project $ADMIN_PROJECT --location global --workload-identity-pool github \
  --issuer-uri https://token.actions.githubusercontent.com \
  --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.environment=assertion.environment" \
  --attribute-condition "assertion.repository == '$REPO'"
POOL=$(gcloud iam workload-identity-pools describe github --project $ADMIN_PROJECT --location global --format 'value(name)')
```

For GitHub Enterprise Server, the issuer is `https://<your-ghes-host>/_services/token`.

Who may use which service account:

```bash
# plan: any workflow in this repo (pull requests)
gcloud iam service-accounts add-iam-policy-binding $PLAN_SA --project $ADMIN_PROJECT \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/$POOL/attribute.repository/$REPO"
# apply: only jobs in the GitHub "production" environment (after merge)
gcloud iam service-accounts add-iam-policy-binding $APPLY_SA --project $ADMIN_PROJECT \
  --role roles/iam.workloadIdentityUser \
  --member "principal://iam.googleapis.com/$POOL/subject/repo:$REPO:environment:production"
```

## 4. Tell the repo

```bash
gh variable set GCP_WIF_PROVIDER --repo $REPO --body "$POOL/providers/gcp-account-vending"
gh variable set GCP_PLAN_SA      --repo $REPO --body "$PLAN_SA"
gh variable set GCP_APPLY_SA     --repo $REPO --body "$APPLY_SA"
```

Setting `GCP_WIF_PROVIDER` turns practice mode off: the next PR shows a real plan.

## 5. First real test

Use a sandbox folder first (`folder_id` in `config/project-defaults.json`). The plan for one
request should read `Plan: 3 to add`: the project and its two API services.
