# SPDX-License-Identifier: MIT

from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase


class CreateLocalAccountCommandTest(TestCase):
    def test_creates_account_once_without_resetting_existing_password(self):
        with patch("sys.stdin", StringIO("first-password\n")):
            call_command("create_local_account", username="annotator")

        user = get_user_model().objects.get(username="annotator")
        self.assertTrue(user.check_password("first-password"))

        with patch("sys.stdin", StringIO("second-password\n")):
            call_command("create_local_account", username="annotator")

        user.refresh_from_db()
        self.assertTrue(user.check_password("first-password"))
