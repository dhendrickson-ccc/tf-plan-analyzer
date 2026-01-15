"""
File I/O utilities for safe reading and writing.

This module provides standardized file operations with consistent error handling
and encoding settings.
"""

from typing import Optional


def safe_read_file(file_path: str, encoding: str = "utf-8") -> str:
    """
    Safely read a text file from disk with proper encoding.

    Args:
        file_path: Path to the file to read
        encoding: Character encoding to use (default: 'utf-8')

    Returns:
        Complete file contents as a string

    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: For other file reading errors
        UnicodeDecodeError: If the file can't be decoded with the specified encoding

    Example:
        >>> readme_content = safe_read_file('README.md')
        >>> print(f"README is {len(readme_content)} characters")
    """
    with open(file_path, "r", encoding=encoding) as f:
        return f.read()


def safe_write_file(file_path: str, content: str, encoding: str = "utf-8") -> None:
    """
    Safely write text content to a file with proper encoding.

    Creates or overwrites the file at the specified path. Parent directories
    must already exist.

    Args:
        file_path: Path to the file to write
        content: String content to write to the file
        encoding: Character encoding to use (default: 'utf-8')

    Returns:
        None

    Raises:
        IOError: If the file cannot be written (permissions, disk full, etc.)
        UnicodeEncodeError: If content can't be encoded with the specified encoding

    Example:
        >>> report_html = generate_html_report(data)
        >>> safe_write_file('output/report.html', report_html)
    """
    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)
