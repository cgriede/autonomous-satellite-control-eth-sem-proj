from pint import UnitRegistry

UREG = UnitRegistry()

# Most common: set pretty-print with exponent notation or compact form
UREG.formatter.default_format = "~.3f~P"
# or ".2f~P"    ← 2 decimal places, short pretty
# or "P"        ← long pretty (meter / second ** 2)
# or "~"        ← short default (m / s ** 2)
# or "H"        ← HTML
# or "L"        ← LaTeX