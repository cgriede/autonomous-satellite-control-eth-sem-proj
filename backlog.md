# Backlog

## Bugs
- 1d strip is updated incorrectly
- clouds are not (visibly) moving in the simulation
- camera cone is dependant on if we show the main plot or not (should be decoupled)

## structural issues
- camera simulation is called from within render, not true backend desired behaviour (decoupling)

## features
- add telemetry: environment: avg cloud speed

- map area that counts as "observer hit"

- Satellite (Camera) view of mapped area:
 from the satellite, render the current pointing direction’s ground footprint as a visible shape that updates continuously as the satellite orientation/orbit changes, so the mapped area on Earth is clearly visualized.

