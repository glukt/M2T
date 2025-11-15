import sys
import subprocess
import os
import venv
import webbrowser
import time
import argparse

# Define the name of the virtual environment directory
VENV_DIR = "venv"

def find_python_version(version=None):
    """Finds the Python executable for the specified version."""
    if version is None:
        # Try Python 3.12.7 first, then 3.12, then 3.13
        versions_to_try = ["3.12.7", "3.12", "3.13"]
    else:
        versions_to_try = [version, version.split(".")[0] + "." + version.split(".")[1]]
    
    if sys.platform == "win32":
        for v in versions_to_try:
            try:
                result = subprocess.run(
                    ["py", f"-{v}", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Return the py launcher command with version spec
                    return ["py", f"-{v}"]
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        # Fallback: try direct python commands
        for cmd in ["python3.12", "python3.13", "python3"]:
            try:
                result = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return [cmd]
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
    else:
        # Unix-like systems
        for v in versions_to_try:
            for cmd in [f"python{v}", f"python3.{v.split('.')[1]}"]:
                try:
                    result = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return [cmd]
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
    
    return None

def create_virtual_env(python_cmd=None):
    """Creates a virtual environment if it doesn't exist."""
    if not os.path.exists(VENV_DIR):
        print(f"Creating virtual environment in ./{VENV_DIR}...")
        try:
            if python_cmd:
                # Use specific Python version
                print(f"Using Python: {' '.join(python_cmd)}")
                subprocess.check_call(python_cmd + ["-m", "venv", VENV_DIR])
            else:
                venv.create(VENV_DIR, with_pip=True)
            print("Virtual environment created successfully.")
        except Exception as e:
            print(f"Error creating virtual environment: {e}")
            sys.exit(1)
    else:
        print("Virtual environment already exists.")

def get_pip_path():
    """Gets the path to the pip executable within the venv."""
    if sys.platform == "win32":
        return os.path.join(VENV_DIR, "Scripts", "pip.exe")
    else:
        return os.path.join(VENV_DIR, "bin", "pip")

def get_python_path():
    """Gets the path to the python executable within the venv."""
    if sys.platform == "win32":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_DIR, "bin", "python")

def install_requirements():
    """Installs dependencies from requirements.txt using the venv's pip."""
    pip_path = get_pip_path()
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print(f"Error: {requirements_file} not found.")
        print("Please make sure it's in the same directory as setup.py.")
        sys.exit(1)

    print("--- Ensuring pip is up-to-date ---")
    try:
        subprocess.check_call([get_python_path(), "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError as e:
        print(f"Could not upgrade pip: {e}. Continuing with installation...")

    print(f"--- Installing dependencies from {requirements_file} ---")
    try:
        # We run pip as a module of the venv's python to ensure correctness
        subprocess.check_call([get_python_path(), "-m", "pip", "install", "-r", requirements_file])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: '{get_python_path()}' or 'pip' not found in venv.")
        print("Virtual environment may be corrupted.")
        sys.exit(1)

def run_application():
    """Runs the main Flask application using the venv's python."""
    python_path = get_python_path()
    app_file = "app.py"
    
    if not os.path.exists(app_file):
        print(f"Error: {app_file} not found.")
        print("Please make sure it's in the same directory as setup.py.")
        sys.exit(1)
        
    print(f"Starting the Flask application ({app_file})...")
    print("Find the application at http://127.0.0.1:5000")
    print("Press CTRL+C to stop the server.")
    
    # --- Auto-open browser ---
    def open_browser():
        time.sleep(2) # Give the server a moment to start
        webbrowser.open('http://127.0.0.1:5000')
        
    from threading import Thread
    browser_thread = Thread(target=open_browser)
    browser_thread.start()
    # ---
    
    try:
        subprocess.check_call([python_path, app_file])
    except subprocess.CalledProcessError as e:
        print(f"Application exited with error: {e}")
    except KeyboardInterrupt:
        print("\nServer stopped by user.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup M2T Morse Code Application")
    parser.add_argument(
        "--python",
        "-p",
        type=str,
        help="Python version to use (e.g., '3.12.7', '3.12', '3.13'). Default: tries 3.12.7, then 3.12, then 3.13"
    )
    args = parser.parse_args()
    
    print("--- Morse Code Application Setup ---")
    
    # Find and use the appropriate Python version
    python_cmd = find_python_version(args.python)
    if python_cmd:
        python_version_str = ' '.join(python_cmd)
        print(f"Found Python: {python_version_str}")
        # Verify version
        try:
            version_result = subprocess.run(python_cmd + ["--version"], capture_output=True, text=True)
            if version_result.returncode == 0:
                print(f"Python version: {version_result.stdout.strip()}")
        except:
            pass
    else:
        print("Warning: Could not find a specific Python version. Using system default.")
        python_cmd = None
    
    create_virtual_env(python_cmd)
    install_requirements()
    print("--- Setup complete ---")
    run_application()
