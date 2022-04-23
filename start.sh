#!/bin/bash

cd /home/zileni/opAmbiente 
. venv/bin/activate
export FLASK_APP=opAmbiente
flask run -p 5000 -h=0.0.0.0
