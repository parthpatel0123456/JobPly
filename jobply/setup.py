from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="jobply",
    version="0.1.0",
    author="JobPly Team",
    description="Automated internship application pipeline",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/jobply",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.1",
    ],
    entry_points={
        'console_scripts': [
            'jobply-discovery=jobply.workers.discovery_worker:main',
        ],
    },
)
