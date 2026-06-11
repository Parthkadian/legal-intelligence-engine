FROM python:3.10-slim

WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir pip --upgrade

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose port (Render injects $PORT at runtime)
EXPOSE 8501

# Run Streamlit frontend (uses $PORT from Render, falls back to 8501 locally)
CMD streamlit run ui/app.py --server.address 0.0.0.0 --server.port ${PORT:-8501}
