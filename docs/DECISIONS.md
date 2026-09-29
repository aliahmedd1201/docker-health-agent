# Design decisions

Short notes on why the project is built the way it is.

## Temporal for the agent's work
Checking a container, reading logs and calling an LLM can all fail halfway. Temporal gives retries with backoff, timeouts and a full history of every step without writing that logic by hand. If the worker crashes mid-run, the workflow resumes from the last completed step.

## LLM calls live in activities, never in workflows
Temporal replays workflow code to rebuild state, so workflow code must be deterministic. An LLM can answer differently every time, so every model call is an activity and its result is stored in the history.

## One retry layer
Strands and boto3 both retry on their own by default. Combined with Temporal that made a single call hang for over a minute and hit the activity timeout. The SDKs now fail fast and Temporal alone owns retries.

## Permanent vs temporary errors
Missing model access or an exhausted daily quota will not fix itself in a few seconds, so those errors are marked non-retryable and fail fast. Short throttling and timeouts are retried.

## The AI is advisory, not in the critical path
Whether to restart is decided by plain rules (not running, healthcheck failing, high CPU or memory). The LLM only explains the cause. Healing keeps working when Bedrock is down.

## Fallbacks are visible
When the LLM is unavailable the agent answers with a keyword-based plan and says so in the output. It never silently pretends the AI answered.

## Guardrails on actions
- The agent may restart only containers in `ALLOWED_CONTAINERS`; it can read Temporal but never restart it or itself.
- A container that has restarted 5 or more times is treated as a crash loop and escalated instead of restarted again.

## No raw Docker socket for the agent
Access to `/var/run/docker.sock` is close to root on the host. The worker talks to a docker-socket-proxy that only allows reading containers and restarting them.

## Docker restart policy and the agent work together
`restart: unless-stopped` already recovers containers that exit. Docker does not act on containers that are running but unhealthy; that gap is what the agent covers.

## Container hardening
- Backend, frontend and worker run as non-root users.
- Nginx listens on 8080 so it does not need root.
- Frontend uses a multi-stage build: the final image has Nginx and static files only (about 23 MB).
- The backend has no published port; it is reachable only through Nginx.
- Memory and CPU limits on every service, and log rotation (3 × 10 MB) so logs cannot fill the disk.

## Nginx re-resolves the backend address
Nginx normally resolves upstream names once at startup. With Docker's DNS resolver and a variable in `proxy_pass`, Nginx keeps serving when the backend is down and reconnects automatically when it returns.

## Healthcheck uses 127.0.0.1, not localhost
In Alpine, `localhost` resolves to IPv6 first while Nginx listened on IPv4 only, which made the healthcheck fail although the site worked.

## Claude Haiku as the default model
The tasks are short classification and summarisation, where a small model is fast and cheap. Any Bedrock model can be set with `BEDROCK_MODEL_ID`.

## Known limitations
- Temporal dev server keeps history in memory. Production: Temporal Cloud or a self-hosted cluster.
- Single Docker host.
