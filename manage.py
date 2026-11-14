#!/usr/bin/env python
"""Django entry point for the WhoFix web app (app/). Run from the project root:
    python manage.py migrate
    python manage.py runserver
"""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
