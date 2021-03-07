# Based on: https://github.com/ibm-functions/runtime-python/tree/master/python3.7
FROM kpavel/pywren_runtime:base37

RUN apt update -y
RUN apt install -y libgl1-mesa-glx libglib2.0-0

RUN pip3 install pygeohash numpy geolib paho-mqtt opencv-python dataClay==2.5 shapely

COPY stubs action/stubs
COPY cfgfiles action/cfgfiles

RUN mkdir /lithops

WORKDIR /lithops

ADD . /lithops

RUN python3 setup.py develop

RUN apt update

WORKDIR /
