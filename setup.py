from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="vmz-wiki-automation",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="VMZ Wiki自动化工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/VMZ-Wiki-Automation",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "vmz-wiki=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "vmz_wiki": ["templates/*.j2"],
    },
)