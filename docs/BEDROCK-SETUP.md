# Amazon Bedrock setup

The agent uses Amazon Bedrock for its AI. Without access it still runs, but answers fall back to keyword matching.

## 1. Credentials

The worker reads credentials from `~/.aws` on your machine (mounted into the container). Any of these work:

| Method | Command | Notes |
|---|---|---|
| Console sign-in (recommended) | `aws login --profile dev --region us-east-1` | Short-lived credentials, no access keys. Needs AWS CLI 2.32+ and the `SignInLocalDevelopmentAccess` policy. |
| IAM Identity Center | `aws configure sso` | Good for teams and multi-account setups |
| Access keys | `aws configure` | Simplest, but keys are long-lived. Avoid in shared environments. |
| IAM role | none | On EC2 or ECS, attach a role instead of using any keys |

Then set `AWS_PROFILE` and `AWS_REGION` in `.env`, and check:

```bash
aws sts get-caller-identity --profile <profile>
```

## 2. Model access

Open the Bedrock console in **us-east-1** → Model catalog → choose the model.

- **Anthropic (Claude) models** need a one-time use-case form per account. After submitting, wait about 15 minutes.
- **Amazon Nova models** need no form. To use one, set `BEDROCK_MODEL_ID=us.amazon.nova-lite-v1:0`.

## 3. Quotas

Bedrock → Quotas (or Service Quotas → Amazon Bedrock) shows tokens and requests per minute and per day for each model and region.

New accounts, especially on the AWS free plan, can have these set to **0**. Calls then fail with `ThrottlingException: Too many tokens per day` even on the first request. Request an increase from the quota's menu, or open a support case.

## 4. Least-privilege IAM policy

The worker needs only these permissions (replace the account ID; adjust the model ID if you change it):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1:<ACCOUNT_ID>:inference-profile/us.anthropic.claude-haiku-4-5-*",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-*"
      ]
    }
  ]
}
```

The `us.` model ID is a cross-region inference profile, which is why both the profile and the underlying foundation models are listed.

## 5. Common errors

| Error | Meaning | Fix |
|---|---|---|
| `ResourceNotFoundException: Model use case details have not been submitted` | Anthropic form missing | Submit the form, wait 15 minutes |
| `ThrottlingException: Too many tokens per day` | Daily quota is 0 or used up | Request a quota increase, or wait for the reset |
| `AccessDeniedException` | IAM policy missing | Add the policy above |
| `NoRegionError` | No region set | Set `AWS_REGION`, or `aws configure set region us-east-1 --profile <profile>` |
| `MissingDependencyException: botocore[crt]` | `aws login` credentials need the CRT package | `pip install "botocore[crt]"` (already in `requirements.txt`) |
