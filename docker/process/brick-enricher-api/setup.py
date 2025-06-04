from setuptools import setup, find_packages

setup(
    name="pcaster",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer[all]",
        "azure-storage-blob",
        "azure-identity",
        "azure-keyvault-secrets",
        "pandas",
        "pyarrow",
        "python-dotenv",
        "playwright"
    ],
    entry_points={
        "console_scripts": [
            "pcaster=app.cli:app"
        ]
    },
)
