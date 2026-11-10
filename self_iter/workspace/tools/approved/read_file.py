from agents import function_tool
import os

@function_tool
def read_file(path: str) -> str:
    """Read a text file inside /workspace with safety checks.

    Args:
        path: Absolute path to the file to read.
    """
    try:
        real_path = os.path.realpath(path)
        allowed_root = "/workspace"
        if os.path.commonpath([real_path, allowed_root]) != allowed_root:
            return "Error: path must be inside /workspace"
        if not os.path.isfile(real_path):
            return "Error: not a file"
        # prevent huge reads
        max_size = 200 * 1024
        size = os.path.getsize(real_path)
        if size > max_size:
            return f"Error: file too large {size} bytes > {max_size}"
        with open(real_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"