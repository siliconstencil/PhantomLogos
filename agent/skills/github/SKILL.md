---
name: github
description: GitHub API integration via MCP. Repository management, file operations, issues, PRs, code search, and user management.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: expert
allowed_tools:
  - github_create_or_update_file
  - github_search_repositories
  - github_create_repository
  - github_get_file_contents
  - github_push_files
  - github_create_issue
  - github_create_pull_request
  - github_fork_repository
  - github_create_branch
  - github_list_commits
  - github_list_issues
  - github_update_issue
  - github_add_issue_comment
  - github_search_code
  - github_search_issues
  - github_search_users
  - github_get_issue
  - github_get_pull_request
  - github_list_pull_requests
  - github_create_pull_request_review
  - github_merge_pull_request
  - github_get_pull_request_files
  - github_get_pull_request_status
  - github_update_pull_request_branch
  - github_get_pull_request_comments
  - github_get_pull_request_reviews
  - report
tier: 3
when_to_use:
  - Creating or updating files in GitHub repositories.
  - Managing issues, pull requests, and code reviews.
  - Searching code, repositories, or users on GitHub.
  - Automating release workflows and repository management.
metadata:
  audience: developers
  tier: L3-Auditor
  workflow: version-control
---

# Skill: GitHub MCP

Full GitHub API integration via MCP. Wraps the Octokit library with 25 tools covering repositories, files, issues, pull requests, search, and user management.

## Requires

- `GITHUB_TOKEN` set in `.env` (personal access token with appropriate scopes)
- `scripts/run_github_mcp.bat` launches the server with token injection

## Tool Categories

### Repository & Files
| Tool | Description |
|------|-------------|
| `create_or_update_file` | Create or update a file in a repository (commits directly) |
| `get_file_contents` | Get contents of a file or directory at a specific path |
| `push_files` | Push multiple files in a single commit to a branch |
| `search_repositories` | Search GitHub repositories by query |
| `fork_repository` | Fork a repository to your account |
| `create_repository` | Create a new repository on GitHub |

### Branches & Commits
| Tool | Description |
|------|-------------|
| `create_branch` | Create a new branch from a specified reference |
| `list_commits` | List commits in a branch with pagination |

### Issues
| Tool | Description |
|------|-------------|
| `create_issue` | Create a new issue in a repository |
| `list_issues` | List issues with filtering (state, labels, assignee) |
| `update_issue` | Update issue title, body, state, labels, assignees |
| `get_issue` | Get details of a specific issue |
| `search_issues` | Search issues and PRs by query |
| `add_issue_comment` | Add a comment to an issue or PR |

### Pull Requests
| Tool | Description |
|------|-------------|
| `create_pull_request` | Create a new pull request |
| `list_pull_requests` | List PRs with state filtering |
| `get_pull_request` | Get details of a specific PR |
| `merge_pull_request` | Merge a PR (merge/squash/rebase) |
| `update_pull_request_branch` | Update a PR branch with latest base |
| `get_pull_request_files` | List changed files in a PR |
| `get_pull_request_status` | Get combined status of all CI checks |
| `get_pull_request_comments` | Get review comments on a PR |
| `get_pull_request_reviews` | Get reviews submitted on a PR |
| `create_pull_request_review` | Submit a review to a PR (approve/comment/request_changes) |

### Search
| Tool | Description |
|------|-------------|
| `search_code` | Search code across GitHub |
| `search_users` | Search GitHub users |

## Guardrails
- NEVER commit secrets or tokens to repositories
- ALWAYS verify GITHUB_TOKEN has correct scopes before operations
- Use `create_branch` + `create_or_update_file` + `create_pull_request` for safe contribution workflow
- Prefer PR-based workflows over direct pushes to main branch
