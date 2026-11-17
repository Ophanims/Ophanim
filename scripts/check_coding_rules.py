"""Check source size, transport ownership and shared contract naming."""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ["backend", "scripts", "frontend/src", "frontend/tests"]
EXTENSIONS = {".py", ".ts", ".tsx", ".css", ".sh"}


def check_rules() -> None:
    failures = []
    checked_count = 0
    for scope in SCOPES:
        for path in (ROOT / scope).rglob("*"):
            if path.suffix not in EXTENSIONS or not path.is_file():
                continue
            text = path.read_text()
            if path.name in {"generated.ts", "routes.generated.ts"}:
                if not text.startswith("// Generated"):
                    failures.append(f"{path}: missing generated-code marker")
                continue
            checked_count += 1
            relative = path.relative_to(ROOT)
            if len(text.splitlines()) > 500:
                failures.append(f"{relative}: exceeds 500 physical lines")
            if path.suffix == ".py":
                tree = ast.parse(text, filename=str(relative))
                for node in ast.walk(tree):
                    if isinstance(node, ast.keyword) and node.arg in {"alias", "alias_generator"}:
                        failures.append(f"{relative}:{node.lineno}: serialization alias in canonical code")
                    if isinstance(node, ast.ImportFrom) and "simulator" in path.parts:
                        module = node.module or ""
                        if module.startswith("controller."):
                            failures.append(f"{relative}:{node.lineno}: domain depends on legacy controller")
            if scope == "frontend/src" and "communication" not in path.parts and "api" not in path.parts:
                if re.search(r"\bfetch\s*\(|new\s+WebSocket\s*\(", text):
                    failures.append(f"{relative}: transport call outside communication module")
    sys.path.insert(0, str(ROOT / "backend"))
    from simulator.schemas.project import Project
    from simulator.contracts import SimulationSnapshot
    for model in (Project, SimulationSnapshot):
        schema = model.model_json_schema()
        for name, definition in {model.__name__: schema, **schema.get("$defs", {})}.items():
            for field in definition.get("properties", {}):
                if not re.fullmatch(r"[a-z][a-z0-9_]*", field):
                    failures.append(f"{name}.{field}: noncanonical contract field")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Coding rules passed for {checked_count} handwritten files across the application.")



if __name__ == "__main__":
    check_rules()
