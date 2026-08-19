# SPDX-License-Identifier: MIT

import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the local annotation account without exposing its password in process arguments"

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)

    def handle(self, *args, **options):
        username = options["username"].strip()
        if not username:
            raise CommandError("账户名不能为空。")

        password = sys.stdin.readline().rstrip("\r\n")
        if len(password) < 8:
            raise CommandError("密码至少需要 8 个字符。")

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"is_active": True},
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS("本地账户已创建。"))
        else:
            self.stdout.write("本地账户已存在，已保留原密码。")
