FROM langchain/langgraph-api:3.12

RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -c /api/constraints.txt langgraph-cli[inmem] langchain langchain-openai langchain-community pydantic

# Copy the entire project
COPY . /app

# Set up the Python package
RUN set -ex && \
    cd /app && \
    for line in '[project]' \
                'name = "trantor"' \
                'version = "0.1"' \
                '[tool.setuptools.package-data]' \
                '"*" = ["**/*"]'; do \
        echo "$line" >> pyproject.toml; \
    done

# Install the package
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -c /api/constraints.txt -e /app

# Set the working directory
WORKDIR /app

# The graph path should be relative to the working directory
ENV LANGSERVE_GRAPHS='{"main": "./agents/main.py:graph"}'