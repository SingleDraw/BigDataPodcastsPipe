from setuptools import setup, find_packages

setup(
    name="test-app",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer[all]",
        "azure-storage-blob",
        "azure-identity",
        "azure-keyvault-secrets",
        "requests"
    ],
    entry_points={
        "console_scripts": [
            "test=app.cli:app"
        ]
    },
)
