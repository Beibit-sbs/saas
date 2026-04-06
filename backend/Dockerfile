FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
	&& apt-get install -y --no-install-recommends postgresql-client \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY tests ./tests
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY pytest.ini ./pytest.ini

EXPOSE 8000
CMD ["sh", "-c", "i=0; until alembic -c /app/alembic.ini upgrade head; do i=$((i+1)); if [ \"$i\" -ge 15 ]; then echo 'alembic failed after retries'; exit 1; fi; echo \"alembic retry $i/15\"; sleep 2; done; python -m app.bootstrap_admin && exec python -m uvi\"\"corn app.main:app --host 0.0.0.0 --port 8000"]
