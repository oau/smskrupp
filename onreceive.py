#!/usr/bin/env python
#-*- coding: utf-8 -*-
import core

doer = None
try:
    doer = core.Doer()
    doer.run()
finally:
    if doer:
        doer.cleanup()
