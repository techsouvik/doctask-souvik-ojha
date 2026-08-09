"""Scalable Non-Blocking Async File System Tools."""

import os
import aiofiles
import difflib
from typing import List, Dict, Any, Optional


class AsyncFileSystemTools:
    """Async, non-blocking file system operations."""

    @staticmethod
    async def read_file_async(filepath: str) -> str:
        """Read a text file asynchronously without blocking the event loop."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        async with aiofiles.open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return await f.read()

    @staticmethod
    async def write_file_async(filepath: str, content: str):
        """Write content to file atomically and asynchronously."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        temp_path = f"{filepath}.tmp_{os.getpid()}"

        async with aiofiles.open(temp_path, "w", encoding="utf-8") as f:
            await f.write(content)

        os.replace(temp_path, filepath)

    @staticmethod
    async def list_dir_async(dirpath: str) -> List[Dict[str, Any]]:
        """List contents of a directory asynchronously."""
        if not os.path.exists(dirpath):
            raise FileNotFoundError(f"Directory not found: {dirpath}")

        entries = []
        for name in os.listdir(dirpath):
            if name.startswith("."):
                continue
            full_path = os.path.join(dirpath, name)
            stat = os.stat(full_path)
            entries.append({
                "name": name,
                "is_dir": os.path.isdir(full_path),
                "size_bytes": stat.st_size,
                "path": full_path
            })
        return entries

    @staticmethod
    async def diff_files_async(filepath_a: str, filepath_b: str) -> str:
        """Generate a line-by-line unified diff between two files asynchronously."""
        content_a = await AsyncFileSystemTools.read_file_async(filepath_a)
        content_b = await AsyncFileSystemTools.read_file_async(filepath_b)

        diff = difflib.unified_diff(
            content_a.splitlines(),
            content_b.splitlines(),
            fromfile=os.path.basename(filepath_a),
            tofile=os.path.basename(filepath_b),
            lineterm=""
        )
        return "\n".join(diff)
