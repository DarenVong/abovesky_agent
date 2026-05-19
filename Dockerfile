FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY abovesky_agent/ ./abovesky_agent/
CMD ["uvicorn", "abovesky_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
