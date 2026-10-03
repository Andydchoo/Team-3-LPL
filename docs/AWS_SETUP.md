# AWS owner: first live integration milestone

This guide follows `owners/AWS-INTEGRATION-OWNER.md`. The current AWS work adds
credential setup, private S3 evidence storage/access and real service preflight
checks. The frontend is now pulled into this checkout. Integration connects its
existing service boundary; the investigation agent remains the AI owner's work.

## 1. Prepare the local environment

Run from the repository root in a local PowerShell terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-aws.txt
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m integration.configure_credentials --profile revenue-hackathon
```

The setup command prompts with hidden input for the event's access key ID,
secret access key and session token. It stores the named profile in the standard
user `.aws/credentials` file, outside this repository, and sets its config region
to us-east-1. It preserves unrelated profiles. These are standard local AWS
credential files, not an encrypted secrets vault; use the event's temporary
credentials and refresh this profile when they expire.

Keep credentials out of `.env`, source code, command-line arguments and chat.
AWS documents the [temporary credential setup](https://docs.aws.amazon.com/sdkref/latest/guide/access-temp-idc.html)
and required [session token](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_use-resources.html).

### Refresh an expired event session

Preflight reports the safe AWS `error_code` on service failures. `ExpiredToken`
means the saved temporary session has expired. Return to the same event account,
obtain a fresh access key ID, secret access key and session token together, then
run this in your local interactive terminal:

```powershell
.\.venv\Scripts\python.exe -m integration.configure_credentials --profile revenue-hackathon
.\.venv\Scripts\python.exe -m integration.aws_preflight --profile revenue-hackathon
```

Replace all three values from the same new session. The bucket/model environment
settings remain usable in the same terminal. Restart Streamlit after refreshing
if it is already running with cached credentials. If the event portal cannot issue
fresh credentials, the event organizer must renew access. Do not recreate the
bucket to fix an expired session.

## 2. Verify account access before picking resources

```powershell
$env:AWS_PROFILE = 'revenue-hackathon'
$env:AWS_REGION = 'us-east-1'
$env:AWS_DEFAULT_REGION = 'us-east-1'
$env:AWS_EC2_METADATA_DISABLED = 'true'
.\.venv\Scripts\python.exe -m integration.aws_preflight
```

This first run can pass `region` and `aws_identity` while reporting that bucket
and model settings are missing. The account ID should match the event account.
Exit code 1 means at least one required check is incomplete; it does not
necessarily mean credentials failed. Keys and tokens are never printed.

Set the resource names; `.env.example` is a reference and is not automatically
loaded. The following resources passed live validation in account 514878621897:

```powershell
$env:REVENUE_S3_BUCKET = 'revenuetwin-514878621897-evidence'
$env:BEDROCK_MODEL_ID = 'amazon.nova-lite-v1:0'
```

Nova Lite matches the AI owner's branch configuration. Its authorization,
entitlement and region availability were checked before a real Converse request
succeeded. This uses the direct model ID in us-east-1. If the event requires
another model, change the setting and rerun preflight. No model subscription was
created. If the assigned ID is a
cross-region inference profile, verify that the event allows its routing and
that the role covers its destination model resources.

## 3. Upload Anderson evidence to private S3

For an existing assigned bucket, the command verifies privacy before uploading:

```powershell
.\.venv\Scripts\python.exe -m integration.setup_s3 --bucket $env:REVENUE_S3_BUCKET
```

If the event permits creating a new bucket, choose a globally unique demo name
and explicitly request creation:

```powershell
.\.venv\Scripts\python.exe -m integration.setup_s3 --bucket $env:REVENUE_S3_BUCKET --create
```

Creation enables BucketOwnerEnforced ownership, all four Block Public Access
settings and AES256 default encryption. It never calls CreateBucket again on an
existing bucket or changes an existing bucket's privacy settings. Uploads
include AES256 encryption and the expected owner account. The object keys are:

- `evidence/anderson/agreement.json`
- `evidence/anderson/pricing_exception.json`
- `evidence/anderson/billing.json`

Only the engine's explicitly synthetic documents are uploaded. Upload is followed
by authenticated reads. Bucket privacy verification requires inspection permissions;
an AccessDenied result does not establish that a bucket is public or private.
Ask the event administrator for the specific missing permission if role changes
are restricted. Adding this code has not deployed a bucket, policy or evidence.

## 4. Run the complete access preflight

```powershell
.\.venv\Scripts\python.exe -m integration.aws_preflight
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Preflight must pass region, AWS identity, private bucket, three evidence reads
and a real Bedrock Converse text response. The Bedrock probe is a short synthetic
connectivity request, not an investigation or financial calculation. It incurs
normal model invocation usage. Avoid repeated probes within one second; the SDK
may retry a transient request once. A response verifies access, not tool-use
capability or the AI owner's finished integration.

## IAM scope

`infra/runtime-policy.template.json` scopes evidence reads and bucket inspection
to one bucket and Bedrock invocation to an assigned resource ARN. Replace its
placeholders before applying it. `infra/setup-policy.template.json` adds bucket
setup and uploads for the coordinator's setup role; combine it with runtime
permissions when running setup/read-back. Neither file is applied automatically.
The runtime role does not need CreateBucket or PutObject for evidence retrieval.

`infra/runtime-policy.event.json` contains the concrete bucket and direct-model
ARN verified for this account. It is a reviewable policy document; no IAM policy
or role was created or attached. Live checks used the existing event role.

For an inference profile, add the exact source/destination foundation-model ARNs
required for that profile to the invocation statement. A profile ARN alone is
insufficient. See AWS's [inference profile authorization guidance](https://docs.aws.amazon.com/bedrock/latest/userguide/geographic-cross-region-inference.html).
Converse uses [bedrock:InvokeModel](https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/converse.html).

The application role now also needs `s3:PutObject` on
`arn:aws:s3:::YOUR_BUCKET/reviews/CASE-001/*`. This grants review writes separately
from evidence reads; the application still cannot upload or alter source evidence
using the runtime template. Review objects use AES256 encryption, the expected
bucket owner and a unique key with `IfNoneMatch='*'`. The application confirms a
decision only after a successful [S3 PutObject](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html).
This is a simple workflow record, not a tamper-proof compliance archive. A failed
or timed-out write is not confirmed; another human click creates a new review ID.

## 5. Connect and run the existing Streamlit frontend

Offline mode works without AWS credentials and remains the default:

```powershell
$env:REVENUE_BACKEND = 'local'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

After the live access preflight passes, use the same profile, bucket and model
settings in the terminal that starts Streamlit:

```powershell
$env:REVENUE_BACKEND = 'aws'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

AWS mode supports Anderson only. Its finding is calculated by the engine from
private S3 evidence, and the source documents remain visible when AI fails.
Other cases remain local demo fixtures and are unavailable in AWS mode. The UI
labels the mode explicitly, clears stale mock results when the mode changes and
shows clean retry states rather than substituting mock success after an AWS error.
Changing shell environment variables requires restarting the Streamlit process;
setting credentials in another terminal does not change the running process's
environment. The example `.env` file is not loaded automatically.

The AI owner's package must export `investigation.investigate_case(case_id)` and
register both read-only tools from `integration.case_tools`. The current pulled
frontend has no investigation package; AWS mode therefore reports a clean
integration error until that handoff is available. The integration adapter
validates the shared JSON Schema, matching case ID, unique evidence references
and human-review flag before rendering. The AI owner supplies Bedrock tool use,
request pacing and an optional formatting repair; malformed responses are rejected.

To validate the P0 handoff after the agent is integrated:

1. Select Anderson and confirm $12,000 / $9,000 / $3,000 from S3 evidence.
2. Investigate and confirm the agent actually calls both S3-backed tools.
3. Select Send for Review and confirm the JSON object under
   `reviews/CASE-001/<review_id>.json`; verify `actor: human` and a UTC `Z` timestamp.
4. Exercise model failure and retry; preserve the finding and three source documents.
5. Exercise denied review-write access; show no confirmed decision until a write
   succeeds. Starting another review leaves the previous S3 record intact.
6. Repeat the full flow before merging the integration work into stable main.

The access preflight checks identity, S3 reads and a model text response. It does
not prove the agent's tool loop, review-write permissions or complete UI flow.

## Owner handoff

After live preflight passes, the AI owner can import the unchanged read-only
tool names from `integration.case_tools`:

```python
from integration.case_tools import get_revenue_case, get_case_evidence
```

The case adapter delegates arithmetic to the engine using retrieved S3 evidence.
UI and AI schemas remain in `docs/CONTRACTS.md`. S3 failures are reported and
do not silently substitute local documents. The local engine tools remain
available for clearly labeled offline development.

Bedrock failure preserves the financial finding and evidence in the UI and allows
retry. SDK exceptions and agent error payloads are mapped to controlled messages;
model prose is escaped before insertion into HTML cards. The AI owner owns model
tool invocation, structured output generation and `investigate_case`; integration
adds boundary validation and error handling. `record_review` now persists human
workflow decisions in the same private S3 bucket without adding another service.
Offline service and Streamlit tests cover these handoffs and failure states.

## Current validation status

The SDK is installed locally and offline tests use botocore Stubber to validate
API requests without contacting AWS. The complete suite currently passes 71
tests, including Streamlit AppTest coverage with stubbed service responses.
The first live access milestone previously passed with `ready: true`:

| Check | Verified result |
|---|---|
| AWS identity | Account 514878621897 using local profile `revenue-hackathon` |
| Region | us-east-1 |
| Private S3 | `revenuetwin-514878621897-evidence`; all four public-access blocks, BucketOwnerEnforced, no public policy |
| Encryption | Bucket default and all three evidence objects use AES256 |
| Evidence | All three Anderson documents uploaded and read back |
| Engine on S3 evidence | Expected $12,000; actual $9,000; difference $3,000 |
| Bedrock | `amazon.nova-lite-v1:0` returned text through a real Converse request |

Repeat the access check using the profile/resource settings above:

```powershell
.\.venv\Scripts\python.exe -m integration.aws_preflight
```

Credentials remain outside the repository and must be refreshed when they expire.
The latest identity diagnostic returned `ExpiredToken` from the saved event
profile. Refresh the temporary credential set before repeating live checks.
The agent's two-tool flow, live human-review write and complete UI workflow remain
pending. Passing this access preflight does not complete the AWS owner task.
