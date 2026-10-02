FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /opt/app

COPY requirements.txt /opt/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /opt/app/
RUN chmod +x /opt/app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/opt/app/entrypoint.sh"]
