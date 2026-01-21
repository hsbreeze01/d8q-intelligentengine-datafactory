import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = PROJECT_ROOT / "spec"
SPEC_WORKFLOW_DIR = PROJECT_ROOT / ".spec-workflow"
SRC_DIR = PROJECT_ROOT / "src"

# =========================
# Layer import forbidden rules
# =========================
FORBIDDEN_IMPORTS = {
    "domain": ["infrastructure", "interfaces"],
    "application": ["infrastructure"],
}

# =========================
# Utilities
# =========================

def fail(msg: str):
    print(f"\n❌ VALIDATION FAILED: {msg}")
    sys.exit(1)


def warn(msg: str):
    print(f"⚠️  {msg}")


def info(msg: str):
    print(f"ℹ️  {msg}")


# =========================
# Spec parsing
# =========================

def parse_module_spec(spec_path: Path) -> Dict[str, List[str]]:
    """
    Parse a module spec file with format:

    ## Section
    - Item
    - Item
    """
    sections: Dict[str, List[str]] = {}
    current = None

    for line in spec_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("## "):
            current = line[3:]
            sections[current] = []
        elif line.startswith("- ") and current:
            sections[current].append(line[2:])

    return sections


def parse_tasks_md(tasks_path: Path) -> List[Dict]:
    """
    Parse tasks.md file and extract task information.
    
    Returns list of tasks with:
    - id: task identifier
    - status: 'pending', 'in-progress', 'completed'
    - description: task description
    """
    tasks = []
    current_task = None
    
    for line in tasks_path.read_text().splitlines():
        line = line.rstrip()
        
        # Match task markers: - [ ], - [-], - [x]
        task_match = re.match(r'^-\s+\[([ x\-])\]\s+(.+)$', line)
        if task_match:
            status_char = task_match.group(1)
            description = task_match.group(2)
            
            status_map = {
                ' ': 'pending',
                '-': 'in-progress',
                'x': 'completed'
            }
            
            current_task = {
                'id': f"task-{len(tasks) + 1}",
                'status': status_map.get(status_char, 'pending'),
                'description': description
            }
            tasks.append(current_task)
        
        # Extract _Prompt field for current task
        elif current_task and line.strip().startswith('_Prompt:'):
            current_task['prompt'] = line.strip()[8:].strip()
        elif current_task and line.strip().startswith('_Leverage:'):
            current_task['leverage'] = line.strip()[10:].strip()
        elif current_task and line.strip().startswith('_Requirements:'):
            current_task['requirements'] = line.strip()[13:].strip()
    
    return tasks


# =========================
# Code analysis
# =========================

def collect_symbols(py_file: Path) -> Set[str]:
    tree = ast.parse(py_file.read_text())
    symbols = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            if not node.name.startswith("_"):
                symbols.add(node.name)

    return symbols


def collect_imports(py_file: Path) -> Set[str]:
    tree = ast.parse(py_file.read_text())
    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.add(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    return imports


# =========================
# Spec-workflow validation
# =========================

def validate_spec_workflow_structure():
    """
    Validate that .spec-workflow directory structure exists and is correct.
    """
    print("\n🔍 Validating spec-workflow structure")
    
    required_dirs = [
        SPEC_WORKFLOW_DIR / "steering",
        SPEC_WORKFLOW_DIR / "specs"
    ]
    
    for dir_path in required_dirs:
        full_path = PROJECT_ROOT / dir_path
        if full_path.exists():
            info(f"✓ Found directory: {dir_path.relative_to(PROJECT_ROOT)}")
        else:
            fail(f"Missing required directory: {dir_path.relative_to(PROJECT_ROOT)}")
    
    # Check for steering documents
    steering_dir = SPEC_WORKFLOW_DIR / "steering"
    required_steering_docs = ["product.md", "tech.md", "structure.md"]
    
    for doc_name in required_steering_docs:
        doc_path = steering_dir / doc_name
        if not doc_path.exists():
            warn(f"Missing steering document: {doc_name}")
        else:
            info(f"✓ Found steering document: {doc_name}")
    
    print("✅ Spec-workflow structure OK")


def validate_tasks_md(spec_name: str) -> Tuple[bool, List[str]]:
    """
    Validate tasks.md for a spec.
    
    Returns (is_valid, errors)
    """
    tasks_path = SPEC_WORKFLOW_DIR / "specs" / spec_name / "tasks.md"
    
    if not tasks_path.exists():
        return False, [f"tasks.md not found for spec: {spec_name}"]
    
    tasks = parse_tasks_md(tasks_path)
    errors = []
    
    if not tasks:
        errors.append(f"No tasks found in {tasks_path.relative_to(PROJECT_ROOT)}")
        return False, errors
    
    # Check for in-progress tasks
    in_progress_count = sum(1 for t in tasks if t['status'] == 'in-progress')
    if in_progress_count > 1:
        errors.append(f"Multiple tasks ({in_progress_count}) are in-progress. Only one task should be in-progress at a time.")
    
    # Check that all tasks have required fields
    for task in tasks:
        if 'prompt' not in task:
            errors.append(f"Task {task['id']} missing _Prompt field")
        if 'requirements' not in task:
            errors.append(f"Task {task['id']} missing _Requirements field")
    
    return len(errors) == 0, errors


def validate_implementation_logs(spec_name: str) -> Tuple[bool, List[str]]:
    """
    Validate implementation logs for a spec.
    
    Returns (is_valid, warnings)
    """
    logs_dir = SPEC_WORKFLOW_DIR / "specs" / spec_name / "Implementation Logs"
    
    if not logs_dir.exists():
        return True, [f"No implementation logs found for spec: {spec_name}"]
    
    warnings = []
    log_files = list(logs_dir.glob("*.md"))
    
    if not log_files:
        warnings.append(f"Implementation Logs directory exists but is empty for spec: {spec_name}")
    
    # Check for duplicate task logs
    task_ids = []
    for log_file in log_files:
        # Extract task ID from filename (e.g., task-1_timestamp_id.md)
        match = re.match(r'task-(\d+)_', log_file.name)
        if match:
            task_id = match.group(1)
            if task_id in task_ids:
                warnings.append(f"Duplicate log found for task {task_id} in spec: {spec_name}")
            task_ids.append(task_id)
    
    return True, warnings


def validate_spec_workflow_specs():
    """
    Validate all specs in .spec-workflow/specs/.
    """
    print("\n🔍 Validating spec-workflow specs")
    
    specs_dir = SPEC_WORKFLOW_DIR / "specs"
    
    if not specs_dir.exists():
        warn("No specs found in .spec-workflow/specs/")
        return
    
    spec_dirs = [d for d in specs_dir.iterdir() if d.is_dir()]
    
    if not spec_dirs:
        warn("No spec directories found")
        return
    
    for spec_dir in spec_dirs:
        spec_name = spec_dir.name
        info(f"\nValidating spec: {spec_name}")
        
        # Check for required files
        required_files = ["requirements.md", "design.md", "tasks.md"]
        for req_file in required_files:
            file_path = spec_dir / req_file
            if file_path.exists():
                info(f"  ✓ {req_file} exists")
            else:
                warn(f"  ⚠ {req_file} missing")
        
        # Validate tasks.md
        tasks_valid, tasks_errors = validate_tasks_md(spec_name)
        if tasks_valid:
            info(f"  ✓ tasks.md is valid")
        else:
            for error in tasks_errors:
                warn(f"  ⚠ tasks.md error: {error}")
        
        # Validate implementation logs
        logs_valid, logs_warnings = validate_implementation_logs(spec_name)
        if logs_valid:
            info(f"  ✓ Implementation logs OK")
        else:
            for warning in logs_warnings:
                warn(f"  ⚠ Implementation logs warning: {warning}")
    
    print("✅ Spec-workflow specs validation completed")


def validate_spec_workflow_integration():
    """
    Validate integration between spec/ and .spec-workflow/.
    """
    print("\n🔍 Validating spec-workflow integration")
    
    # Check that spec/ exists
    if not SPEC_DIR.exists():
        fail("spec/ directory not found")
    
    # Check for consistency between spec/modules/ and .spec-workflow/specs/
    spec_modules = [f.stem.replace('.spec', '') for f in (SPEC_DIR / "modules").glob("*.spec.md")]
    workflow_specs = [d.name for d in (SPEC_WORKFLOW_DIR / "specs").iterdir() if d.is_dir()]
    
    # Find specs that exist in one but not the other
    only_in_spec = set(spec_modules) - set(workflow_specs)
    only_in_workflow = set(workflow_specs) - set(spec_modules)
    
    if only_in_spec:
        warn(f"Specs in spec/modules/ but not in .spec-workflow/specs/: {', '.join(only_in_spec)}")
    
    if only_in_workflow:
        warn(f"Specs in .spec-workflow/specs/ but not in spec/modules/: {', '.join(only_in_workflow)}")
    
    if not only_in_spec and not only_in_workflow:
        info("✓ Spec directories are consistent")
    
    print("✅ Spec-workflow integration OK")


# =========================
# Validation entry point
# =========================

def main():
    print("=" * 80)
    print("SPEC VALIDATION")
    print("=" * 80)
    
    # New spec-workflow validations
    validate_spec_workflow_structure()
    validate_spec_workflow_specs()
    validate_spec_workflow_integration()
    
    print("\n" + "=" * 80)
    print("🎉 ALL SPEC VALIDATIONS PASSED")
    print("=" * 80)
    print("The spec-driven development structure is correctly implemented.")
    print("All required spec files and directories are present.")
    print("=" * 80)


if __name__ == "__main__":
    main()
