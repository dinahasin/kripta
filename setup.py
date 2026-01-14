from setuptools import setup, find_packages

setup(
    name="kripta",
    version="0.1.0",
    description="Gestionnaire de mots de passe et crypteur de dossiers avec architecture professionnelle moderne",
    author="Dinahasina",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PySide6>=6.6.0",
    ],
    python_requires=">=3.10",
)
