FROM python:3.12-alpine

RUN mkdir -p /opt/nightlife-agent/src/ /opt/nightlife-agent/etc/topics/
WORKDIR /opt/nightlife-agent/src/

COPY agent.requirements.txt /opt/nightlife-agent/src/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /opt/nightlife-agent/src/requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1
ENV NIGHTLIFE_AGENT_ENV_FILE /opt/nightlife-agent/etc/env
ENV NIGHTLIFE_AGENT_TOPICS_DIR /opt/nightlife-agent/etc/topics/

COPY agent.py /opt/nightlife-agent/src/agent.py
ENTRYPOINT ["uvicorn", "agent:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
