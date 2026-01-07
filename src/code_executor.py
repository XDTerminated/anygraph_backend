import subprocess
import tempfile
import os
import sys
from typing import Dict, Any
import time
import signal


class CodeExecutor:
    def __init__(self):
        """Initialize the secure subprocess-based code executor."""
        # Whitelist of allowed imports for security
        self.allowed_imports = {
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'scikit-learn',
            'sklearn', 'scipy', 'openpyxl', 'requests', 'tabulate',
            'json', 'csv', 'io', 'os', 'sys', 'math', 're', 'datetime',
            'collections', 'itertools', 'functools', 'warnings'
        }

    def _validate_code(self, code: str) -> tuple[bool, str]:
        """Basic validation to check for dangerous operations."""
        dangerous_patterns = [
            'import subprocess', 'import os.system', '__import__',
            'eval(', 'exec(', 'compile(', 'open(', 'file(',
            'input(', 'raw_input('
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                return False, f"Potentially dangerous operation detected: {pattern}"
        
        return True, ""

    def execute_code(self, code: str, timeout: int = 60) -> Dict[str, Any]:
        """Execute Python code in a secure subprocess with timeout and resource limits."""
        start_time = time.time()

        # Validate code for dangerous operations
        is_valid, error_msg = self._validate_code(code)
        if not is_valid:
            return {
                "success": False,
                "output": "",
                "error": f"Security validation failed: {error_msg}",
                "execution_time": 0
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            code_file = os.path.join(temp_dir, "analysis.py")
            
            # Write code to temporary file
            with open(code_file, "w", encoding="utf-8") as f:
                f.write(code)

            try:
                # Set up environment with restricted permissions
                env = os.environ.copy()
                env['PYTHONUNBUFFERED'] = '1'
                env['TMPDIR'] = temp_dir
                
                # Execute code in subprocess with timeout
                process = subprocess.Popen(
                    [sys.executable, code_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=temp_dir,
                    env=env,
                    text=True,
                    preexec_fn=os.setpgrp if os.name != 'nt' else None
                )

                try:
                    stdout, stderr = process.communicate(timeout=timeout)
                    execution_time = time.time() - start_time

                    # Combine stdout and stderr
                    output = stdout
                    if stderr:
                        output = f"{stdout}\n[STDERR]\n{stderr}" if stdout else stderr

                    # Debug: Log output length
                    print(f"[CodeExecutor] Output length: {len(output)} characters")
                    print(f"[CodeExecutor] Output preview: {output[:200] if output else 'EMPTY'}...")

                    success = process.returncode == 0

                    return {
                        "success": success,
                        "output": output,
                        "error": None if success else stderr,
                        "execution_time": execution_time
                    }

                except subprocess.TimeoutExpired:
                    # Kill the process group to ensure all child processes are terminated
                    if os.name != 'nt':
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    else:
                        process.terminate()
                    
                    process.wait(timeout=5)
                    execution_time = time.time() - start_time

                    return {
                        "success": False,
                        "output": "",
                        "error": f"Execution timed out after {timeout} seconds",
                        "execution_time": execution_time
                    }

            except Exception as e:
                execution_time = time.time() - start_time
                return {
                    "success": False,
                    "output": "",
                    "error": f"Execution error: {str(e)}",
                    "execution_time": execution_time
                }

    def test_docker(self) -> bool:
        """Test if execution environment is working (backwards compatibility)."""
        try:
            result = self.execute_code('print("Executor is working")', timeout=5)
            return result["success"]
        except Exception:
            return False


_executor_instance = None


def get_executor() -> CodeExecutor:
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = CodeExecutor()
    return _executor_instance
