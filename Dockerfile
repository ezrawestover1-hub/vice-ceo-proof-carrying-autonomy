FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir \
  "fastapi>=0.115.0" \
  "google-adk>=1.21.0" \
  "google-cloud-firestore>=2.20.0" \
  "uvicorn[standard]>=0.30.0"

# The reviewer routes build an integrity/preflight report from these checked-in
# release inputs. Keep them in the image so the public Cloud Run surface has
# the same evidence it reports locally.
COPY Dockerfile ./Dockerfile
COPY agents-cli-manifest.yaml ./agents-cli-manifest.yaml
COPY scripts ./scripts
COPY app ./app

EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.fast_api_app:app --host 0.0.0.0 --port ${PORT}"]
