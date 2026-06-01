#!/usr/bin/env python3
"""Version-independent Python obfuscation v3 - preserves __future__ imports."""
import base64
import zlib
import sys
import re
from pathlib import Path

def extract_future_imports(source: str) -> str:
    """Extract __future__ imports that must be at the top of the file."""
    futures = []
    for line in source.split('\n'):
        stripped = line.strip()
        if stripped.startswith('from __future__ import'):
            futures.append(stripped)
    return '\n'.join(futures)

def strip_docstrings(source: str) -> str:
    """Remove docstrings but keep code intact."""
    lines = source.split('\n')
    out = []
    in_docstring = False
    docstring_char = None
    for line in lines:
        stripped = line.strip()
        if in_docstring:
            if docstring_char in stripped:
                in_docstring = False
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            docstring_char = stripped[:3]
            if stripped.count(docstring_char) >= 2 and stripped.endswith(docstring_char) and len(stripped) > 6:
                continue
            in_docstring = True
            continue
        out.append(line)
    return '\n'.join(out)

def obfuscate_file(filepath: str) -> bool:
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"  SKIP: {filepath} not found")
        return False
    
    source = filepath.read_text(encoding='utf-8', errors='ignore')
    if source.startswith('# OBFUSCATED_V3') or '_obf_run' in source:
        print(f"  SKIP: {filepath} already obfuscated")
        return False
    
    # Extract __future__ imports (they MUST be first in file)
    future_imports = extract_future_imports(source)
    
    # Remove __future__ lines from source before encoding
    source_no_future = '\n'.join(
        line for line in source.split('\n')
        if not line.strip().startswith('from __future__ import')
    )
    
    # Strip docstrings
    cleaned = strip_docstrings(source_no_future)
    
    # Compress and encode
    compressed = zlib.compress(cleaned.encode('utf-8'), 9)
    encoded = base64.b64encode(compressed).decode('ascii')
    
    # Split into chunks
    chunk_size = 120
    chunks = [encoded[i:i+chunk_size] for i in range(0, len(encoded), chunk_size)]
    data_str = '\n'.join(f'    {repr(c)}' for c in chunks)
    
    # Build loader with __future__ imports preserved at top
    future_block = future_imports + '\n' if future_imports else ''
    
    loader = f'''# OBFUSCATED_V3 - BPB Easy Active Config MAIN v9.0.0
# This file is protected. Unauthorized modification is prohibited.
# Copyright (c) 2026 mcoders
{future_block}import base64 as _b;import zlib as _z
_d=_b.b64decode(
{data_str}
)
exec(_z.decompress(_d).decode('utf-8'))
'''
    filepath.write_text(loader, encoding='utf-8')
    print(f"  OK: {filepath} obfuscated ({len(source)} -> {len(loader)} bytes)")
    return True

def main():
    target_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    skip_dirs = {'__pycache__', '.pyarmor', 'dist', 'build', '.git', '.venv', 'node_modules'}
    
    count = 0
    for f in sorted(target_dir.rglob('*.py')):
        if any(d in f.parts for d in skip_dirs):
            continue
        if f.name.startswith('obfuscate'):
            continue
        print(f"Obfuscating: {f}")
        if obfuscate_file(str(f)):
            count += 1
    
    print(f"\nTotal obfuscated: {count} files")

if __name__ == '__main__':
    main()
