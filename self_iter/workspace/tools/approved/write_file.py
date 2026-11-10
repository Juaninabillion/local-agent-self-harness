from agents import function_tool
import os

@function_tool
def write_file(path: str, content: str) -> str:
    """Write text to a file inside /workspace/memory.

    Args:
        path: Absolute path to the file to write.
        content: Text content to write.
    """
    try:
        real_path = os.path.realpath(path)
        allowed_root = "/workspace/memory"
        if os.path.commonpath([real_path, allowed_root]) != allowed_root:
            return "Error: path must be inside /workspace/memory"
        if os.path.splitext(real_path)[1].lower() not in {".json", ".md", ".txt"}:
            return "Error: only .json, .md, .txt allowed"
        # prevent huge writes
        if len(content.encode("utf-8")) > 100 * 1024:
            return "Error: content too large"
        os.makedirs(os.path.dirname(real_path), exist_ok=True)
        with open(real_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Wrote {real_path}"
    except Exception as e:
        return f"Error writing file: {e}"