FROM python:3.13-slim

ARG ANSIBLE_CORE_VERSION=2.19.5
RUN apt-get update && apt-get install -y --no-install-recommends openssh-client ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir \
       "ansible-core==${ANSIBLE_CORE_VERSION}" hvac==2.4.0 requests==2.32.5 ncclient==0.7.0 pytest==8.4.2

COPY collections/requirements.yml /tmp/collections.yml
RUN ansible-galaxy collection install -r /tmp/collections.yml \
    && rm /tmp/collections.yml

RUN useradd --create-home --uid 10001 automation \
    && install -d -m 700 -o automation -g automation /home/automation/.ssh
WORKDIR /workspace
USER automation
ENTRYPOINT ["ansible-playbook"]
CMD ["--version"]
