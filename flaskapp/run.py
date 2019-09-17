#!/usr/bin/env python
import os
import sys
sys.path.append(os.path.dirname(__file__))
from flaskexample import app
app.run(debug = True)