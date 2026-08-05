#!/usr/bin/env python3
"""Count pages in one or more PDF catalog files and print a summary.

Usage:
    python count_pages.py <file1.pdf> [file2.pdf ...]
"""
import contextlib
import os
import re
import subprocess
import sys
from pathlib import Path


@contextlib.contextmanager
def _quiet_native_stderr():
    """Silence the process's stderr fd for the duration of the block.

    A broken local cryptography/cffi install can make pypdf's import trigger
    a Rust-level pyo3 panic, which prints a native stack trace straight to
    fd 2 (bypassing sys.stderr, so redirecting that alone wouldn't catch it).
    """
    fd = sys.stderr.fileno()
    saved_fd = os.dup(fd)
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull_fd, fd)
        yield
    finally:
        os.dup2(saved_fd, fd)
        os.close(devnull_fd)
        os.close(saved_fd)


def _get_pdf_reader():
    """Return pypdf's PdfReader, installing the package on first use if needed.

    Caught as BaseException, not Exception: that same broken cryptography/cffi
    install makes the panic surface as a pyo3 PanicException, which subclasses
    BaseException directly and would otherwise crash the script instead of
    falling through to the regex-scan fallback.
    """
    try:
        with _quiet_native_stderr():
            from pypdf import PdfReader
        return PdfReader
    except BaseException:
        pass
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "pypdf"],
            check=True,
            capture_output=True,
        )
        with _quiet_native_stderr():
            from pypdf import PdfReader
        return PdfReader
    except BaseException:
        return None


def _count_via_fallback_scan(path):
    """Estimate a page count directly from PDF bytes when pypdf is unavailable.

    Used only as a last resort (e.g. no network to install pypdf). Reads the
    /Pages root's /Count when it's present uncompressed, else counts
    individual /Type /Page objects. Can undercount PDFs that store their
    page tree in compressed object streams.
    """
    data = Path(path).read_bytes()
    counts = re.findall(rb"/Type\s*/Pages\b[^>]*?/Count\s+(\d+)", data, re.DOTALL)
    if counts:
        return int(counts[0])
    page_objs = re.findall(rb"/Type\s*/Page(?!s)\b", data)
    return len(page_objs)


def count_pages(path):
    """Return (page_count, method) for a single PDF file."""
    reader_cls = _get_pdf_reader()
    if reader_cls is not None:
        try:
            reader = reader_cls(str(path))
            return len(reader.pages), "pypdf"
        except BaseException:
            pass
    return _count_via_fallback_scan(path), "fallback-scan"


def main():
    if len(sys.argv) < 2:
        print("Usage: count_pages.py <file1.pdf> [file2.pdf ...]", file=sys.stderr)
        sys.exit(1)

    results = []
    errors = []
    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            errors.append((arg, "file not found"))
            continue
        if path.suffix.lower() != ".pdf":
            errors.append((arg, f"unsupported file type '{path.suffix}' (only .pdf is supported)"))
            continue
        try:
            count, method = count_pages(path)
        except Exception as e:
            errors.append((arg, str(e)))
            continue
        results.append((path.name, count, method))

    name_width = max([len(name) for name, _, _ in results] + [4])
    for name, count, method in results:
        note = "" if method == "pypdf" else "  (estimated)"
        print(f"{name.ljust(name_width)}  {count:>5} pages{note}")

    if len(results) > 1:
        total = sum(count for _, count, _ in results)
        print("-" * (name_width + 14))
        print(f"{'TOTAL'.ljust(name_width)}  {total:>5} pages")

    for arg, msg in errors:
        print(f"WARNING: {arg}: {msg}", file=sys.stderr)

    if errors and not results:
        sys.exit(1)


if __name__ == "__main__":
    main()
