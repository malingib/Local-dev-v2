"""
Stack Detector - analyzes project structure to detect tech stack.
"""
import json
from pathlib import Path
from typing import Dict, List, Set


def detect_stack(project_path: str) -> Dict[str, List[str]]:
    """
    Detect the tech stack of a project.
    
    Args:
        project_path: Path to the project directory
    
    Returns:
        Dict with 'stack', 'routes', and other detected info
    """
    path = Path(project_path)
    if not path.exists():
        return {"stack": [], "routes": [], "error": "Path not found"}
    
    stack: Set[str] = set()
    routes: List[str] = []
    
    # Check for package.json (Node.js projects)
    package_json = path / "package.json"
    if package_json.exists():
        try:
            with open(package_json) as f:
                pkg = json.load(f)
            
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            
            # Framework detection
            if "react" in deps:
                stack.add("react")
                if "next" in deps:
                    stack.add("nextjs")
                if "react-router-dom" in deps or "react-router" in deps:
                    stack.add("react-router")
            
            if "vue" in deps:
                stack.add("vue")
                if "nuxt" in deps:
                    stack.add("nuxt")
            
            if "svelte" in deps:
                stack.add("svelte")
                if "@sveltejs/kit" in deps:
                    stack.add("sveltekit")
            
            if "angular" in deps or "@angular/core" in deps:
                stack.add("angular")
            
            # Build tools
            if "vite" in deps:
                stack.add("vite")
            if "webpack" in deps:
                stack.add("webpack")
            if "rollup" in deps:
                stack.add("rollup")
            
            # Styling
            if "tailwindcss" in deps:
                stack.add("tailwindcss")
            if "styled-components" in deps:
                stack.add("styled-components")
            if "sass" in deps or "node-sass" in deps:
                stack.add("sass")
            
            # State management
            if "redux" in deps:
                stack.add("redux")
            if "zustand" in deps:
                stack.add("zustand")
            if "mobx" in deps:
                stack.add("mobx")
            
            # Testing
            if "jest" in deps:
                stack.add("jest")
            if "vitest" in deps:
                stack.add("vitest")
            if "cypress" in deps:
                stack.add("cypress")
            if "@playwright/test" in deps:
                stack.add("playwright")
            
            # TypeScript
            if "typescript" in deps:
                stack.add("typescript")
            
            # Backend frameworks
            if "express" in deps:
                stack.add("express")
            if "fastify" in deps:
                stack.add("fastify")
            if "koa" in deps:
                stack.add("koa")
            if "nest" in deps:
                stack.add("nestjs")
            
        except Exception:
            pass
    
    # Python projects
    requirements = path / "requirements.txt"
    pyproject = path / "pyproject.toml"
    setup_py = path / "setup.py"
    
    if requirements.exists() or pyproject.exists() or setup_py.exists():
        stack.add("python")
        
        # Check requirements.txt
        if requirements.exists():
            try:
                content = requirements.read_text().lower()
                if "django" in content:
                    stack.add("django")
                if "flask" in content:
                    stack.add("flask")
                if "fastapi" in content:
                    stack.add("fastapi")
                if "sqlalchemy" in content:
                    stack.add("sqlalchemy")
                if "pytest" in content:
                    stack.add("pytest")
            except Exception:
                pass
        
        # Check pyproject.toml
        if pyproject.exists():
            try:
                content = pyproject.read_text().lower()
                if "django" in content:
                    stack.add("django")
                if "flask" in content:
                    stack.add("flask")
                if "fastapi" in content:
                    stack.add("fastapi")
            except Exception:
                pass
    
    # Check for specific files
    if (path / "manage.py").exists():
        stack.add("django")
    if (path / "app.py").exists() or (path / "wsgi.py").exists():
        if "flask" not in stack:
            stack.add("python-web")
    
    # Go projects
    if (path / "go.mod").exists():
        stack.add("go")
        try:
            content = (path / "go.mod").read_text()
            if "gin" in content:
                stack.add("gin")
            if "echo" in content:
                stack.add("echo")
            if "fiber" in content:
                stack.add("fiber")
        except Exception:
            pass
    
    # Ruby projects
    if (path / "Gemfile").exists():
        stack.add("ruby")
        try:
            content = (path / "Gemfile").read_text().lower()
            if "rails" in content:
                stack.add("rails")
            if "sinatra" in content:
                stack.add("sinatra")
        except Exception:
            pass
    
    # PHP projects
    if (path / "composer.json").exists():
        stack.add("php")
        try:
            with open(path / "composer.json") as f:
                composer = json.load(f)
            reqs = composer.get("require", {})
            if "laravel/framework" in reqs:
                stack.add("laravel")
            if "symfony" in str(reqs).lower():
                stack.add("symfony")
        except Exception:
            pass
    
    # Rust projects
    if (path / "Cargo.toml").exists():
        stack.add("rust")
        try:
            content = (path / "Cargo.toml").read_text().lower()
            if "actix" in content:
                stack.add("actix")
            if "rocket" in content:
                stack.add("rocket")
        except Exception:
            pass
    
    # Flutter
    if (path / "pubspec.yaml").exists():
        stack.add("flutter")
        stack.add("dart")
    
    # Docker
    if (path / "Dockerfile").exists() or (path / "docker-compose.yml").exists():
        stack.add("docker")
    
    # GitHub Actions
    if (path / ".github" / "workflows").exists():
        stack.add("github-actions")
    
    # Detect routes for common frameworks
    routes = _detect_routes(path, stack)
    
    return {
        "stack": sorted(list(stack)),
        "routes": routes,
    }


def _detect_routes(path: Path, stack: Set[str]) -> List[str]:
    """Detect routes for various frameworks."""
    routes = []
    
    # Next.js routes
    if "nextjs" in stack:
        app_dir = path / "app"
        pages_dir = path / "pages"
        
        if app_dir.exists():
            for f in app_dir.rglob("page.tsx"):
                rel = f.relative_to(app_dir).parent
                route = "/" + str(rel).replace("\\", "/") if str(rel) != "." else "/"
                routes.append(route)
        
        if pages_dir.exists():
            for f in pages_dir.rglob("*.tsx"):
                if f.name.startswith("_"):
                    continue
                rel = f.relative_to(pages_dir).parent / f.stem
                route = "/" + str(rel).replace("\\", "/")
                if route.endswith("/index"):
                    route = route[:-6]
                routes.append(route)
    
    # React Router routes (look for route definitions)
    if "react-router" in stack:
        # Try to find route definitions in common files
        for pattern in ["App.tsx", "App.jsx", "router.tsx", "routes.tsx"]:
            app_file = path / "src" / pattern
            if app_file.exists():
                try:
                    content = app_file.read_text()
                    # Simple regex to find route paths
                    import re
                    matches = re.findall(r'path=["\']([^"\']+)["\']', content)
                    routes.extend([m for m in matches if m not in routes])
                except Exception:
                    pass
    
    # Django routes
    if "django" in stack:
        urls_file = path / "urls.py"
        if urls_file.exists():
            try:
                content = urls_file.read_text()
                import re
                matches = re.findall(r'path\(["\']([^"\']+)["\']', content)
                routes.extend([m for m in matches if m not in routes])
            except Exception:
                pass
    
    # Flask routes
    if "flask" in stack:
        for py_file in path.rglob("*.py"):
            try:
                content = py_file.read_text()
                import re
                matches = re.findall(r'@app\.route\(["\']([^"\']+)["\']', content)
                routes.extend([m for m in matches if m not in routes])
            except Exception:
                pass
    
    return sorted(list(set(routes)))
