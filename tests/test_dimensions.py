import pytest
from roomlab.dimensions import parse_dimension,format_dimension
@pytest.mark.parametrize(('raw','expected'), [('9 ft',108),("9’ 11”",119),('9 feet 11 inches',119),('11.5 ft',138),('119 inches',119),('254 cm',100)])
def test_parse(raw,expected): assert parse_dimension(raw)==pytest.approx(expected)
def test_format(): assert format_dimension(119)=="9’ 11”"
