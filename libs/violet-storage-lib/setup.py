from setuptools import setup, find_packages

# This is the setup script for the local Violet Storage Library.
# Created as a standalone library for reusability across different applications.
#
# The library provides a unified interface for both Azure Blob Storage and S3,
# allowing users to upload and download files, objects, and DataFrames.
#
# standard installation of the library can be done using pip:
# pip install /path-to/violet-storage-lib # can be relative or absolute path
#
# parquet support can be added by installing the optional dependency:
# pip install /path-to/violet-storage-lib[parquet]

setup(
    name="violet-storage-lib",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "azure-storage-blob",
        "azure-identity",
        "boto3",
    ],
    extras_require={
        "parquet": ["pyarrow"],
    },
    python_requires=">=3.8",
)
