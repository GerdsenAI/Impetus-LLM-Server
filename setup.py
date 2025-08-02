#!/usr/bin/env python3
"""
Setup script for Impetus LLM Server
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
requirements = []
requirements_path = this_directory / "gerdsen_ai_server" / "requirements.txt"
if requirements_path.exists():
    requirements = [
        line.strip() 
        for line in requirements_path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="impetus-llm-server",
    version="0.1.0",
    author="GerdsenAI",
    author_email="dev@gerdsenai.com",
    description="Lightning-fast local LLM server optimized for Apple Silicon with OpenAI-compatible API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GerdsenAI/Impetus-LLM-Server",
    packages=find_packages(where="gerdsen_ai_server"),
    package_dir={"": "gerdsen_ai_server"},
    package_data={
        "": ["*.json", "*.yaml", "*.yml", "*.html", "*.css", "*.js"],
    },
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio",
            "pytest-cov",
            "ruff",
            "mypy",
            "black",
        ],
    },
    entry_points={
        "console_scripts": [
            "impetus=src.cli:main",
            "impetus-server=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: MacOS :: MacOS X",
        "Environment :: GPU",
    ],
    keywords="llm mlx apple-silicon ml ai inference server openai-compatible",
    project_urls={
        "Documentation": "https://github.com/GerdsenAI/Impetus-LLM-Server#readme",
        "Issues": "https://github.com/GerdsenAI/Impetus-LLM-Server/issues",
        "Source": "https://github.com/GerdsenAI/Impetus-LLM-Server",
    },
)