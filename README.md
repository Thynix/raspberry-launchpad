# Raspberry Launchpad

A utility providing information and functions helpful as you prepare to go
outside.

Uses a [PiPiRus e-ink display](https://github.com/PiSupply/PaPiRus#papirus) for
the Raspberry Pi Zero (W) and Python 3.

![Demonstration photo](img/sun_times.jpg)

## Current features

* Sunrise and sunset
* High and low temperatures

## Planned

* Precipitation
* Measuring pet food/water bowl weights over time

## Requirements

* A PaPiRus HAT
* [PaPiRus libraries installed](https://github.com/PiSupply/PaPiRus#setup-papirus)
* Dependency packages:

    apt install python3 python3-pandas python3-defusedxml python3-requests

## Attribution

* [no wifi by Gregor Cresnar from the Noun Project](https://thenounproject.com/term/no-wifi/488903/)
* [settings error by icon 54 from the Noun Project](https://thenounproject.com/term/settings-error/230271) (lines)
* [settings error by icon 54 from the Noun Project](https://thenounproject.com/term/settings-error/237416) (solid)
* [Arrow by Free Icons from the Noun Project](https://thenounproject.com/term/arrow/2540002)

## TODO

pipenv, configuration file, fpm package, use pytz

* Download sun data if not already present
  * https://aa.usno.navy.mil/data/docs/RS_OneYear.php
  * https://aa.usno.navy.mil/cgi-bin/aa_rstablew.pl?ID=AA&year=2019&task=0&state=MI&place=Ann+Arbor
* Accomodate locations like Barrow, Alaska that have

    (**** object continuously above horizon)                                                      (---- object continuously below horizon)

  entries
