#!/usr/bin/env python3
"""
Snap! Educational MCP System Setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="snap-edu-mcp",
    version="0.1.0",
    author="Snap! Educational Team",
    author_email="team@snap-edu.dev",
    description="Educational programming system using MCP to generate Snap! blocks from natural language",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/snap-edu/snap-llm-mcp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Topic :: Education",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.11.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        # Note: Heavy NLP dependencies removed - Claude handles NLP!
        # "nlp": [
        #     "transformers>=4.30.0",  # REMOVED - 500MB+ not needed
        #     "torch>=2.0.0",          # REMOVED - Heavy dependency
        # ],
    },
    entry_points={
        "console_scripts": [
            "snap-mcp-server=mcp_server.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "mcp_server": [
            "knowledge/*.json",
            "knowledge/*.yaml",
        ],
    },
    zip_safe=False,
)
