from pint import UnitRegistry

units = UnitRegistry()

raw_value = 30
raw_units = units.celsius

raw_quantity = units.Quantity(raw_value, raw_units)
print(raw_quantity)

print(raw_quantity.to('fahrenheit'))