from functools import wraps

from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


class persist_session_vars(object):
    """
    Some views, such as login and logout, will reset all session state.
    (via a call to ``request.session.cycle_key()`` or ``session.flush()``).
    That is a security measure to mitigate session fixation vulnerabilities.

    By applying this decorator, some values are retained.
    Be very aware what kind of variables you want to persist.

    SO source: https://stackoverflow.com/a/41849076
    """

    def __init__(self, vars):
        self.vars = vars

    def __call__(self, view_func):

        @wraps(view_func)
        def inner(request, *args, **kwargs):
            # Backup first
            session_backup = {}
            for var in self.vars:
                try:
                    session_backup[var] = request.session[var]
                except KeyError:
                    pass

            # Call the original view
            response = view_func(request, *args, **kwargs)

            # Restore variables in the new session
            for var, value in session_backup.items():
                request.session[var] = value

            return response

        return inner


class NeverCacheMixin(object):
    """source: https://stackoverflow.com/a/35385953"""
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(NeverCacheMixin, self).dispatch(*args, **kwargs)
