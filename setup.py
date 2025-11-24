from setuptools import setup, find_packages

setup(
    name="lyricbeats-ai",
    version="0.3.0",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.2.0",
        "langgraph>=0.0.50",
        "langchain-groq>=0.1.0",
        "langsmith>=0.1.0",
        "pydantic>=2.0",
        "alembic>=1.13.0",
        "sqlalchemy>=2.0",
        "music21>=9.1.0",
        "flask>=2.0",
        "gdown>=4.7.0",
        "pydub>=0.25.0",
        "requests>=2.31.0",
        "langchain-community>=0.0.20",
        "python-dotenv>=1.0.0",
        "moviepy>=1.0.3",  # For MP4 blending/viz
        "gunicorn>=21.0",  # For Render
    ],
    python_requires=">=3.10",
)