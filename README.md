# Raspberry Launchpad

A utility providing information and functions helpful as you prepare to leave
your home.

Uses a [PiPiRus e-ink display](https://github.com/PiSupply/PaPiRus#papirus) for
the Raspberry Pi Zero (W) and Python 3.

## Current features

* Sunrise and sunset

## Planned

* Precipitation
* High and low temperatures
* Measuring pet food/water bowl weights over time

## TODO

pipenv, systemd service, fpm package

Download sun data
    https://aa.usno.navy.mil/data/docs/RS_OneYear.php
    https://aa.usno.navy.mil/cgi-bin/aa_rstablew.pl?ID=AA&year=2019&task=0&state=MI&place=Ann+Arbor
Account for DST
