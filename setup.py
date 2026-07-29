"""
NetReaper setup configuration.
Author: 09azo14 | License: MIT
"""

from setuptools import setup, find_packages
from pathlib import Path

long_description = Path("README.md").read_text(encoding="utf-8")

setup(
    name="netreaper",
    version="1.0.0",
    author="09azo14",
    description="Command-line security testing framework for isolated network environments.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/09AZ014/netreaper",
    packages=find_packages(exclude=["tests*", "docs*"]),
    python_requires=">=3.8",
    install_requires=[
        "rich>=13.0.0",
        "questionary>=2.0.0",
        "InquirerPy>=0.3.4",
        "fpdf2>=2.7.0",
        "colorama>=0.4.6",
        "tabulate>=0.9.0",
        "requests>=2.31.0",
        "paramiko>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
            "bandit>=1.7.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "netreaper=netreaper:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: System :: Networking :: Monitoring",
    ],
)
