#!/usr/bin/env python
#-*- coding: utf-8 -*-
import core

'''
def _parse_input(self):
    if 'DECODED_PARTS' in os.environ:
        numparts = int(os.environ['DECODED_PARTS'])
        self._log("DECODED_PARTS: "+os.environ['DECODED_PARTS'])
    else:
        numparts = 0
        self._log('decoded_parts does not exist!')

    if 'SMS_MESSAGES' in os.environ:
        nummessages = int(os.environ['SMS_MESSAGES'])
        self._log("SMS_MESSAGES: "+os.environ['SMS_MESSAGES'])
    else:
        nummessages = 0
        self._log('sms_messages does not exist!')

    if nummessages == 1:
        self._log('single part message')
        text = os.environ['SMS_1_TEXT']
        #text = u"tåst"
        self._log('Number %s sent: "%s"'%(os.environ['SMS_1_NUMBER'],
                                          text))
        return os.environ['SMS_1_NUMBER'], text
    elif numparts > 0:
        self._log('multipart message')
        text = ''
        for i in range(1, numparts + 1):
            varname = 'DECODED_%d_TEXT' % i
            if varname in os.environ:
                text = text + os.environ[varname]
        self._log('Number %s have sent text: %s' %
                (os.environ['SMS_1_NUMBER'], text))
        return os.environ['SMS_1_NUMBER'], text
    else:
        self._log("didn't expect this")
        return None
'''
w = core.Worker()
w.run()
