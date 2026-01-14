import os
import subprocess
import sys
from pathlib import Path

def compile_ui_files(src_dir: Path):
    """
    Recursively finds all .ui files in src_dir and compiles them to .py files.
    The output file is named {filename}_ui.py.
    """
    print(f"Scanning for .ui files in {src_dir}...")
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".ui"):
                ui_path = Path(root) / file
                py_filename = f"{ui_path.stem}_ui.py"
                py_path = ui_path.parent / py_filename
                
                # Check if recompilation is needed (timestamp check)
                if py_path.exists() and py_path.stat().st_mtime > ui_path.stat().st_mtime:
                    print(f"Skipping {ui_path.name} (up to date)")
                    continue
                
                print(f"Compiling {ui_path.name} -> {py_filename}...")
                
                try:
                    subprocess.run(
                        ["pyside6-uic", str(ui_path), "-o", str(py_path)],
                        check=True,
                        capture_output=True
                    )
                except subprocess.CalledProcessError as e:
                    print(f"Error compiling {ui_path}:")
                    print(e.stderr.decode())
                    sys.exit(1)
                except FileNotFoundError:
                     # Fallback if the command is not in PATH but accessible via python -m
                    try:
                         subprocess.run(
                            [sys.executable, "-m", "PySide6.scripts.uic", str(ui_path), "-o", str(py_path)],
                            check=True
                        )
                    except Exception as e2:
                        print(f"Error compiling {ui_path} (fallback method): {e2}")
                        sys.exit(1)

def main():
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    print("Starting build process...")
    compile_ui_files(src_dir)
    print("Build complete.")

if __name__ == "__main__":
    main()
