FROM python:3.11-alpine
WORKDIR /app
COPY . .
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "python -m http.server ${PORT} --bind 0.0.0.0"]
