from setuptools import setup, find_packages

setup(
    name="pcaster",
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
        "playwright"
    ],
    entry_points={
        "console_scripts": [
            "pcaster=app.cli:app"
        ]
    },
)
