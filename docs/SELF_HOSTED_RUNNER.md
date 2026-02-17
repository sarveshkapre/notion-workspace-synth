# Self-Hosted GitHub Actions Runner

This repository CI is configured for `runs-on: self-hosted` and does not rely on GitHub-hosted runners.

## 1) Runner machine prerequisites

Required tools:
- `git`
- `make`
- `curl`
- `tar`
- `python3` (3.11+ recommended)

Recommended:
- persistent workspace storage (for pip cache)
- outbound network access to `github.com`, `api.github.com`, and `pypi.org`

Platform notes:
- Linux and macOS are supported by the workflow.
- Docker is not required by CI in this repository.

## 2) Register a runner in this repository

1. Open repository settings:
   - `Settings -> Actions -> Runners -> New self-hosted runner`
2. Select your OS and architecture.
3. On the runner machine, run the commands GitHub shows:
   - `mkdir actions-runner && cd actions-runner`
   - download + extract runner package
   - `./config.sh --url <repo-url> --token <registration-token>`
4. Start runner:
   - foreground: `./run.sh`
   - service mode (recommended): `sudo ./svc.sh install && sudo ./svc.sh start`
5. Confirm runner status in GitHub UI is `Idle`.

Because the workflow uses only `runs-on: self-hosted`, any online self-hosted runner registered for this repository can pick up jobs.

## 3) Validate locally before/after registration

Run the same command sequence as CI:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
make check
make security
scripts/ci_self_hosted_smoke.sh
```

Expected result:
- all commands exit with status `0`
- GitHub Actions workflow `CI` succeeds on the self-hosted runner

## 4) Troubleshooting

- `Missing required command` in workflow:
  - install the missing CLI on runner host and rerun.
- `actions/setup-python` fails:
  - ensure runner can reach GitHub release assets and has disk space.
- `pip_audit` failures:
  - these are dependency vulnerabilities, not runner failures.
