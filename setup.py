from setuptools import setup, find_packages
import os

# 读取README文件
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="apartment-accesscode",
    version="1.0.0",
    author="Apartment AccessCode Team",
    author_email="support@apartment-accesscode.com",
    description="地址公寓识别与门禁码提取工具 - 基于Placekey API的智能地址处理",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/apartment-accesscode/apartment-accesscode",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Text Processing :: General",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "apartment-accesscode=apartment_accesscode.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "apartment_accesscode": ["*.json", "*.yaml", "*.yml"],
    },
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.910",
        ],
        "ui": [
            "flask>=2.0",
            "flask-cors>=3.0",
            "gunicorn>=20.0",
        ],
    },
)