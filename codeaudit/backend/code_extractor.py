"""
Token-efficient code extraction — inspired by joshuaboyst/distil.
Extracts structured code analysis at 5 layers of depth:
  L1: AST (functions, classes, imports, signatures)
  L2: Call graph (who calls what)
  L3: Control flow graph (branches, loops, complexity)
  L4: Data flow graph (def-use chains)
  L5: Program slicing (backward/forward from a line)

Each layer adds detail so you request only what the task needs.
Reduces context by ~95% compared to dumping raw source.
"""
import ast
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Set, Tuple
from collections import defaultdict


# ── L1: AST Extraction ───────────────────────────────────────────────────

def extract_ast(file_path: str) -> Dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        return {"error": "File not found"}

    ext = path.suffix.lower()
    try:
        content = path.read_text(errors="ignore", encoding="utf-8")
    except Exception as e:
        return {"error": str(e)}

    if ext == ".py":
        return _extract_python_ast(content, file_path)
    elif ext in (".js", ".jsx", ".ts", ".tsx"):
        return _extract_js_ts_ast(content, file_path, ext)
    else:
        return _extract_generic(content, file_path)


def _extract_python_ast(content: str, file_path: str) -> Dict[str, Any]:
    result = {
        "file": file_path, "language": "python", "type": "ast",
        "imports": [], "classes": [], "functions": [],
        "tokens_approx": len(content) // 4,
    }

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        result["error"] = f"Syntax error: {e}"
        return result

    def _node_name(n):
        if isinstance(n, ast.Name):
            return n.id
        if isinstance(n, ast.Attribute):
            return f"{_node_name(n.value)}.{n.attr}"
        if isinstance(n, ast.Subscript):
            return f"{_node_name(n.value)}[{_node_name(n.slice)}]"
        return "..."

    def _param_name(a):
        if isinstance(a, ast.arg):
            return a.arg
        return str(a)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result["imports"].append({
                    "name": alias.name, "alias": alias.asname,
                    "line": node.lineno,
                })

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                result["imports"].append({
                    "name": f"{node.module or ''}.{alias.name}",
                    "alias": alias.asname, "line": node.lineno,
                })

        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in ast.iter_child_nodes(node):
                if isinstance(item, ast.FunctionDef):
                    params = [_param_name(a) for a in item.args.args]
                    methods.append({
                        "name": item.name, "params": params,
                        "line": item.lineno,
                    })
            result["classes"].append({
                "name": node.name,
                "bases": [_node_name(b) for b in node.bases],
                "line": node.lineno, "methods": methods,
            })

        elif isinstance(node, ast.FunctionDef):
            def is_method(n, tree):
                for p in ast.walk(tree):
                    if isinstance(p, ast.ClassDef):
                        for child in ast.iter_child_nodes(p):
                            if child is n:
                                return True
                return False
            if not is_method(node, tree):
                params = [_param_name(a) for a in node.args.args]
                result["functions"].append({
                    "name": node.name, "params": params,
                    "line": node.lineno, "returns": None,
                })

    result["tokens_approx"] = _count_tokens(result)
    return result


def _extract_js_ts_ast(content: str, file_path: str, ext: str) -> Dict[str, Any]:
    lang = "typescript" if ext in (".ts", ".tsx") else "javascript"
    result = {
        "file": file_path, "language": lang, "type": "ast",
        "imports": [], "classes": [], "functions": [],
        "tokens_approx": len(content) // 4,
    }

    for m in re.finditer(r'(?:import\s+(\{?\s*[\w\s,]+}?)\s+from\s+)?["\']([^"\']+)["\']', content):
        result["imports"].append({
            "name": m.group(2),
            "symbols": (m.group(1) or "").strip(),
            "line": content[:m.start()].count("\n") + 1,
        })

    for m in re.finditer(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(', content):
        params_str = _extract_params(content, m.end())
        result["functions"].append({
            "name": m.group(1), "params": params_str,
            "line": content[:m.start()].count("\n") + 1,
        })

    for m in re.finditer(r'(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?', content):
        result["classes"].append({
            "name": m.group(1),
            "extends": m.group(2),
            "line": content[:m.start()].count("\n") + 1,
        })

    result["tokens_approx"] = _count_tokens(result)
    return result


def _extract_generic(content: str, file_path: str) -> Dict[str, Any]:
    ext = Path(file_path).suffix.lower()
    result = {
        "file": file_path, "language": ext.lstrip(".") or "unknown",
        "type": "ast", "imports": [], "classes": [], "functions": [],
        "tokens_approx": len(content) // 4,
    }

    for m in re.finditer(r'(?:fn|func|def|function)\s+(\w+)\s*\(', content):
        result["functions"].append({
            "name": m.group(1),
            "line": content[:m.start()].count("\n") + 1,
        })

    for m in re.finditer(r'(?:class|struct|trait|interface)\s+(\w+)', content):
        result["classes"].append({
            "name": m.group(1),
            "line": content[:m.start()].count("\n") + 1,
        })

    for m in re.finditer(r'(?:import|use|require)\s+["\']?([a-zA-Z0-9_./-]+)["\']?', content):
        result["imports"].append({
            "name": m.group(1),
            "line": content[:m.start()].count("\n") + 1,
        })

    result["tokens_approx"] = _count_tokens(result)
    return result


def _extract_params(content: str, start: int) -> List[str]:
    depth = 1
    i = start
    while i < len(content) and depth > 0:
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
        i += 1
    params_str = content[start:i - 1]
    return [p.strip() for p in params_str.split(",") if p.strip()]


def _count_tokens(ast_result: Dict[str, Any]) -> int:
    count = 50
    count += len(ast_result.get("imports", [])) * 5
    count += len(ast_result.get("functions", [])) * 15
    count += len(ast_result.get("classes", [])) * 20
    for cls in ast_result.get("classes", []):
        count += len(cls.get("methods", [])) * 10
    return count


# ── L2: Call Graph ───────────────────────────────────────────────────────

def build_call_graph(project_path: str, file_paths: Optional[List[str]] = None) -> Dict[str, Any]:
    root = Path(project_path)
    if not root.exists():
        return {"error": "Project not found"}

    calls: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    defined: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    py_files = []
    if file_paths:
        py_files = [root / f for f in file_paths]
    else:
        py_files = list(root.rglob("*.py"))
        py_files = [f for f in py_files if "node_modules" not in str(f) and ".git" not in str(f)]

    for fp in py_files:
        if not fp.exists():
            continue
        try:
            content = fp.read_text(errors="ignore")
        except Exception:
            continue

        rel = str(fp.relative_to(root))

        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                defined[rel].append({
                    "name": node.name, "line": node.lineno,
                })
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            calls[rel].append({
                                "caller": node.name,
                                "callee": child.func.id,
                                "line": child.lineno,
                            })
                        elif isinstance(child.func, ast.Attribute):
                            callee = child.func.attr
                            calls[rel].append({
                                "caller": node.name,
                                "callee": callee,
                                "line": child.lineno,
                            })

    return {
        "type": "call_graph",
        "files_analyzed": len(py_files),
        "defined_functions": dict(defined),
        "calls": dict(calls),
        "tokens_approx": sum(len(v) * 8 for v in calls.values()) + sum(len(v) * 5 for v in defined.values()),
    }


# ── L3: Control Flow Graph ───────────────────────────────────────────────

def extract_cfg(file_path: str, function_name: Optional[str] = None) -> Dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        return {"error": "File not found"}

    try:
        content = path.read_text(errors="ignore")
        tree = ast.parse(content)
    except Exception as e:
        return {"error": str(e)}

    result = {
        "file": file_path, "type": "cfg",
        "functions": [], "tokens_approx": 0,
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if function_name and node.name != function_name:
                continue

            blocks = _analyze_control_flow(node)
            complexity = _compute_cyclomatic(node)

            result["functions"].append({
                "name": node.name,
                "line": node.lineno,
                "blocks": blocks,
                "cyclomatic_complexity": complexity,
                "has_loops": any(b["type"] == "loop" for b in blocks),
                "has_conditionals": any(b["type"] == "branch" for b in blocks),
                "has_exceptions": any(b["type"] == "try" for b in blocks),
            })

    result["tokens_approx"] = sum(
        f["cyclomatic_complexity"] * 5 + len(f["blocks"]) * 3
        for f in result["functions"]
    )
    return result


def _analyze_control_flow(node: ast.AST) -> List[Dict[str, Any]]:
    blocks = []
    for child in ast.walk(node):
        if isinstance(child, ast.If):
            blocks.append({
                "type": "branch", "line": child.lineno,
                "condition": "...",
            })
        elif isinstance(child, (ast.For, ast.While)):
            blocks.append({
                "type": "loop", "line": child.lineno,
                "kind": "for" if isinstance(child, ast.For) else "while",
            })
        elif isinstance(child, (ast.Try, ast.ExceptHandler)):
            blocks.append({
                "type": "try", "line": child.lineno,
            })
        elif isinstance(child, (ast.Return,)):
            blocks.append({
                "type": "return", "line": child.lineno,
            })
    return blocks


def _compute_cyclomatic(node: ast.AST) -> int:
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                               ast.With, ast.Assert)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity


# ── L4: Data Flow Graph ──────────────────────────────────────────────────

def extract_df(project_path: str, file_path: str) -> Dict[str, Any]:
    path = Path(project_path) / file_path
    if not path.exists():
        return {"error": "File not found"}

    try:
        content = path.read_text(errors="ignore")
        tree = ast.parse(content)
    except Exception as e:
        return {"error": str(e)}

    result = {
        "file": file_path, "type": "data_flow",
        "def_use_chains": [], "tokens_approx": 0,
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defs = []
            uses = []

            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name):
                            defs.append({
                                "var": target.id, "line": child.lineno,
                                "kind": "assignment",
                            })
                elif isinstance(child, ast.AugAssign):
                    if isinstance(child.target, ast.Name):
                        defs.append({
                            "var": child.target.id,
                            "line": child.lineno,
                            "kind": "augmented",
                        })
                elif isinstance(child, ast.Name):
                    if isinstance(child.ctx, ast.Load):
                        uses.append({
                            "var": child.id, "line": child.lineno,
                        })

            chain = {"function": node.name, "defs": defs, "uses": uses}
            result["def_use_chains"].append(chain)

    result["tokens_approx"] = sum(
        len(c["defs"]) * 4 + len(c["uses"]) * 2
        for c in result["def_use_chains"]
    )
    return result


# ── L5: Program Slicing ──────────────────────────────────────────────────

def slice_file(file_path: str, target_line: int, direction: str = "backward") -> Dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        return {"error": "File not found"}

    try:
        content = path.read_text(errors="ignore")
        lines = content.splitlines()
        tree = ast.parse(content)
    except Exception as e:
        return {"error": str(e)}

    target_line_0 = target_line - 1

    relevant_lines: Set[int] = set()
    relevant_lines.add(target_line_0)

    if direction in ("backward", "both"):
        relevant_lines.update(_slice_backward(tree, target_line))

    if direction in ("forward", "both"):
        relevant_lines.update(_slice_forward(tree, target_line))

    if direction == "backward":
        relevant_lines = {l for l in relevant_lines if l <= target_line_0}

    relevant_lines = sorted(relevant_lines)
    sliced = [lines[i] for i in relevant_lines if i < len(lines)]

    context_lines = []
    for i in relevant_lines:
        if i < len(lines):
            marker = ">>>" if i == target_line_0 else "   "
            context_lines.append({"line": i + 1, "content": lines[i], "is_target": i == target_line_0})

    return {
        "file": file_path, "type": "slice",
        "target_line": target_line,
        "direction": direction,
        "original_lines": len(lines),
        "sliced_lines": len(sliced),
        "compression_ratio": round((1 - len(sliced) / max(len(lines), 1)) * 100, 1),
        "context": context_lines,
    }


def _slice_backward(tree: ast.AST, target_line: int) -> Set[int]:
    lines = set()
    target_var = None

    for node in ast.walk(tree):
        if hasattr(node, 'lineno') and node.lineno == target_line:
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                target_var = node.id

    if target_var:
        for node in ast.walk(tree):
            if hasattr(node, 'lineno') and node.lineno < target_line:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == target_var:
                            lines.add(node.lineno - 1)
                elif isinstance(node, ast.FunctionDef) and node.name == target_var:
                    lines.add(node.lineno - 1)
                    lines.update(range(node.lineno, node.end_lineno or node.lineno + 5))

    parent_func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and hasattr(node, 'lineno'):
            end = node.end_lineno or node.lineno + 5
            if node.lineno <= target_line <= end:
                parent_func = node
                break

    if parent_func:
        lines.add(parent_func.lineno - 1)
        for child in ast.walk(parent_func):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                if hasattr(child, 'lineno'):
                    lines.add(child.lineno - 1)

    return lines


def _slice_forward(tree: ast.AST, target_line: int) -> Set[int]:
    lines = set()
    target_vars = set()

    for node in ast.walk(tree):
        if hasattr(node, 'lineno') and node.lineno == target_line:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        target_vars.add(target.id)

    if target_vars:
        for node in ast.walk(tree):
            if hasattr(node, 'lineno') and node.lineno > target_line:
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    if node.id in target_vars:
                        lines.add(node.lineno - 1)

    parent_func = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and hasattr(node, 'lineno'):
            end = node.end_lineno or node.lineno + 5
            if node.lineno <= target_line <= end:
                parent_func = node
                break

    if parent_func:
        end = parent_func.end_lineno or parent_func.lineno + 5
        lines.update(range(target_line, min(end, target_line + 10)))

    return lines


# ── Convenience: Extract all layers ──────────────────────────────────────

def extract_all(file_path: str) -> Dict[str, Any]:
    ast_result = extract_ast(file_path)
    if "error" in ast_result:
        return ast_result

    project = str(Path(file_path).parent)
    rel = Path(file_path).name

    call_graph = build_call_graph(project, [rel])
    cfg = extract_cfg(file_path)

    total_tokens = (
        ast_result.get("tokens_approx", 0) +
        call_graph.get("tokens_approx", 0) +
        cfg.get("tokens_approx", 0)
    )

    raw_tokens = len(Path(file_path).read_text(errors="ignore")) // 4

    return {
        "file": file_path,
        "layers": {
            "L1_ast": ast_result,
            "L2_call_graph": call_graph,
            "L3_cfg": cfg,
        },
        "summary": {
            "total_extracted_tokens": total_tokens,
            "raw_tokens": raw_tokens,
            "compression_ratio": round((1 - total_tokens / max(raw_tokens, 1)) * 100, 1),
        },
    }
