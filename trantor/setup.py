from setuptools import setup, find_packages

setup(
    name="trantor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langgraph-cli[inmem]",
        "langchain",
        "langchain-openai",
        "langchain-community",
        "pydantic",
        "python-dotenv"
    ],
    python_requires=">=3.12",
)
