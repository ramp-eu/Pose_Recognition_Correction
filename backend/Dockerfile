FROM ubuntu:20.04 as build_openvino

# get and build openvino
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    git-lfs \
    sudo \
    && rm -rf /var/lib/apt/lists/*
ARG OPENVINO_FORK="openvinotoolkit"
ARG OPENVINO_BRANCH="master"
RUN git-lfs install; \
    git clone https://github.com/${OPENVINO_FORK}/openvino.git

WORKDIR /openvino
RUN git submodule update --init --recursive --jobs=$(nproc --all)

RUN chmod +x install_build_dependencies.sh
ENV DEBIAN_FRONTEND=noninteractive
RUN ./install_build_dependencies.sh
RUN mkdir /openvino/build
WORKDIR /openvino/build
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cython \
    && rm -rf /var/lib/apt/lists/*
RUN cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DENABLE_AUTO=OFF \
    -DENABLE_HETERO=OFF \
    -DENABLE_INTEL_GNA=OFF \
    -DENABLE_INTEL_GPU=OFF \
    -DENABLE_INTEL_MYRIAD=OFF \
    -DENABLE_INTEL_MYRIAD_COMMON=OFF \
    -DENABLE_OPENCV=ON \
    -DENABLE_PYTHON=ON \
    -DCMAKE_INSTALL_PREFIX=install\
    ..
RUN make --jobs=$(nproc --all) \
    && make install
CMD [ "bash" ]

# get and build opencv
FROM build_openvino as build_opencv
WORKDIR /
RUN git clone https://github.com/opencv/opencv.git
RUN mkdir /opencv/build
WORKDIR /opencv/build
RUN cmake \
    -DCMAKE_INSTALL_PREFIX=install \
    ..
RUN make --jobs=$(nproc --all)
RUN make install
CMD [ "bash" ]


# build open_model_zoo
FROM build_opencv as build_omz
RUN mkdir /openvino/thirdparty/open_model_zoo/demos/build
WORKDIR /openvino/thirdparty/open_model_zoo/demos/build
RUN pip install -r ../requirements.txt
RUN source /openvino/build/install/setupvars.sh ;\
    cmake \
        -DENABLE_PYTHON=ON \
        -DOpenCV_DIR=/opencv/build/install/lib/cmake/opencv4/ \
        -DOpenVINO_DIR=/openvino/build/install/runtime/cmake/ \
        -DCMAKE_INSTALL_PREFIX=/openvino/build/install \
        ..
RUN make --jobs=$(nproc --all)
RUN make install
CMD [ "bash" ]

FROM ubuntu:20.04 as runtime
# get librealsense and copy everything in place
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        dirmngr \
        gpg-agent \
    && rm -rf /var/lib/apt/lists/* ;\
    apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE;\
    add-apt-repository "deb https://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main" -u ;\
    apt-get update && \
    apt-get install -y --no-install-recommends \
        librealsense2 \
        librealsense2-utils \
        python3 \
        libpython3.8 \
        python3-pip \
        libgl1 \
    && rm -rf /var/lib/apt/lists/*
# copy stuff from previous stages
COPY --from=build_openvino /openvino/build/install /opt/openvino
COPY --from=build_omz /openvino/thirdparty/open_model_zoo/demos/build/intel64/Release /opt/open_model_zoo
COPY --from=build_opencv /opencv/build/install /opt/opencv
# adjust paths and ENVS
ENV PYTHONPATH=/opt/open_model_zoo/
ENV LD_LIBRARY_PATH=/opt/opencv/lib/
RUN echo "source /opt/openvino/setupvars.sh" >> /etc/bash.bashrc

#copy app and install dependencies
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app
CMD [ "bash" ]
