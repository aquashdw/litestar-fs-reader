from pathlib import Path
from typing import AsyncGenerator

async def file_streamer(file_path: Path) -> AsyncGenerator[bytes, None]:
    """Streams a file from disk in chunks to minimize memory usage."""
    chunk_size = 65536  # 64KB
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            yield chunk
