# Raspberry Launchpad

A utility providing information and functions helpful as you prepare to go
outside.

Uses a [PiPiRus e-ink display](https://github.com/PiSupply/PaPiRus#papirus) for
the Raspberry Pi Zero (W) and Python 3.

![Demonstration photo](img/sun_times.jpg)

## Current features

* Sunrise and sunset

## Planned

* Precipitation
* High and low temperatures
* Measuring pet food/water bowl weights over time

## Requirements

* A PaPiRus HAT
* [PaPiRus libraries installed](https://github.com/PiSupply/PaPiRus#setup-papirus)
* Dependency packages:

    apt install python3 python3-pandas

## TODO

pipenv, configuration file, fpm package

* Download sun data
  * https://aa.usno.navy.mil/data/docs/RS_OneYear.php
  * https://aa.usno.navy.mil/cgi-bin/aa_rstablew.pl?ID=AA&year=2019&task=0&state=MI&place=Ann+Arbor
* Account for DST
