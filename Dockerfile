# Based on: https://github.com/ibm-functions/runtime-python/tree/master/python3.7
FROM kpavel/pywren_runtime:base37

RUN apt update
RUN apt install telnet

RUN pip3 install pygeohash numpy geolib paho-mqtt

RUN pip3 install dataClay==2.5

COPY stubs action/stubs
COPY cfgfiles action/cfgfiles

RUN mkdir /lithops

WORKDIR /lithops

ADD . /lithops

RUN python3 setup.py develop

RUN apt update

WORKDIR /
