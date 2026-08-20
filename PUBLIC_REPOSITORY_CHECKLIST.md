# Vice CEO public repository checklist

This checklist prepares **only this directory** for a separate public
hackathon repository. It does not authorize publishing the private Westover
EPR repository or deploying a service.

## Public-source allowlist

Copy these items to the standalone repository root:

- `app/`
- `tests/`
- `scripts/`
- `Dockerfile`
- `agents-cli-manifest.yaml`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `LICENSE`
- `ARCHITECTURE.png`
- `ARCHITECTURE.svg`

## Required public-repository checks

- [ ] Run a fresh secret scan after the standalone copy is created.
- [ ] Confirm no `.env`, credential export, customer fixture, production URL,
  deployment target, or private Westover material is included.
- [ ] Confirm `LICENSE` appears at the public repository root.
- [ ] Confirm the root README explains the synthetic-only boundary, install
  commands, tests, architecture, and video/demo path.
- [ ] Confirm `ARCHITECTURE.png` renders correctly and attach it to Devpost.
- [ ] Confirm the GitHub repository is public only after the contents above
  have been reviewed.

## Never copy from the parent Westover repository

- `.env*`, service-account files, Supabase configuration, and deployment
  values;
- `src/`, `product-evidence/`, `artifacts/`, database migrations, customer
  workflows, or private operational documents; and
- Git history from the private parent repository.

The submission may claim only what the runtime demonstrates locally: a
synthetic, zero-effect proof-carrying workflow with no production authority.
