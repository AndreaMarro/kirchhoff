import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TRUTH=ROOT/"src/kirchhoff/domain/truthfulness.py"
EXECUTE=ROOT/"src/kirchhoff/domain/didactic/execute.py"

def test_truthfulness_domain_only():
    text=TRUTH.read_text()
    tree=ast.parse(text)
    imports=[n.module or a.name for n in ast.walk(tree) for a in (n.names if isinstance(n,ast.Import) else [n]) if isinstance(n,(ast.Import,ast.ImportFrom))]
    assert not any(x and ("pipeline" in x or "render" in x or "adapter" in x) for x in imports)
    assert "pianifica(" not in text

def test_execute_has_no_oracle():
    text=EXECUTE.read_text()
    assert all(word not in text for word in ("solve_dc","solve_dc_tableau","truthfulness","from ..mna","from ..independent_dc"))
