import collections
import copy
import functools
import logging
import sys

import six
from jsonschema import Draft4Validator, ValidationError, draft4_format_checker
from werkzeug import FileStorage

from ..exceptions import ExtraParameterProblem
from ..json_schema import Draft4RequestValidator, Draft4ResponseValidator
from ..problem import problem
from ..content_types import KNOWN_CONTENT_TYPES
from ..types import TypeValidationError, coerce_type
from ..utils import is_null, is_nullable

logger = logging.getLogger(__name__)


def validate_parameter_list(request_params, spec_params):
    request_params = set(request_params)
    spec_params = set(spec_params)

    return request_params.difference(spec_params)


class RequestBodyValidator(object):

    def __init__(self, schema, consumes, api, is_null_value_valid=False, validator=None,
                 strict_validation=False):
        """
        :param schema: The schema of the request body
        :param consumes: The list of content types the operation consumes
        :param is_null_value_valid: Flag to indicate if null is accepted as valid value.
        :param validator: Validator class that should be used to validate passed data
                          against API schema. Default is jsonschema.Draft4Validator.
        :type validator: jsonschema.IValidator
        :param strict_validation: Flag indicating if parameters not in spec are allowed
        """
        self.consumes = consumes
        self.schema = schema
        self.has_default = schema.get('default', False)
        self.is_null_value_valid = is_null_value_valid
        validatorClass = validator or Draft4RequestValidator
        self.validator = validatorClass(schema, format_checker=draft4_format_checker)
        self.api = api
        self.strict_validation = strict_validation
        self._content_handlers = [
            de(self.validator,
               self.schema,
               self.strict_validation,
               self.is_null_value_valid) for de in KNOWN_CONTENT_TYPES
        ]

    def register_content_handler(self, cv):
        deser = cv(self.validator,
                   self.schema,
                   self.strict_validation,
                   self.is_null_value_valid)
        self._content_handlers += [deser]

    def lookup_content_handler(self, request):
        matches = [
            v for v in self._content_handlers
            if request.content_type is not None and
               v.regex.match(request.content_type)
        ]
        if len(matches) > 1:
            logger.warning("Content could be handled by multiple validators")
        if matches:
            return matches[0]

    def __call__(self, function):
        """
        :type function: types.FunctionType
        :rtype: types.FunctionType
        """

        @functools.wraps(function)
        def wrapper(request):
            content_handler = self.lookup_content_handler(request)
            exact_match = (
                request.content_type is not None and
                request.content_type in self.consumes
            )
            partial_match = content_handler and content_handler.name in self.consumes
            if not (exact_match or partial_match):
                msg = "Invalid Content-type ({content_type}), expected one of {consumes}"
                msg = msg.format(content_type=request.content_type, consumes=self.consumes)
                return problem(415, "Unsupported Media Type", msg)

            if content_handler:
                error = content_handler.validate(request)
                if error:
                    return error
            else:
                logger.debug("No handler for ({content_type})".format(
                             content_type=request.content_type))

            response = function(request)
            return response

        return wrapper


class ResponseBodyValidator(object):
    def __init__(self, schema, validator=None):
        """
        :param schema: The schema of the response body
        :param validator: Validator class that should be used to validate passed data
                          against API schema. Default is jsonschema.Draft4Validator.
        :type validator: jsonschema.IValidator
        """
        ValidatorClass = validator or Draft4ResponseValidator
        self.validator = ValidatorClass(schema, format_checker=draft4_format_checker)

    def validate_schema(self, data, url):
        # type: (dict, AnyStr) -> Union[SpecificResponse, None]
        try:
            self.validator.validate(data)
        except ValidationError as exception:
            logger.error("{url} validation error: {error}".format(url=url,
                                                                  error=exception),
                         extra={'validator': 'response'})
            six.reraise(*sys.exc_info())

        return None


class ParameterValidator(object):
    def __init__(self, parameters, api, strict_validation=False):
        """
        :param parameters: List of request parameter dictionaries
        :param api: api that the validator is attached to
        :param strict_validation: Flag indicating if parameters not in spec are allowed
        """
        self.parameters = collections.defaultdict(list)
        for p in parameters:
            self.parameters[p['in']].append(p)

        self.api = api
        self.strict_validation = strict_validation

    @staticmethod
    def validate_parameter(parameter_type, value, param, param_name=None):
        if value is not None:
            if is_nullable(param) and is_null(value):
                return

            try:
                converted_value = coerce_type(param, value, parameter_type, param_name)
            except TypeValidationError as e:
                return str(e)

            param = copy.deepcopy(param)
            param = param.get('schema', param)
            if 'required' in param:
                del param['required']
            try:
                if parameter_type == 'formdata' and param.get('type') == 'file':
                    Draft4Validator(
                        param,
                        format_checker=draft4_format_checker,
                        types={'file': FileStorage}).validate(converted_value)
                else:
                    Draft4Validator(
                        param, format_checker=draft4_format_checker).validate(converted_value)
            except ValidationError as exception:
                debug_msg = 'Error while converting value {converted_value} from param ' \
                            '{type_converted_value} of type real type {param_type} to the declared type {param}'
                fmt_params = dict(
                    converted_value=str(converted_value),
                    type_converted_value=type(converted_value),
                    param_type=param.get('type'),
                    param=param
                )
                logger.info(debug_msg.format(**fmt_params))
                return str(exception)

        elif param.get('required'):
            return "Missing {parameter_type} parameter '{param[name]}'".format(**locals())

    def validate_query_parameter_list(self, request):
        request_params = request.query.keys()
        spec_params = [x['name'] for x in self.parameters.get('query', [])]
        return validate_parameter_list(request_params, spec_params)

    def validate_formdata_parameter_list(self, request):
        request_params = request.form.keys()
        spec_params = [x['name'] for x in self.parameters.get('formData', [])]
        return validate_parameter_list(request_params, spec_params)

    def validate_query_parameter(self, param, request):
        """
        Validate a single query parameter (request.args in Flask)

        :type param: dict
        :rtype: str
        """
        val = request.query.get(param['name'])
        return self.validate_parameter('query', val, param)

    def validate_path_parameter(self, param, request):
        val = request.path_params.get(param['name'].replace('-', '_'))
        return self.validate_parameter('path', val, param)

    def validate_header_parameter(self, param, request):
        val = request.headers.get(param['name'])
        return self.validate_parameter('header', val, param)

    def validate_formdata_parameter(self, param_name, param, request):
        if param.get('type') == 'file' or param.get('format') == 'binary':
            val = request.files.get(param_name)
        else:
            val = request.form.get(param_name)

        return self.validate_parameter('formdata', val, param)

    def __call__(self, function):
        """
        :type function: types.FunctionType
        :rtype: types.FunctionType
        """

        @functools.wraps(function)
        def wrapper(request):
            logger.debug("%s validating parameters...", request.url)

            if self.strict_validation:
                query_errors = self.validate_query_parameter_list(request)
                formdata_errors = self.validate_formdata_parameter_list(request)

                if formdata_errors or query_errors:
                    raise ExtraParameterProblem(formdata_errors, query_errors)

            for param in self.parameters.get('query', []):
                error = self.validate_query_parameter(param, request)
                if error:
                    response = problem(400, 'Bad Request', error)
                    return self.api.get_response(response)

            for param in self.parameters.get('path', []):
                error = self.validate_path_parameter(param, request)
                if error:
                    response = problem(400, 'Bad Request', error)
                    return self.api.get_response(response)

            for param in self.parameters.get('header', []):
                error = self.validate_header_parameter(param, request)
                if error:
                    response = problem(400, 'Bad Request', error)
                    return self.api.get_response(response)

            for param in self.parameters.get('formData', []):
                error = self.validate_formdata_parameter(param["name"], param, request)
                if error:
                    response = problem(400, 'Bad Request', error)
                    return self.api.get_response(response)

            return function(request)

        return wrapper
