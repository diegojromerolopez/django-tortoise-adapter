FROM python:3.12-slim-bookworm

WORKDIR /app

# The test script uses only Python standard libraries (urllib, json, unittest)
COPY test_e2e.py .

# Run unittest
CMD ["python", "-m", "unittest", "test_e2e.py"]
