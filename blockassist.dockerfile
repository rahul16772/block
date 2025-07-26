FROM accetto/ubuntu-vnc-xfce-g3:22.04

USER root

# Copy source over.
COPY --chown=headless:headless . /home/headless/blockassist

# Install system deps + pip.
RUN apt-get update && apt-get install -y --quiet \
  python3 python3-pip python3-venv \
  git curl wget zip \
  unzip ffmpeg libsm6 libxext6

# Install Java 8u152.
# Modified from https://github.com/zulu-openjdk/zulu-openjdk/blob/master/debian/8u152-8.25.0.1/Dockerfile
RUN apt-get -yqq update && \
  apt-get -yqq install apt-transport-https && \
  echo "deb http://repos.azulsystems.com/debian stable  main" >> /etc/apt/sources.list.d/zulu.list && \
  apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 0x219BD9C9 && \
  apt-get -yqq update && \
  apt-get -yqq install zulu-8=8.25.0.1 && \
  apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

USER headless
WORKDIR /home/headless/blockassist

RUN python3 -m venv .venv
ENV PATH="/home/headless/blockassist/.venv/bin:$PATH"
RUN python3 -m pip install -e .

ENV TMPDIR=/tmp/
EXPOSE 5901 6901

CMD ["python", "-m", "malmo.minecraft", "launch", "--num_instances", "2", "--goal_visibility", "True", "False"]
