# 06. Path Traversal & Directory Sandboxing
**Status:** [VERIFIED]

## 1. File Path
`backend/app/agents/tools/sandbox_tools.py`: `validate_sandbox_path(target_path, allowed_dir)`

## 2. Threat Mitigated
Directory traversal attacks (e.g. `../../Windows/System32` or `../../../etc/shadow`) via uploaded filenames or tool parameters.

## 3. Canonical Path Enforcement
```python
def validate_sandbox_path(path: str, base_dir: Path) -> Path:
    resolved_target = Path(path).resolve()
    resolved_base = base_dir.resolve()
    if not str(resolved_target).startswith(str(resolved_base)):
        raise PermissionError(f"Access denied: {path} is outside allowed directory {base_dir}")
    return resolved_target
```
Restricts all read/write file tools strictly to:
- `multimodal_uploads/`
- `demo_data/`
- `generated_artifacts/`
