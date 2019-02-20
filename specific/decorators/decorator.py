import functools
import logging

logger = logging.getLogger(__name__)


class BaseDecorator(object):

    def __call__(self, function):
        """
        :type function: types.FunctionType
        :rtype: types.FunctionType
        """
        return function

    def __repr__(self):  # pragma: no cover
        """
        :rtype: str
        """
        return '<BaseDecorator>'


class RequestResponseDecorator(BaseDecorator):
    """Manages the lifecycle of the request internally in Specific.
    Filter the SpecificRequest instance to return the corresponding
    framework specific object.
    """

    def __init__(self, api, mimetype):
        self.api = api
        self.mimetype = mimetype

    def __call__(self, function):
        """
        :type function: types.FunctionType
        :rtype: types.FunctionType
        """
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            request = self.api.get_request(*args, **kwargs)
            response = function(request)
            return self.api.get_response(response, self.mimetype, request)

        return wrapper
