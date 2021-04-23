#!/bin/bash/
elastalert-create-index --config config.yaml
elastalert --config config.yaml --verbose
