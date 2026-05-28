---
name: file-operations
description: Advanced filesystem management including moving, copying, and secure
  deletion.
version: 1.0.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
- write_file
- replace_content
- ls
- run_code
- mcp_slm_remember
tier: 2
---
# Skill: File Operations (Sovereign Edition)

Handles complex filesystem tasks with atomicity and multi-layer safety guards to ensure system integrity during structural changes.

## Workflow
1.  **Validate**: Verify the target path using `get_project_root()` and ensure it does not violate restricted directory rules.
2.  **Snapshot**: Before any modification, trigger `Sovereign Shield` to create a pre-write snapshot of the target file/directory.
3.  **Atomic Write**:
    - For large edits: Write to a `.tmp` file first, then use `os.replace` to ensure atomicity.
    - For small edits: Use the standard `replace_file_content` tool with precise target anchors.
4.  **Checksum**: Calculate the SHA-256 hash of the final file to verify successful write.
5.  **Audit**: Log the operation in `OperationalStore` (Axis 7) with the before/after state reference.

## Guardrails
- **Restricted Directories**: Never modify files in `.opencode`, `.git`, or system root unless an `L0_AUTH_TOKEN` is present.
- **Path Traversal**: Reject any path containing `..` or leading `/` that points outside the `D:\Hank` workspace.
- **Size Limit**: Operations involving files >50MB require explicit L0 confirmation.
- **Concurrency**: Only one "hard-write" operation is allowed at a time to prevent race conditions.

## Output Format
- `file_path`: Absolute path of the modified file.
- `operation`: Type of operation (MOVE, COPY, WRITE, DELETE).
- `checksum`: SHA-256 hash of the resulting artifact.
- `backup_path`: Path to the pre-write snapshot.
- `integrity_status`: Status of the post-write verification check.
