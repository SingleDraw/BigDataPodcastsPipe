from setuptools import setup, find_packages

APP_ROOT_DIR_NAME = 'app'

setup(
    name="whisperer",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi",
        "uvicorn",
        "celery",
        "redis",
        "typer[all]",
        # -- Storage clients handled by external storage_lib
        # "boto3",
        # "azure-storage-blob",
        # "azure-identity",
        "azure-keyvault-secrets",
        "asyncio",
        "websockets",
        "faster-whisper",
        "ffmpeg-python",
        "psutil",
        "requests"
    ],
    entry_points={
        "console_scripts": [
            f"whisperer-server={APP_ROOT_DIR_NAME}.server:main",
            f"whisperer-submit={APP_ROOT_DIR_NAME}.cli:app"
        ]
    },
)
