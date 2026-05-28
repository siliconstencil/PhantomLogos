# GitHub MCP Operations

Manage repositories, issues, pull requests, and code search via GitHub MCP.

## Requires

`GITHUB_TOKEN` must be set (via `scripts/run_github_mcp.bat` or env). Verify with `list_issues` on a known repo.

## Common Workflows

### Safe Contribution (branch -> PR)
```
create_branch(repo, branch, from_sha)
-> create_or_update_file(repo, path, content, branch)
-> create_pull_request(repo, title, head, base)
```

### Review a PR
```
get_pull_request(repo, pr_number)
-> get_pull_request_files(repo, pr_number)
-> get_pull_request_status(repo, pr_number)
-> create_pull_request_review(repo, pr_number, event, comments)
```

### Issue Management
```
list_issues(repo, state="open")
-> get_issue(repo, issue_number)
-> update_issue / add_issue_comment
```

### Code Search
```
search_code(query="<term> repo:<owner>/<repo>")
search_issues(query="<term> is:pr is:open")
```

## Tool Reference

| Category | Tools |
|----------|-------|
| Files | `create_or_update_file`, `get_file_contents`, `push_files` |
| Repo | `create_repository`, `fork_repository`, `search_repositories` |
| Branches | `create_branch`, `list_commits` |
| Issues | `create_issue`, `list_issues`, `update_issue`, `get_issue`, `add_issue_comment`, `search_issues` |
| PRs | `create_pull_request`, `list_pull_requests`, `get_pull_request`, `merge_pull_request`, `get_pull_request_files`, `get_pull_request_status`, `get_pull_request_comments`, `get_pull_request_reviews`, `create_pull_request_review`, `update_pull_request_branch` |
| Search | `search_code`, `search_users` |

## Guardrails
- NEVER commit secrets, tokens, or credentials.
- Always use branch -> PR workflow, never push directly to main.
- Verify token scopes before write operations.
- Use `get_pull_request_status` to check CI before merging.

GitHub task or repo (owner/repo): $ARGUMENTS
