from jsonschema.exceptions import ValidationError
from werkzeug.exceptions import Forbidden, Unauthorized

from .problem import problem


class SpecificException(Exception):
    pass


class ProblemException(SpecificException):
    def __init__(self, status=400, title=None, detail=None, type=None,
                 instance=None, headers=None, ext=None):
        """
        This exception is holds arguments that are going to be passed to the
        `specific.problem` function to generate a propert response.
        """
        self.status = status
        self.title = title
        self.detail = detail
        self.type = type
        self.instance = instance
        self.headers = headers
        self.ext = ext

    def to_problem(self):
        return problem(status=self.status, title=self.title, detail=self.detail,
                       type=self.type, instance=self.instance, headers=self.headers,
                       ext=self.ext)


class ResolverError(LookupError):
    def __init__(self, reason='Unknown reason', exc_info=None):
        """
        :param reason: Reason why the resolver failed.
        :type reason: str
        :param exc_info: If specified, gives details of the original exception
            as returned by sys.exc_info()
        :type exc_info: tuple | None
        """
        self.reason = reason
        self.exc_info = exc_info

    def __str__(self):  # pragma: no cover
        return '<ResolverError: {}>'.format(self.reason)

    def __repr__(self):  # pragma: no cover
        return '<ResolverError: {}>'.format(self.reason)


class InvalidSpecification(SpecificException, ValidationError):
    pass


class NonConformingResponse(SpecificException):
    def __init__(self, reason='Unknown Reason', message=None):
        """
        :param reason: Reason why the response did not conform to the specification
        :type reason: str
        """
        self.reason = reason
        self.message = message

    def __str__(self):  # pragma: no cover
        return '<NonConformingResponse: {}>'.format(self.reason)

    def __repr__(self):  # pragma: no cover
        return '<NonConformingResponse: {}>'.format(self.reason)


class NonConformingResponseBody(NonConformingResponse):
    def __init__(self, message, reason="Response body does not conform to specification"):
        super(NonConformingResponseBody, self).__init__(reason=reason, message=message)


class NonConformingResponseHeaders(NonConformingResponse):
    def __init__(self, message, reason="Response headers do not conform to specification"):
        super(NonConformingResponseHeaders, self).__init__(reason=reason, message=message)


class OAuthProblem(Unauthorized):
    pass


class OAuthResponseProblem(OAuthProblem):
    def __init__(self, token_response, **kwargs):
        self.token_response = token_response
        super(OAuthResponseProblem, self).__init__(**kwargs)


class OAuthScopeProblem(Forbidden):
    def __init__(self, token_scopes, required_scopes, **kwargs):
        self.required_scopes = required_scopes
        self.token_scopes = token_scopes

        super(OAuthScopeProblem, self).__init__(**kwargs)


class ExtraParameterProblem(ProblemException):
    def __init__(self, formdata_parameters, query_parameters, title=None, detail=None, **kwargs):
        self.extra_formdata = formdata_parameters
        self.extra_query = query_parameters

        # This keep backwards compatibility with the old returns
        if detail is None:
            if self.extra_query:
                detail = "Extra {parameter_type} parameter(s) {extra_params} not in spec"\
                    .format(parameter_type='query', extra_params=', '.join(self.extra_query))
            elif self.extra_formdata:
                detail = "Extra {parameter_type} parameter(s) {extra_params} not in spec"\
                    .format(parameter_type='formData', extra_params=', '.join(self.extra_formdata))

        super(ExtraParameterProblem, self).__init__(title=title, detail=detail, **kwargs)
