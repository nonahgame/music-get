# setup.py
from setuptools import setup, find_packages

setup(
    name="lyricbeats-ai",
    version="0.4.0",
    packages=find_packages(),
    install_requires=[
        # --- Core LangChain / LLM ---
        "langchain>=0.2.0",
        "langgraph>=0.0.60",
        "langchain-groq>=0.1.1",
        "langchain-community>=0.0.33",
        "langsmith>=0.1.12",

        # --- Pydantic / Serialization ---
        "pydantic>=2.5.0",

        # --- Database (if you enable DB later) ---
        "sqlalchemy>=2.0",
        "alembic>=1.13.0",

        # --- Flask Backend ---
        "flask>=2.3.0",
        "gunicorn>=21.0",  # Required by Render

        # --- Environment Variables ---
        "python-dotenv>=1.0.0",

        # --- Audio Processing ---
        "pydub>=0.25.1",
        "ffmpeg-python>=0.2.0",  # moviepy requires ffmpeg; this supports it
        # NOTE: You still need system-level ffmpeg installed on VPS/Render.

        # --- Video Generation (moviepy) ---
        "moviepy>=1.0.3",
        "imageio>=2.34",
        "imageio-ffmpeg>=0.4.9",

        # --- ML / Vector Math ---
        "numpy>=1.26",
        "scipy>=1.11",

        # --- File Download Helper ---
        "gdown>=4.7.0",

        # --- Utility / Requests ---
        "requests>=2.31.0",

        # --- Music Theory (optional but useful for MIDI tasks) ---
        "music21>=9.1.0",
    ],
    python_requires=">=3.10",
)

# then pip install -e .  Or
# python setup.py install or
# python setup.py sdist bdist_wheel
#pip install dist/*.whl
# remember update pip *
# pip install --upgrade pip setuptools wheel
