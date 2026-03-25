from pint import Quantity


def require_compatible_units(value: object, expected_unit: str, name: str) -> None:
    if not isinstance(value, Quantity):
        raise TypeError(f"{name} must be a pint quantity.")
    try:
        value.to(expected_unit)
    except Exception as exc:
        raise ValueError(f"{name} must be compatible with {expected_unit}.") from exc
