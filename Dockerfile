# Axelera-Hailo Benchmark Analysis Docker Environment
# Provides reproducible environment for statistical analysis and validation

FROM python:3.9-slim

LABEL maintainer="Axelera AI Benchmark Analysis Team"
LABEL description="Reproducible environment for AI accelerator benchmark analysis"
LABEL version="2.0"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /benchmark-analysis

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional statistical and validation packages
RUN pip install --no-cache-dir \
    jupyter \
    matplotlib \
    seaborn \
    plotly \
    scipy \
    scikit-learn

# Copy analysis code and data
COPY src/ ./src/
COPY data/ ./data/
COPY docs/ ./docs/

# Copy papers and documentation
COPY papers/ ./papers/
COPY README.md .
COPY LICENSE .

# Set environment variables
ENV PYTHONPATH=/benchmark-analysis/src
ENV BENCHMARK_DATA_PATH=/benchmark-analysis/data

# Create directories for outputs
RUN mkdir -p /benchmark-analysis/outputs
RUN mkdir -p /benchmark-analysis/validation

# Set permissions
RUN chmod +x src/analysis/*.py
RUN chmod +x src/validation/*.py

# Expose port for Jupyter notebook (optional)
EXPOSE 8888

# Default command runs validation
CMD ["python", "src/validation/validate_calculations.py"]

# Alternative commands:
# docker run -it benchmark-analysis python src/analysis/extract_real_data_only.py
# docker run -p 8888:8888 benchmark-analysis jupyter notebook --ip=0.0.0.0 --allow-root --no-browser