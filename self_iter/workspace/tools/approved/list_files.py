from agents import function_tool
import os

@function_tool
def list_files(dir_path: str) -> str:
    """List files and directories inside /workspace.

    Args:
        dir_path: Absolute path to directory to list.
    """
    try:
        real_path = os.path.realpath(dir_path)
        allowed_root = "/workspace"
        if os.path.commonpath([real_path, allowed_root]) != allowed_root:
            return "Error: path must be inside /workspace"
        if not os.path.isdir(real_path):
            return "Error: not a directory"
        entries = []
        for name in os.listdir(real_path):
            full = os.path.join(real_path, name)
            typ = "dir" if os.path.isdir(full) else "file"
            entries.append(f"{typ}:{name}")
        return "\n".join(entries[:500])
    except Exception as e:
        return f"Error listing files: {e}"