"""
Application responsible for data serialization and deserialization to other formats, like binary, JSON, XML, YAML, etc. It supplies
as well functions to download/import fixture files as load them by command line as well.
"""

from core import serialize, deserialize
from serializers.json_format import JsonSerializer
