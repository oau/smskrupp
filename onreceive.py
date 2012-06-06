#!/usr/bin/env python
#-*- coding: utf-8 -*-
import core

doer = None
try:
    sender = core.Sender()
    doer = core.Doer(sender)
    doer.run()
finally:
    if doer:
        doer.cleanup()
