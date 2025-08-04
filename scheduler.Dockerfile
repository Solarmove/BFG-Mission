FROM python:3.12-slim-bookworm


ARG TZ=Europe/Kyiv
ENV TZ=${TZ} \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/root/.local/bin/:$PATH"

# установить tzdata + curl/сертификаты и задать зону
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata curl ca-certificates \
    && ln -snf /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo "${TZ}" > /etc/timezone \
    && dpkg-reconfigure -f noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*


# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, using the frozen lockfile
WORKDIR /app
RUN uv sync

CMD ["uv", "run", "arq", "scheduler.main.WorkerSettings"]