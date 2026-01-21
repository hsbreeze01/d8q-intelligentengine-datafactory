import sys
from pathlib import Path
from typing import List, Set


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = PROJECT_ROOT / "spec"
SRC_DIR = PROJECT_ROOT / "src"

# =========================
# Expected structure
# =========================

def get_expected_structure() -> Set[str]:
    """
    Get the expected directory structure based on spec files.
    """
    expected = set()
    
    # Add base directories
    expected.add("spec")
    expected.add("spec/layers")
    expected.add("spec/modules")
    expected.add("src")
    expected.add("src/d8q_intelligentengine_datafactory")
    expected.add("src/d8q_intelligentengine_datafactory/domain")
    expected.add("src/d8q_intelligentengine_datafactory/application")
    expected.add("src/d8q_intelligentengine_datafactory/infrastructure")
    expected.add("src/d8q_intelligentengine_datafactory/interfaces")
    expected.add("scripts")
    expected.add("tests")
    expected.add("docs")
    expected.add("frontend")
    expected.add(".spec-workflow")
    expected.add(".spec-workflow/steering")
    expected.add(".spec-workflow/specs")
    
    return expected

# =========================
# Utilities
# =========================

def fail(msg: str):
    print(f"\n❌ STRUCTURE VALIDATION FAILED: {msg}")
    sys.exit(1)


def warn(msg: str):
    print(f"⚠️  {msg}")


def info(msg: str):
    print(f"ℹ️  {msg}")


# =========================
# Validation functions
# =========================

def validate_base_structure():
    """
    Validate the base directory structure.
    """
    print("\n🔍 Validating base directory structure")
    
    expected = get_expected_structure()
    
    for dir_path in expected:
        full_path = PROJECT_ROOT / dir_path
        if full_path.exists():
            info(f"✓ Found directory: {dir_path}")
        else:
            fail(f"Missing expected directory: {dir_path}")
    
    print("✅ Base structure OK")


def validate_spec_files():
    """
    Validate that all required spec files exist.
    """
    print("\n🔍 Validating spec files")
    
    required_specs = [
        "spec/system.spec.md",
        "spec/layers/domain.spec.md",
        "spec/layers/application.spec.md",
        "spec/layers/infrastructure.spec.md",
        "spec/layers/interfaces.spec.md",
    ]
    
    for spec_file in required_specs:
        full_path = PROJECT_ROOT / spec_file
        if full_path.exists():
            info(f"✓ Found spec file: {spec_file}")
        else:
            fail(f"Missing required spec file: {spec_file}")
    
    print("✅ Spec files OK")


def validate_steering_files():
    """
    Validate that all required steering files exist.
    """
    print("\n🔍 Validating steering files")
    
    required_steering = [
        ".spec-workflow/steering/product.md",
        ".spec-workflow/steering/tech.md",
        ".spec-workflow/steering/structure.md",
    ]
    
    for steering_file in required_steering:
        full_path = PROJECT_ROOT / steering_file
        if full_path.exists():
            info(f"✓ Found steering file: {steering_file}")
        else:
            warn(f"Missing recommended steering file: {steering_file}")
    
    print("✅ Steering files validation completed")


def validate_source_files():
    """
    Validate that source files follow the spec-driven approach.
    """
    print("\n🔍 Validating source files")
    
    # Check for unexpected directories in src
    src_root = SRC_DIR / "d8q_intelligentengine_datafactory"
    
    allowed_src_dirs = {
        "domain",
        "application",
        "infrastructure",
        "interfaces"
    }
    
    # Check for unexpected directories in src
    for item in src_root.iterdir():
        if item.is_dir() and item.name not in allowed_src_dirs:
            warn(f"Unexpected directory in src: {item.relative_to(SRC_DIR)}")
    
    print("✅ Source files validation completed")


def validate_script_files():
    """
    Validate that required script files exist.
    """
    print("\n🔍 Validating script files")
    
    required_scripts = [
        "scripts/validate_spec.py",
        "scripts/validate_structure.py",
    ]
    
    for script_file in required_scripts:
        full_path = PROJECT_ROOT / script_file
        if full_path.exists():
            info(f"✓ Found script file: {script_file}")
        else:
            warn(f"Missing required script file: {script_file}")
    
    print("✅ Script files validation completed")


def validate_readme_files():
    """
    Validate that required README files exist.
    """
    print("\n🔍 Validating README files")
    
    required_readmes = [
        "README.md",
    ]
    
    for readme_file in required_readmes:
        full_path = PROJECT_ROOT / readme_file
        if full_path.exists():
            info(f"✓ Found README file: {readme_file}")
        else:
            warn(f"Missing recommended README file: {readme_file}")
    
    print("✅ README files validation completed")


def validate_agent_file():
    """
    Validate that the AGENT.md file exists.
    """
    print("\n🔍 Validating AGENT.md file")
    
    agent_file = PROJECT_ROOT / "AGENT.md"
    if agent_file.exists():
        info(f"✓ Found AGENT.md file")
        return True
    else:
        fail(f"Missing required AGENT.md file")


# =========================
# Main validation
# =========================

def main():
    print("=" * 80)
    print("STRUCTURE VALIDATION")
    print("=" * 80)
    
    # Validate AGENT.md first
    validate_agent_file()
    
    # Validate all other structure components
    validate_base_structure()
    validate_spec_files()
    validate_steering_files()
    validate_script_files()
    validate_source_files()
    validate_readme_files()
    
    print("\n" + "=" * 80)
    print("🎉 ALL STRUCTURE VALIDATIONS PASSED")
    print("=" * 80)
    print("The project structure follows the spec-driven development pattern.")
    print("All required directories and files are present.")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    main()
