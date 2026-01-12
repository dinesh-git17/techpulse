# Label Taxonomy

Single source of truth for repository labels. This file serves as IaC for `github-label-sync` or equivalent tooling.

## Type Labels

| Label | Hex Color | Description |
|-------|-----------|-------------|
| `type: bug` | `#d73a4a` | Something isn't working |
| `type: feat` | `#0e8a16` | New feature or enhancement |
| `type: debt` | `#1d76db` | Technical debt or refactoring |
| `type: docs` | `#6a737d` | Documentation improvements |
| `type: chore` | `#6a737d` | Maintenance tasks |

## Status Labels

| Label | Hex Color | Description |
|-------|-----------|-------------|
| `status: triage` | `#5319e7` | Needs initial assessment |
| `status: blocked` | `#fbca04` | Waiting on external dependency |
| `status: needs-info` | `#fbca04` | Requires more information from reporter |
| `status: in-progress` | `#1d76db` | Actively being worked on |
| `status: review` | `#5319e7` | Ready for code review |

## Area Labels

| Label | Hex Color | Description |
|-------|-----------|-------------|
| `area: backend` | `#6a737d` | Backend service changes |
| `area: frontend` | `#6a737d` | Frontend application changes |
| `area: data` | `#6a737d` | Data pipeline changes |
| `area: infra` | `#6a737d` | Infrastructure and DevOps |
| `area: compliance` | `#6a737d` | Security and compliance |

## Priority Labels

| Label | Hex Color | Description |
|-------|-----------|-------------|
| `prio: P0` | `#d73a4a` | Critical - Drop everything |
| `prio: P1` | `#fbca04` | High - Address this sprint |
| `prio: P2` | `#0e8a16` | Normal - Backlog priority |
| `prio: P3` | `#6a737d` | Low - Nice to have |
