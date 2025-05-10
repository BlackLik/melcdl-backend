#!/bin/bash

python -m cli.migrate upgrade
pytest --benchmark-enable --benchmark-only
