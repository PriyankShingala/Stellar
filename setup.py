from setuptools import setup, find_packages

setup(
    name="stellar_ai",
    version="0.1.0",
    description="Offline AI-Based Human Activity Recognition for On-Board BAS Experiments (SIH 2026)",
    author="Team Stellar",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "numpy",
        "opencv-python",
        "pyyaml",
        "PySide6",
        "pyttsx3",
        "pydantic"
    ],
    entry_points={
        "console_scripts": [
            "stellar-gui=frontend.app:main",
            "stellar-backend=backend.app.orchestrator:main",
        ],
    },
)
