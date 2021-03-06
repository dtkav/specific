import logging
import re

from jsonschema import ValidationError

from .exceptions import ExtraParameterProblem
from .problem import problem
from .types import coerce_type
from .utils import is_null

logger = logging.getLogger(__name__)


class ContentType(object):

    def __init__(self, validator, schema, strict, is_null_value_valid):
        self.schema = schema
        self.strict_validation = strict
        self.is_null_value_valid = is_null_value_valid
        self.validator = validator
        self.has_default = schema.get('default', False)

    def validate_schema(self, data, url):
        # type: (dict, AnyStr) -> Union[ConnexionResponse, None]
        if self.is_null_value_valid and is_null(data):
            return None

        try:
            self.validator.validate(data)
        except ValidationError as exception:
            logger.error("{url} validation error: {error}".format(url=url,
                                                                  error=exception.message),
                         extra={'validator': 'body'})
            return problem(400, 'Bad Request', str(exception.message))

        return None

    def deserialize(self, request):
        return request.body

    def validate(self, request):
        data = self.deserialize(request)
        errors = self.validate_schema(data, request.url)
        if errors and not self.has_default:
            return errors


class StreamingContentType(ContentType):
    name = "application/octet-stream"
    regex = re.compile(r'^application\/octet-stream.*')

    def validate(self, request):
        # Don't validate, leave stream for user to read
        pass


class JSONContentType(ContentType):
    name = "application/json"
    regex = re.compile(r'^application\/json.*|^.*\+json$')

    def deserialize(self, request):
        data = request.json
        empty_body = not(request.body or request.form or request.files)
        if data is None and not empty_body and not self.is_null_value_valid:
            # Content-Type is json but actual body was not parsed
            return problem(400,
                           "Bad Request",
                           "Request body is not valid JSON"
                           )
        return data


def validate_parameter_list(request_params, spec_params):
    request_params = set(request_params)
    spec_params = set(spec_params)

    return request_params.difference(spec_params)


class FormDataContentType(ContentType):
    name = "application/x-www-form-urlencoded"
    regex = re.compile(
        r'^application\/x-www-form-urlencoded.*'
    )

    def _validate_formdata_parameter_list(self, request):
        request_params = request.form.keys()
        spec_params = self.schema.get('properties', {}).keys()
        return validate_parameter_list(request_params, spec_params)

    def deserialize(self, request):
        data = dict(request.form.items()) or \
                   (request.body if len(request.body) > 0 else {})
        data.update(dict.fromkeys(request.files, ''))  # validator expects string..
        logger.debug('%s validating schema...', request.url)

        if self.strict_validation:
            formdata_errors = self._validate_formdata_parameter_list(request)
            if formdata_errors:
                raise ExtraParameterProblem(formdata_errors, [])

        if data:
            props = self.schema.get("properties", {})
            for k, param_defn in props.items():
                if k in data:
                    data[k] = coerce_type(param_defn, data[k], 'requestBody', k)
            # XXX it's surprising to hide this in validation
            request.form = data
        return data


class MultiPartFormDataContentType(FormDataContentType):
    name = "multipart/form-data"
    regex = re.compile(
        r'^multipart\/form-data.*'
    )


KNOWN_CONTENT_TYPES = [
    StreamingContentType,
    JSONContentType,
    FormDataContentType,
    MultiPartFormDataContentType
]
