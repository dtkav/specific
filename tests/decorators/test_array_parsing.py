from werkzeug.datastructures import MultiDict

import pytest
from specific.decorators.array_parsing import (AlwaysMultiArrayParser,
                                               FirstValueArrayParser,
                                               Swagger2ArrayParser)

QUERY1 = MultiDict([("letters", "a"), ("letters", "b,c"),
                    ("letters", "d,e,f")])
QUERY2 = MultiDict([("letters", "a"), ("letters", "b|c"),
                    ("letters", "d|e|f")])
PATH1 = {"letters": "d,e,f"}
PATH2 = {"letters": "d|e|f"}
CSV = "csv"
PIPES = "pipes"
MULTI = "multi"


@pytest.mark.parametrize("parser_class, expected, query_in, collection_format", [
        (Swagger2ArrayParser, ['d', 'e', 'f'], QUERY1, CSV),
        (FirstValueArrayParser, ['a'], QUERY1, CSV),
        (AlwaysMultiArrayParser, ['a', 'b', 'c', 'd', 'e', 'f'], QUERY1, CSV),
        (Swagger2ArrayParser, ['a', 'b', 'c', 'd', 'e', 'f'], QUERY1, MULTI),
        (FirstValueArrayParser, ['a', 'b', 'c', 'd', 'e', 'f'], QUERY1, MULTI),
        (AlwaysMultiArrayParser, ['a', 'b', 'c', 'd', 'e', 'f'], QUERY1, MULTI),
        (Swagger2ArrayParser, ['d', 'e', 'f'], QUERY2, PIPES),
        (FirstValueArrayParser, ['a'], QUERY2, PIPES),
        (AlwaysMultiArrayParser, ['a', 'b', 'c', 'd', 'e', 'f'], QUERY2, PIPES)])
def test_array_parser_query_params(parser_class, expected, query_in,
                                   collection_format):
    class Request(object):
        query = query_in
        path_params = {}
        form = {}

    request = Request()
    parameters = [
        {"name": "letters",
         "in": "query",
         "type": "array",
         "items": {"type": "string"},
         "collectionFormat": collection_format}
    ]
    body_defn = {}
    p = parser_class(parameters, body_defn)
    res = p(lambda x: x)(request)
    assert res.query["letters"] == expected


@pytest.mark.parametrize("parser_class, expected, query_in, collection_format", [
        (Swagger2ArrayParser, ['d', 'e', 'f'], QUERY1, CSV),
        (FirstValueArrayParser, ['a'], QUERY1, CSV),
        (AlwaysMultiArrayParser, ['a', 'b', 'c', 'd', 'e', 'f'], QUERY1, CSV),
        (Swagger2ArrayParser, ['a', 'b', 'c', 'd', 'e', 'f'], QUERY1, MULTI),
        (FirstValueArrayParser, ['a', 'b', 'c', 'd', 'e', 'f'], QUERY1, MULTI),
        (AlwaysMultiArrayParser, ['a', 'b', 'c', 'd', 'e', 'f'], QUERY1, MULTI),
        (Swagger2ArrayParser, ['d', 'e', 'f'], QUERY2, PIPES),
        (FirstValueArrayParser, ['a'], QUERY2, PIPES),
        (AlwaysMultiArrayParser, ['a', 'b', 'c', 'd', 'e', 'f'], QUERY2, PIPES)])
def test_array_parser_form_params(parser_class, expected, query_in, collection_format):
    class Request(object):
        query = {}
        form = query_in
        path_params = {}

    request = Request()
    parameters = [
        {"name": "letters",
         "in": "formData",
         "type": "array",
         "items": {"type": "string"},
         "collectionFormat": collection_format}
    ]
    body_defn = {}
    p = parser_class(parameters, body_defn)
    res = p(lambda x: x)(request)
    assert res.form["letters"] == expected


@pytest.mark.parametrize("parser_class, expected, query_in, collection_format", [
        (Swagger2ArrayParser, ['d', 'e', 'f'], PATH1, CSV),
        (FirstValueArrayParser, ['d', 'e', 'f'], PATH1, CSV),
        (AlwaysMultiArrayParser, ['d', 'e', 'f'], PATH1, CSV),
        (Swagger2ArrayParser, ['d', 'e', 'f'], PATH2, PIPES),
        (FirstValueArrayParser, ['d', 'e', 'f'], PATH2, PIPES),
        (AlwaysMultiArrayParser, ['d', 'e', 'f'], PATH2, PIPES)])
def test_array_parser_path_params(parser_class, expected, query_in, collection_format):
    class Request(object):
        query = {}
        form = {}
        path_params = query_in

    request = Request()
    parameters = [
        {"name": "letters",
         "in": "path",
         "type": "array",
         "items": {"type": "string"},
         "collectionFormat": collection_format}
    ]
    body_defn = {}
    p = parser_class(parameters, body_defn)
    res = p(lambda x: x)(request)
    assert res.path_params["letters"] == expected
