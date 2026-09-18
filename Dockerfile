FROM python:3.11-alpine
WORKDIR /app
COPY . .
ENV PORT=8080
EXPOSE 8080
# Range-aware static host: byte-range requests (206) are required for mp4
# playback on Safari and iOS; the stdlib simple server only returns 200.
CMD ["python", "serve.py"]
