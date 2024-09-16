from datetime import datetime

from django.conf import settings
from django.utils.crypto import constant_time_compare, salted_hmac
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import base36_to_int, int_to_base36


class ShareProfileTokenGenerator(PasswordResetTokenGenerator):
    """
    Would like to generate a token so that each profile share has a unique
    link that is only valid for a specified time period
    https://simpleisbetterthancomplex.com/tutorial/2016/08/24/how-to-create-one-time-link.html
    """
    def make_token(self, profile):
        pass

    def check_token(self, profile, token):
        pass
