from setuptools import setup, find_packages

setup(
    name="enricher-api",
    description="Podcast Metadata Enrichment API",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer[all]",
        "pandas",
        # NOTE: violet-storage-lib is not included here,
        #      it should be installed separately in the Dockerfile
        # "pip install libs/violet-storage-lib[pyarrow]",
        "python-dotenv",
        "rapidfuzz"
    ],
    entry_points={
        "console_scripts": [
            "enricher=app.cli:app"
        ]
    },
)
