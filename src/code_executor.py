import docker
import tempfile
import os
from typing import Dict, Any
import time


class CodeExecutor:
    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception:
            self.client = None

    def execute_code(self, code: str, timeout: int = 60) -> Dict[str, Any]:
        if not self.client:
            raise Exception("Docker client is not available. Make sure Docker Desktop is running.")

        start_time = time.time()

        with tempfile.TemporaryDirectory() as temp_dir:
            code_file = os.path.join(temp_dir, "analysis.py")
            with open(code_file, "w", encoding="utf-8") as f:
                f.write(code)

            try:
                container = self.client.containers.run(
                    image="anygraph-executor:latest",
                    command=["python", "/code/analysis.py"],
                    volumes={temp_dir: {"bind": "/code", "mode": "rw"}},
                    mem_limit="512m",
                    network_disabled=False,
                    remove=True,
                    detach=False,
                    stdout=True,
                    stderr=True
                )

                output = container.decode("utf-8")
                execution_time = time.time() - start_time

                return {
                    "success": True,
                    "output": output,
                    "error": None,
                    "execution_time": execution_time
                }

            except docker.errors.ContainerError as e:
                execution_time = time.time() - start_time
                return {
                    "success": False,
                    "output": e.stdout.decode("utf-8") if e.stdout else "",
                    "error": e.stderr.decode("utf-8") if e.stderr else str(e),
                    "execution_time": execution_time
                }

            except docker.errors.APIError as e:
                execution_time = time.time() - start_time
                return {
                    "success": False,
                    "output": "",
                    "error": f"Docker API error: {str(e)}",
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
        if not self.client:
            return False

        try:
            self.client.containers.run(
                "anygraph-executor:latest",
                "python -c 'print(\"Docker is working\")'",
                remove=True
            )
            return True
        except Exception:
            return False


_executor_instance = None


def get_executor() -> CodeExecutor:
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = CodeExecutor()
    return _executor_instance
