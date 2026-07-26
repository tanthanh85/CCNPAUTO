FROM python:3.11-alpine

LABEL org.opencontainers.image.title="Loopback1 Auto Recovery"
LABEL org.opencontainers.image.description="Receives IOS XE syslog and re-enables Loopback1 through Netmiko"

WORKDIR /app
COPY requirements.txt /app/requirements.txt
COPY loopback_recovery.py /app/loopback_recovery.py

ENV SYSLOG_HOST=0.0.0.0 \
    SYSLOG_PORT=5514 \
    LOG_LEVEL=INFO

RUN apk add --no-cache iproute2 \
    && python3 -m pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 5514/udp

CMD ["python3", "/app/loopback_recovery.py"]
