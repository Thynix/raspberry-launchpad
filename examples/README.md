This is an error page returned with status code 200.

My current suspicion is it fails to parse as XML due to

> The character encoding specified in the HTTP header (utf-8) is different from the value in the <meta\> element (iso-8859-1).

as pointed out by the [W3C validator](https://validator.w3.org/). Specifically, a failure looks like:

```
Traceback (most recent call last):
  File "/usr/lib/python3.5/xml/etree/ElementTree.py", line 1654, in feed
    self.parser.Parse(data, 0)
xml.parsers.expat.ExpatError: not well-formed (invalid token): line 1, column 112
During handling of the above exception, another exception occurred:
Traceback (most recent call last):
  File "/usr/lib/python3.5/runpy.py", line 193, in _run_module_as_main
    "__main__", mod_spec)
  File "/usr/lib/python3.5/runpy.py", line 85, in _run_code
    exec(code, run_globals)
  File "/home/pi/raspberry-launchpad/launchpad/__main__.py", line 149, in <module>
    main()
  File "/home/pi/raspberry-launchpad/launchpad/__main__.py", line 56, in main
    get_temperature_forecast(latitude, longitude)
  File "/home/pi/raspberry-launchpad/launchpad/__main__.py", line 86, in get_temperature_forecast
    root = defusedxml.ElementTree.fromstring(r.text)
  File "/usr/lib/python3/dist-packages/defusedxml/common.py", line 159, in fromstring
    parser.feed(text)
  File "/usr/lib/python3.5/xml/etree/ElementTree.py", line 1656, in feed
    self._raiseerror(v)
  File "/usr/lib/python3.5/xml/etree/ElementTree.py", line 1555, in _raiseerror
    raise err
xml.etree.ElementTree.ParseError: not well-formed (invalid token): line 1, column 112
```
