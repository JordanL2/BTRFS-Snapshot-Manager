import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="btrfssnapshotmanager",
    version="0.99.0",
    author="Jordan Leppert",
    author_email="jordanleppert@gmail.com",
    description="A tool to manage, schedule, and backup snapshots of btrfs subvolumes.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JordanL2/BTRFS-Snapshot-Manager",
    packages=setuptools.find_packages() + setuptools.find_namespace_packages(include=['btrfssnapshotmanager.*']),
    install_requires=[
        'pyyaml',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL-3.0 License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    entry_points = {'console_scripts': [
        'btrfs-snapshot-manager=btrfssnapshotmanager.cli:main',
        ], },
)
