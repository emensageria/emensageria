#!/bin/bash
clear
set -e

if [[ "$1" == "--install" ]]; then
    echo "Executando instalações via pip..."
    pip install pip-audit --root-user-action=ignore
    pip install django-debug-toolbar --root-user-action=ignore
    pip install flake8 --root-user-action=ignore
    pip install mypy --root-user-action=ignore
    pip install types-beautifulsoup4 --root-user-action=ignore
    pip install lxml-stubs --root-user-action=ignore
    pip install djangorestframework-stubs --root-user-action=ignore
    pip install types-python-dateutil --root-user-action=ignore
    pip install types-xmltodict --root-user-action=ignore
    pip install vulture --root-user-action=ignore
    pip install pylint --root-user-action=ignore
    pip install autopep8 --root-user-action=ignore
    pip install pytest --root-user-action=ignore
    pip install coverage --root-user-action=ignore
    pip install openai --root-user-action=ignore
fi

source venv/bin/activate
flake8 --max-line=100 --select=E,F,W,C --ignore=W503,W504,E731 apps adminlteui_custom config
#mypy --install-types
#mypy apps *.py
coverage run manage.py test
coverage report -m
python -m pip_audit || true
deactivate
