FROM ubuntu:24.04 AS dev

ENV DEBIAN_FRONTEND=noninteractive

ENV KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols
ENV KICAD9_FOOTPRINT_DIR=/usr/share/kicad/footprints
ENV KICAD9_3DMODEL_DIR=/usr/share/kicad/3dmodels
ENV KICAD9_TEMPLATE_DIR=/usr/share/kicad/templates

# Install the tools needed to add the KiCad repository and keyring.
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       curl \
       gnupg \
       lsb-release \
       software-properties-common

RUN add-apt-repository --yes ppa:kicad/kicad-9.0-releases

# Install KiCad 9 along with Python 3 tooling.
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update \
    && apt-get install -y --no-install-recommends \
        kicad=9.0.6* \
        kicad-symbols=9.0.6* \
        kicad-footprints=9.0.6* \
        kicad-templates=7.0.9* \
        python3 \
        python3-pip \
        python3-venv \
        python3-lxml \
        git \
        make \
        librsvg2-bin \
        ghostscript \
        imagemagick \
        pandoc \
        texlive \
        texlive-latex-base \
        texlive-latex-recommended \
        unzip \
        zip \
        xvfb \
        xdotool

# Create a venv for Python automation tools and ensure KiCad's Python modules are available.
RUN python3 -m venv /opt/venv --system-site-packages

ENV VIRTUAL_ENV=/opt/venv
ENV PATH=/workspace/scripts:/opt/venv/bin:$PATH

# Install kibot and easyeda2kicad using the venv pip on the PATH.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install --no-compile kibot easyeda2kicad \
       kicost kikit junit-xml \
       mkdocs mkdocs-material

RUN curl -L -o /tmp/ibom.deb https://github.com/INTI-CMNB/InteractiveHtmlBom/releases/download/v2.10.0-2/interactivehtmlbom.inti-cmnb_2.10.0-2_all.deb && \
    dpkg -i /tmp/ibom.deb

COPY scripts/* /usr/local/bin/

# Cache the combiled python bytecode
# INVESTIGATE: There must be a less clunky way to accomplish this.
RUN kibot >/dev/null 2>&1 || true