#!/usr/bin/env python3
"""Version-independent Python obfuscation using base64 + zlib on source TEXT (not bytecode).
This approach works across all Python versions because we encode the source text,
not compiled bytecode which is version-specific."""
import base64
import zlib
import sys
import re
from pathlib import Path

def strip_source(source: str) -> str:
    """Strip docstrings and comments but keep code intact."""
    lines = source.split('\n')
    out = []
    in_docstring = False
    docstring_char = None
    for line in lines:
        stripped = line.strip()
        # Handle multi-line docstrings
        if in_docstring:
            if docstring_char in stripped:
                in_docstring = False
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            docstring_char = stripped[:3]
            if stripped.count(docstring_char) >= 2 and stripped.endswith(docstring_char) and len(stripped) > 6:
                continue  # single-line docstring
            in_docstring = True
            continue
        # Keep code lines (including comments - they'll be encoded anyway)
        out.append(line)
    return '\n'.join(out)

def obfuscate_file(filepath: str) -> bool:
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"  SKIP: {filepath} not found")
        return False
    
    source = filepath.read_text(encoding='utf-8', errors='ignore')
    if source.startswith('# OBFUSCATED_V2') or '_obf_run' in source:
        print(f"  SKIP: {filepath} already obfuscated")
        return False
    
    # Strip docstrings to reduce size
    cleaned = strip_source(source)
    
    # Compress and encode the source TEXT (not bytecode!)
    compressed = zlib.compress(cleaned.encode('utf-8'), 9)
    encoded = base64.b64encode(compressed).decode('ascii')
    
    # Split encoded data into chunks for readability
    chunk_size = 120
    chunks = [encoded[i:i+chunk_size] for i in range(0, len(encoded), chunk_size)]
    data_str = '\n'.join(f'    {repr(c)}' for c in chunks)
    
    # Create obfuscated loader - version independent!
    loader = f'''# OBFUSCATED_V2 - BPB Easy Active Config MAIN v9.0.0
# This file is protected. Unauthorized modification is prohibited.
# Copyright (c) 2026 mcoders
import base64 as _b;import zlib as _z
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
        if f.name == 'obfuscate_v2.py':
            continue
        print(f"Obfuscating: {f}")
        if obfuscate_file(str(f)):
            count += 1
    
    print(f"\nTotal obfuscated: {count} files")

if __name__ == '__main__':
    main()
