"""
Knowledge Graph Pipeline — inspired by Lum1104/Understand-Anything.
Multi-agent pipeline that scans projects, builds a knowledge graph
of files, functions, classes, imports, and dependencies.
Also includes graphify-style multi-modal document support.
"""
import ast
import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any, Set, Tuple
from collections import defaultdict

from backend.constants import IGNORE_DIRS
from backend.llm_router import llm_call


GRAPH_NODES: List[Dict[str, Any]] = []
GRAPH_EDGES: List[Dict[str, Any]] = []
_GRAPH_CACHE: Dict[str, Any] = {}


def _get_graph_dir() -> Path:
    d = Path.home() / ".codeaudit" / "knowledge_graph"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _node_id(prefix: str, name: str) -> str:
    safe = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    return f"{prefix}:{safe}"


def _add_node(node_id: str, label: str, node_type: str, metadata: Dict[str, Any] = None):
    if not any(n["id"] == node_id for n in GRAPH_NODES):
        GRAPH_NODES.append({
            "id": node_id, "label": label, "type": node_type,
            "metadata": metadata or {},
        })


def _add_edge(source: str, target: str, rel: str, metadata: Dict[str, Any] = None):
    GRAPH_EDGES.append({
        "source": source, "target": target, "relation": rel,
        "metadata": metadata or {},
    })


# ── Project Scanner ──────────────────────────────────────────────────────

def scan_project(project_path: str) -> Dict[str, Any]:
    global GRAPH_NODES, GRAPH_EDGES
    GRAPH_NODES = []
    GRAPH_EDGES = []

    root = Path(project_path)
    if not root.exists():
        return {"error": "Project not found", "nodes": [], "edges": []}

    _add_node("project", root.name, "project", {"path": str(root)})

    for p in sorted(root.rglob("*")):
        if p.is_dir():
            continue
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        rel = str(p.relative_to(root))
        ext = p.suffix.lower()
        size = p.stat().st_size

        file_id = _node_id("file", rel)
        _add_node(file_id, p.name, "file", {
            "path": rel, "extension": ext, "size": size,
        })
        _add_edge("project", file_id, "contains")

        if ext in ('.py', '.js', '.ts', '.tsx', '.jsx', '.rs', '.go', '.java', '.vue', '.svelte'):
            _analyze_code_file(p, root, rel, ext)
        elif ext in ('.md', '.rst', '.txt'):
            _analyze_doc_file(p, root, rel)
        elif ext in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'):
            _add_node(file_id, p.name, "image",
                       {"path": rel, "size": size})

    graph = {"nodes": GRAPH_NODES, "edges": GRAPH_EDGES}
    _save_graph(project_path, graph)
    return graph


# ── Code File Analyzer ───────────────────────────────────────────────────

def _analyze_code_file(file_path: Path, root: Path, rel: str, ext: str):
    try:
        content = file_path.read_text(errors="ignore", encoding="utf-8")
    except Exception:
        return

    file_id = _node_id("file", rel)

    if ext == '.py':
        _analyze_python(content, file_id, root, rel)
    elif ext in ('.js', '.jsx', '.ts', '.tsx'):
        _analyze_js_ts(content, file_id, root, rel, ext)
    elif ext == '.rs':
        _analyze_rust(content, file_id, root, rel)
    elif ext == '.go':
        _analyze_go(content, file_id, root, rel)


def _analyze_python(content: str, file_id: str, root: Path, rel: str):
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_id = _node_id("function", f"{rel}:{node.name}")
                _add_node(func_id, node.name, "function", {
                    "file": rel, "line": node.lineno,
                })
                _add_edge(file_id, func_id, "defines")

                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name):
                        dep_id = _node_id("external", decorator.id)
                        _add_edge(func_id, dep_id, "uses")

            elif isinstance(node, ast.ClassDef):
                cls_id = _node_id("class", f"{rel}:{node.name}")
                _add_node(cls_id, node.name, "class", {
                    "file": rel, "line": node.lineno,
                })
                _add_edge(file_id, cls_id, "defines")

                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_id = _node_id("class", base.id)
                        _add_edge(cls_id, base_id, "extends")

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    dep_id = _node_id("module", alias.name)
                    _add_node(dep_id, alias.name, "module")
                    _add_edge(file_id, dep_id, "imports")

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full = f"{module}.{alias.name}" if module else alias.name
                    dep_id = _node_id("module", full)
                    _add_node(dep_id, full, "module")
                    _add_edge(file_id, dep_id, "imports")
    except SyntaxError:
        pass


def _analyze_js_ts(content: str, file_id: str, root: Path, rel: str, ext: str):
    patterns = [
        (r'(?:export\s+)?(?:async\s+)?function\s+(\w+)', "function"),
        (r'(?:export\s+)?class\s+(\w+)', "class"),
        (r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*[=:]', "variable"),
        (r'interface\s+(\w+)', "interface"),
        (r'type\s+(\w+)\s*=', "type"),
        (r'import\s+\{?\s*[\w\s,]*\}?\s+from\s+["\']([^"\']+)', "import"),
        (r'require\(["\']([^"\']+)["\']\)', "require"),
    ]

    for pattern, kind in patterns:
        for m in re.finditer(pattern, content):
            name = m.group(1)
            if kind in ("import", "require"):
                dep_id = _node_id("module", name)
                _add_node(dep_id, name, "module")
                _add_edge(file_id, dep_id, "imports")
            else:
                node_id = _node_id(kind, f"{rel}:{name}")
                _add_node(node_id, name, kind, {"file": rel})
                _add_edge(file_id, node_id, "defines")


def _analyze_rust(content: str, file_id: str, root: Path, rel: str):
    patterns = [
        (r'(?:pub\s+)?fn\s+(\w+)', "function"),
        (r'(?:pub\s+)?struct\s+(\w+)', "struct"),
        (r'(?:pub\s+)?enum\s+(\w+)', "enum"),
        (r'(?:pub\s+)?trait\s+(\w+)', "trait"),
        (r'(?:pub\s+)?mod\s+(\w+)', "module"),
        (r'use\s+([\w:]+)', "use"),
    ]
    for pattern, kind in patterns:
        for m in re.finditer(pattern, content):
            name = m.group(1)
            if kind == "use":
                dep_id = _node_id("module", name)
                _add_node(dep_id, name, "module")
                _add_edge(file_id, dep_id, "uses")
            else:
                node_id = _node_id(kind, f"{rel}:{name}")
                _add_node(node_id, name, kind, {"file": rel})
                _add_edge(file_id, node_id, "defines")


def _analyze_go(content: str, file_id: str, root: Path, rel: str):
    patterns = [
        (r'func\s+(\w+)', "function"),
        (r'type\s+(\w+)\s+struct', "struct"),
        (r'type\s+(\w+)\s+interface', "interface"),
        (r'import\s+\(?([^)]+)\)?', "import"),
    ]
    for pattern, kind in patterns:
        for m in re.finditer(pattern, content):
            name = m.group(1).strip()
            if kind == "import":
                for imp in re.findall(r'"([^"]+)"', name):
                    dep_id = _node_id("module", imp)
                    _add_node(dep_id, imp, "module")
                    _add_edge(file_id, dep_id, "imports")
            else:
                node_id = _node_id(kind, f"{rel}:{name}")
                _add_node(node_id, name, kind, {"file": rel})
                _add_edge(file_id, node_id, "defines")


# ── Document Analyzer ────────────────────────────────────────────────────

def _analyze_doc_file(file_path: Path, root: Path, rel: str):
    try:
        content = file_path.read_text(errors="ignore", encoding="utf-8")
    except Exception:
        return

    file_id = _node_id("file", rel)
    lines = content.splitlines()
    _add_node(file_id, file_path.name, "document", {
        "path": rel, "lines": len(lines),
    })

    h1s = re.findall(r'^#\s+(.+)$', content, re.MULTILINE)
    for h1 in h1s[:5]:
        section_id = _node_id("section", f"{rel}:{h1}")
        _add_node(section_id, h1, "section", {"file": rel})
        _add_edge(file_id, section_id, "contains")

    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    for text, url in links[:20]:
        if url.startswith("http"):
            ref_id = _node_id("reference", url[:60])
            _add_node(ref_id, text, "reference", {"url": url})
            _add_edge(file_id, ref_id, "references")


# ── Architecture Analyzer ────────────────────────────────────────────────

def analyze_architecture(graph: Dict[str, Any]) -> Dict[str, Any]:
    layers = defaultdict(list)
    type_counts = defaultdict(int)
    dep_map = defaultdict(set)

    for node in graph.get("nodes", []):
        ntype = node["type"]
        type_counts[ntype] += 1
        path = node.get("metadata", {}).get("path", "")

        if "api" in path.lower() or "route" in path.lower() or "controller" in path.lower() or "handler" in path.lower():
            layers["api"].append(node["id"])
        elif "model" in path.lower() or "entity" in path.lower() or "schema" in path.lower():
            layers["data"].append(node["id"])
        elif "ui" in path.lower() or "component" in path.lower() or "view" in path.lower() or "page" in path.lower():
            layers["ui"].append(node["id"])
        elif "util" in path.lower() or "helper" in path.lower() or "lib" in path.lower():
            layers["utility"].append(node["id"])
        elif "test" in path.lower() or "spec" in path.lower() or "__test__" in path.lower():
            layers["test"].append(node["id"])
        else:
            layers["service"].append(node["id"])

    for edge in graph.get("edges", []):
        dep_map[edge["source"]].add(edge["target"])

    return {
        "layers": {k: len(v) for k, v in layers.items()},
        "node_types": dict(type_counts),
        "total_nodes": len(graph.get("nodes", [])),
        "total_edges": len(graph.get("edges", [])),
        "density": round(len(graph.get("edges", [])) / max(len(graph.get("nodes", [])), 1), 3),
    }


# ── Graph Persistence ────────────────────────────────────────────────────

def _save_graph(project_path: str, graph: Dict[str, Any]):
    project_name = Path(project_path).name
    path = _get_graph_dir() / f"{project_name}.json"
    path.write_text(json.dumps(graph, indent=2, default=str))


def load_graph(project_path: str) -> Optional[Dict[str, Any]]:
    project_name = Path(project_path).name
    path = _get_graph_dir() / f"{project_name}.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
    return None


def list_graphs() -> List[Dict[str, Any]]:
    results = []
    for p in _get_graph_dir().glob("*.json"):
        try:
            data = json.loads(p.read_text())
            arch = analyze_architecture(data)
            results.append({
                "name": p.stem,
                "nodes": arch["total_nodes"],
                "edges": arch["total_edges"],
                "layers": arch["layers"],
                "node_types": arch["node_types"],
                "updated": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
            })
        except Exception:
            continue
    return results


# ── Graph Queries ────────────────────────────────────────────────────────

def query_graph(project_path: str, node_type: Optional[str] = None,
                search: Optional[str] = None) -> Dict[str, Any]:
    graph = load_graph(project_path)
    if not graph:
        return {"nodes": [], "edges": []}

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if node_type:
        nodes = [n for n in nodes if n["type"] == node_type]

    if search:
        q = search.lower()
        nodes = [n for n in nodes if q in n["label"].lower() or
                 q in n.get("metadata", {}).get("path", "").lower()]

    node_ids = {n["id"] for n in nodes}
    edges = [e for e in edges if e["source"] in node_ids and e["target"] in node_ids]

    return {"nodes": nodes, "edges": edges}


def get_file_dependencies(project_path: str, file_path: str) -> Dict[str, Any]:
    graph = load_graph(project_path)
    if not graph:
        return {"imports": [], "dependents": []}

    file_id = _node_id("file", file_path)

    imports = []
    dependents = []

    for edge in graph.get("edges", []):
        if edge["source"] == file_id and edge["relation"] in ("imports", "uses", "requires"):
            target_node = next((n for n in graph["nodes"] if n["id"] == edge["target"]), None)
            if target_node:
                imports.append({"name": target_node["label"], "type": edge["relation"]})
        if edge["target"] == file_id and edge["relation"] == "contains":
            source_node = next((n for n in graph["nodes"] if n["id"] == edge["source"]), None)
            if source_node and source_node["type"] != "project":
                dependents.append(source_node["label"])

    return {"imports": imports, "dependents": dependents}


# ── Multi-Modal: Graphify-style Doc/Image support ────────────────────────

def index_document(file_path: str, content: str = "") -> Dict[str, Any]:
    path = Path(file_path)
    if not path.exists() and not content:
        return {"error": "File not found"}

    if content:
        text = content
    else:
        try:
            text = path.read_text(errors="ignore", encoding="utf-8")
        except Exception as e:
            return {"error": str(e)}

    ext = path.suffix.lower()
    rel = str(path)

    doc_id = _node_id("doc", rel)
    _add_node(doc_id, path.name, "document", {
        "path": rel, "type": ext, "size": len(text),
    })

    sections = []
    if ext == ".md":
        headings = re.findall(r'^(#{1,6})\s+(.+)$', text, re.MULTILINE)
        for level, heading in headings:
            sections.append({"level": len(level), "heading": heading})
            section_id = _node_id("section", f"{rel}:{heading}")
            _add_node(section_id, heading, "section", {"level": len(level)})
            _add_edge(doc_id, section_id, "contains")

    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
    for link_text, url in links[:20]:
        ref_id = _node_id("ref", url[:60])
        _add_node(ref_id, link_text, "link", {"url": url})
        _add_edge(doc_id, ref_id, "links_to")

    code_blocks = re.findall(r'```(\w*)\n(.*?)```', text, re.DOTALL)
    code_count = len(code_blocks)
    code_langs = list(set(cb[0] for cb in code_blocks if cb[0]))

    result = {
        "id": doc_id,
        "title": path.name,
        "sections": len(sections),
        "links": len(links),
        "code_blocks": code_count,
        "code_languages": code_langs,
    }

    _save_graph("_documents", {"nodes": GRAPH_NODES, "edges": GRAPH_EDGES})
    return result


def search_documents(query: str) -> List[Dict[str, Any]]:
    graphs = []
    for p in _get_graph_dir().glob("*.json"):
        try:
            data = json.loads(p.read_text())
            graphs.append(data)
        except Exception:
            continue

    results = []
    q = query.lower()
    for graph in graphs:
        for node in graph.get("nodes", []):
            if q in node["label"].lower() or q in node.get("metadata", {}).get("path", "").lower():
                results.append(node)
    return results[:50]
