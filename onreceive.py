#!/usr/bin/env python
#-*- coding: utf-8 -*-
import core

worker = None
try:
    worker = core.Worker()
    worker.run()
finally:
    if worker:
        worker.cleanup()
