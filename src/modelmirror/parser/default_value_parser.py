from modelmirror.parser.value_parser import FormatValidation, ParsedValue, ValueParser


class DefaultValueParser(ValueParser):
    def __init__(self):
        super().__init__()

    def _validate(self, value: str) -> FormatValidation:
        return FormatValidation(is_valid=True)

    def _parse(self, value: str) -> ParsedValue:
        if ":" in value:
            id, instance = value.split(":", 1)
            return ParsedValue(id=id, instance=instance)
        return ParsedValue(id=value, instance=None)
