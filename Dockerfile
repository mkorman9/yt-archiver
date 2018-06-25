FROM python:3.5

RUN mkdir -p /opt/ytarchiver && mkdir -p /data
COPY . /opt/ytarchiver
RUN useradd -ms /bin/bash ytarchiver &&\
    chown -R ytarchiver:ytarchiver /opt/ytarchiver && chown -R ytarchiver:ytarchiver /data &&\
    chmod u+x /opt/ytarchiver/docker-entrypoint.sh

USER ytarchiver
WORKDIR /opt/ytarchiver
RUN pip install --user --no-warn-script-location -e .

CMD exec /bin/bash docker-entrypoint.sh
