FROM python:3

# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
RUN mkdir -p /tmp/pip-tmp/
COPY requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt && rm -rf /tmp/pip-tmp
