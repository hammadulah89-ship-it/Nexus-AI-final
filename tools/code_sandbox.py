"""
Pillar 2: Isolated Subprocess Python REPL Sandbox & Dynamic Plot Generator.
Runs code in an isolated child subprocess with strict timeout guards (SIGKILL on timeout),
preventing infinite loops from blocking the FastAPI server, and captures generated Matplotlib plots.
"""

import asyncio
import base64
import os
import subprocess
import sys
import tempfile
import time
from typing import Dict, Any, List, Optional
from config import SANDBOX_TIMEOUT_SECONDS

SANDBOX_WRAPPER_TEMPLATE = """
import sys
import os
import io

# Setup headless matplotlib
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

# Execute user code
__output_plots__ = []

def __save_current_plots__():
    if plt is not None and plt.get_fignums():
        for i, fig_num in enumerate(plt.get_fignums()):
            fig = plt.figure(fig_num)
            plot_path = f"{PLOT_DIR}/plot_{i}.png"
            fig.savefig(plot_path, format='png', bbox_inches='tight', dpi=120, facecolor='#13151f', edgecolor='none')
            __output_plots__.append(plot_path)
        plt.close('all')

# User Script Begins
{USER_CODE}
# User Script Ends

__save_current_plots__()
"""

class PythonCodeSandbox:
    def __init__(self, timeout: float = SANDBOX_TIMEOUT_SECONDS):
        self.timeout = timeout

    async def execute_async(self, code: str) -> Dict[str, Any]:
        """
        Executes Python code in an isolated subprocess with hard timeout enforcement.
        If an infinite loop occurs, the subprocess is killed without blocking the server.
        """
        t_start = time.perf_counter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "sandbox_script.py")
            plot_dir = os.path.join(temp_dir, "plots")
            os.makedirs(plot_dir, exist_ok=True)

            wrapped_code = (
                SANDBOX_WRAPPER_TEMPLATE
                .replace("{PLOT_DIR}", plot_dir)
                .replace("{USER_CODE}", code)
            )

            with open(script_path, "w", encoding="utf-8") as f:
                f.write(wrapped_code)

            stdout_text = ""
            stderr_text = ""
            success = False
            has_timeout = False

            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable,
                    script_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=temp_dir
                )

                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(),
                        timeout=self.timeout
                    )
                    stdout_text = stdout_bytes.decode("utf-8", errors="ignore").strip()
                    stderr_text = stderr_bytes.decode("utf-8", errors="ignore").strip()
                    success = (proc.returncode == 0)
                except asyncio.TimeoutError:
                    has_timeout = True
                    success = False
                    try:
                        proc.kill()
                        await proc.wait()
                    except Exception:
                        pass
                    stderr_text = f"Execution Timeout: Code execution exceeded the maximum limit of {self.timeout}s and was terminated safely."

            except Exception as e:
                success = False
                stderr_text = f"Subprocess launch error: {str(e)}"

            # Collect any generated plots
            images = []
            if os.path.exists(plot_dir):
                plot_files = sorted(os.listdir(plot_dir))
                for pf in plot_files:
                    if pf.endswith(".png"):
                        full_pf = os.path.join(plot_dir, pf)
                        try:
                            with open(full_pf, "rb") as img_file:
                                b64 = base64.b64encode(img_file.read()).decode("utf-8")
                                images.append(f"data:image/png;base64,{b64}")
                        except Exception:
                            pass

        exec_time = round((time.perf_counter() - t_start) * 1000, 2)

        if not success:
            output_msg = stderr_text or stdout_text or "[Execution failed with no error output]"
        else:
            output_msg = stdout_text or (f"[Generated {len(images)} plot(s)]" if images else "[Execution finished successfully]")

        return {
            "success": success and not has_timeout,
            "code": code,
            "output": output_msg[:4000],
            "has_error": not success or has_timeout,
            "has_timeout": has_timeout,
            "images": images,
            "plots_count": len(images),
            "execution_time_ms": exec_time
        }

    def execute(self, code: str) -> Dict[str, Any]:
        """Synchronous wrapper around async subprocess execution."""
        try:
            return asyncio.run(self.execute_async(code))
        except Exception:
            # Fallback if loop already running
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Run with standard subprocess
                t_start = time.perf_counter()
                with tempfile.TemporaryDirectory() as temp_dir:
                    script_path = os.path.join(temp_dir, "sandbox_script.py")
                    plot_dir = os.path.join(temp_dir, "plots")
                    os.makedirs(plot_dir, exist_ok=True)

                    wrapped_code = (
                        SANDBOX_WRAPPER_TEMPLATE
                        .replace("{PLOT_DIR}", plot_dir)
                        .replace("{USER_CODE}", code)
                    )
                    with open(script_path, "w", encoding="utf-8") as f:
                        f.write(wrapped_code)

                    try:
                        res = subprocess.run(
                            [sys.executable, script_path],
                            capture_output=True,
                            text=True,
                            timeout=self.timeout,
                            cwd=temp_dir
                        )
                        stdout_text = res.stdout.strip()
                        stderr_text = res.stderr.strip()
                        success = (res.returncode == 0)
                        has_timeout = False
                    except subprocess.TimeoutExpired:
                        stdout_text = ""
                        stderr_text = f"Execution Timeout: Code exceeded maximum limit of {self.timeout}s and was terminated."
                        success = False
                        has_timeout = True

                    images = []
                    if os.path.exists(plot_dir):
                        for pf in sorted(os.listdir(plot_dir)):
                            if pf.endswith(".png"):
                                with open(os.path.join(plot_dir, pf), "rb") as img_file:
                                    images.append(f"data:image/png;base64,{base64.b64encode(img_file.read()).decode('utf-8')}")

                    exec_time = round((time.perf_counter() - t_start) * 1000, 2)
                    output_msg = stderr_text if not success else (stdout_text or f"[Generated {len(images)} plot(s)]")
                    return {
                        "success": success,
                        "code": code,
                        "output": output_msg[:4000],
                        "has_error": not success,
                        "has_timeout": has_timeout,
                        "images": images,
                        "plots_count": len(images),
                        "execution_time_ms": exec_time
                    }
            return asyncio.run(self.execute_async(code))
