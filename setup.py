from setuptools import setup, find_packages

setup(
    name="crawl4ai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "python-docx>=0.8.11",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart",
        "starlette-csrf",
        "sqlalchemy>=2.0.0",
        "alembic",
        "pytest",
        "pytest-asyncio",
        "httpx",
    ],
    python_requires=">=3.8",
) 