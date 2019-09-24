#!/usr/bin/env python
import os
import sys
sys.path.append(os.path.dirname(__file__))
from noshowfomo import app
if sys.argv[1] == 'debug':
    app.run(debug = True)
else:
    app.run(host="0.0.0.0", port="80")