"""
Auto-generated device metadata for mioc_flop.
"""
TYPE_NAME = "mioc_flop"
INPUT_PINS = [
  "in1",
  "in2",
  "in3",
  "in4"
]
OUTPUT_PINS = [
  "q",
  "qbar"
]
IS_SEQUENTIAL = True
ATTRS = {}

class MiocFlop:
    type_name = TYPE_NAME
    input_pins = tuple(INPUT_PINS)
    output_pins = tuple(OUTPUT_PINS)
    is_sequential = IS_SEQUENTIAL
    attrs = dict(ATTRS)
