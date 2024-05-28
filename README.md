# Plot Director

## Overview
Plot Director is a process that consumes plotter commands from a text file generated by 
[OPENRNDR](https://github.com/openrndr/openrndr) and the add-on feature 
[OPENRNDR Plot](https://github.com/nfletton/openrndr-plot)

## Features
- Executes [AxiDraw Python API](https://axidraw.com/doc/py_api/) commands contained in a text file
- Ability to define reusable sets of API commands for operations such a paintbrush dipping and washing. 
- Notification of plot completion via an optional webhook

## Issues
### Hardcoded penlift
The `penlift` [API option](https://axidraw.com/doc/py_api/#penlift) is hardcoded to the brushless servo
as this option cannot be set in the command text file due to a bug in the Python API. Edit the script if
necessary for your setup.

## Candidate Features
- process keyboard input while running
  - ability to stop a plot and restart at stop point  
  - ability to pause a plot and restart
- display of plot progression
  - distance travelled relative to total distance
  - time so far relative to total time estimate
- logging for command processing progression
- improved commandline option processing
- webhook notification of:
  - pen change required
  - drawing medium refill required