#!/bin/bash
python -m cli.migrate upgrade
pytest --benchmark-skip -n auto
