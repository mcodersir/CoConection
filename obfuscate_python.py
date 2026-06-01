#!/usr/bin/env python3
"""Obfuscate Python files using base64 + zlib + marshal approach."""
import base64
import zlib
import marshal
import py_compile
import sys
import os
from pathlib import Path

def obfuscate_file(filepath: str) -> bool:
    """Read a .py file, compile to bytecode, compress, encode, and replace with obfuscated version."""
    filepath = Path(filepath)
    if not filepath.exists():
        print(f"  SKIP: {filepath} not found")
        return False
    
    source = filepath.read_text(encoding='utf-8', errors='ignore')
    if source.startswith('# OBFUSCATED') or '_obf_loader' in source:
        print(f"  SKIP: {filepath} already obfuscated")
        return False
    
    try:
        code = compile(source, str(filepath.name), 'exec')
        bytecode = marshal.dumps(code)
        compressed = zlib.compress(bytecode, 9)
        encoded = base64.b64encode(compressed).decode('ascii')
    except Exception as e:
        print(f"  ERROR compiling {filepath}: {e}")
        return False
    
    # Create obfuscated loader
    loader = f'''# OBFUSCATED - BPB Easy Active Config MAIN v9.0.0
# This file is protected and obfuscated. Unauthorized modification is prohibited.
# Copyright (c) 2026 mcoders
import base64 as _b;import zlib as _z;import marshal as _m;_d=_b.b64decode({repr(encoded)});_c=_m.loads(_z.decompress(_d));exec(_c)
'''
    filepath.write_text(loader, encoding='utf-8')
    print(f"  OK: {filepath} obfuscated ({len(source)} -> {len(loader)} bytes, ratio {len(loader)/max(len(source),1):.1f}x)")
    return True

def main():
    target_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    py_files = list(target_dir.rglob('*.py'))
    
    # Skip __pycache__, .pyarmor, etc.
    skip_dirs = {'__pycache__', '.pyarmor', 'dist', 'build', '.git', '.venv', 'node_modules'}
    
    count = 0
    for f in py_files:
        if any(d in f.parts for d in skip_dirs):
            continue
        if f.name == 'obfuscate_python.py':
            continue
        print(f"Obfuscating: {f}")
        if obfuscate_file(str(f)):
            count += 1
    
    print(f"\nTotal obfuscated: {count} files")

if __name__ == '__main__':
    main()
