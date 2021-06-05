# Based on: https://github.com/ibm-functions/runtime-python/tree/master/python3.7
FROM kpavel/pywren_runtime:base37

RUN apt update -y
RUN apt install -y libgl1-mesa-glx libglib2.0-0

RUN pip3 install sklearn pygeohash numpy geolib paho-mqtt opencv-python shapely
RUN pip3 install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple dataClay==2.6.dev20210528

COPY stubs action/stubs
COPY cfgfiles action/cfgfiles

RUN mkdir /lithops

WORKDIR /lithops

ADD . /lithops

RUN python3 setup.py develop

RUN apt update

WORKDIR /root
COPY .lithops .lithops

WORKDIR /
