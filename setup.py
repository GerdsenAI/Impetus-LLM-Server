#!/usr/bin/env python3
"""
Setup script for GerdsenAI MLX Model Manager
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="gerdsen-ai-mlx-manager",
    version="2.0.0",
    author="GerdsenAI Team",
    author_email="contact@gerdsenai.com",
    description="Professional AI Model Management Platform for Apple Silicon",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gerdsenai/mlx-model-manager",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "full": [
            "torch>=2.0.0",
            "transformers>=4.30.0",
            "safetensors>=0.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gerdsen-ai=integrated_gerdsen_ai:main",
            "gerdsen-ai-installer=drag_drop_installer:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.html", "*.css", "*.js", "*.json", "*.md"],
    },
    project_urls={
        "Bug Reports": "https://github.com/gerdsenai/mlx-model-manager/issues",
        "Source": "https://github.com/gerdsenai/mlx-model-manager",
        "Documentation": "https://github.com/gerdsenai/mlx-model-manager/wiki",
    },
)

