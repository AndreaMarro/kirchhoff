import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TRUTH=ROOT/"src/kirchhoff/domain/truthfulness.py"
EXECUTE=ROOT/"src/kirchhoff/domain/didactic/execute.py"

def test_truthfulness_domain_only():
    text=TRUTH.read_text()
    tree=ast.parse(text)
    imports=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node,ast.ImportFrom):
            imports.append(node.module)
    assert not any(x and ("pipeline" in x or "render" in x or "adapter" in x) for x in imports)
    assert "pianifica(" not in text

def test_execute_has_no_oracle():
    text=EXECUTE.read_text()
    assert all(word not in text for word in ("solve_dc","solve_dc_tableau","truthfulness","from ..mna","from ..independent_dc"))


def test_one_shared_comparator_and_no_private_pipeline_copy():
    source = ROOT / "src"
    definitions = sum(path.read_text(encoding="utf-8").count("def compare_exact_solution_paths") for path in source.rglob("*.py"))
    assert definitions == 1
    assert "_confronta_percorsi" not in (source / "kirchhoff/pipeline/resolve.py").read_text(encoding="utf-8")
