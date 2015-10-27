#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import time
import random
import re


class BramkaPlay(object):
    loginPage = 'https://logowanie.play.pl/opensso/logowanie'
    smsGate = 'https://bramka.play.pl/'
    smsPage = 'https://bramka.play.pl/composer/public/editableSmsCompose.do'
    ssoPage = 'https://logowanie.play.pl/p4-idp2/SSOrequest.do'
    samlLog = 'https://bramka.play.pl/composer/samlLog?action=sso'
    securityPage = 'https://bramka.play.pl/composer/j_security_check'
    userAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'
    sleepMin, sleepMax = 3, 7

    def __init__(self, login, password):
        self.playLogin = login
        self.playPassword = password
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(), urllib2.HTTPHandler(debuglevel=1))

    def _sendurlrequest(self, url, formdict=None, contenttype=None):
        request = urllib2.Request(url)
        request.add_header('User-Agent', self.userAgent)
        if contenttype is not None:
            request.add_header('Content-Type', contenttype)
        if formdict is not None:
            if isinstance(formdict, dict):
                formdict = urllib.urlencode(formdict)
            request.add_data(formdict)
        time.sleep(random.randint(self.sleepMin, self.sleepMax))
        try:
            return self.opener.open(request).read()
        except IOError, e:
            print 'Error:', e

    def _encode_multipart_formdata(self):
        limit = '---------------------------319662358430573'
        crlf = '\r\n'
        payload = []
        payload.append('--' + limit)
        payload.append('Content-Disposition: form-data; name="SMS_SEND_CONFIRMED.x"')
        payload.append('')
        payload.append('0')
        payload.append('--' + limit)
        payload.append('Content-Disposition: form-data; name="SMS_SEND_CONFIRMED.y"')
        payload.append('')
        payload.append('0')
        payload.append('--' + limit + '--')
        payload.append('')
        body = crlf.join(payload)
        content_type = 'multipart/form-data; boundary=%s' % limit
        return content_type, body

    def sendsms(self, recipient, message):
        self._sendurlrequest(self.loginPage)    # 1st request for cookies

        formparameters = {'IDToken1': self.playLogin,
                          'IDToken2': self.playPassword,
                          'Login.Submit': 'Zaloguj',
                          'goto': '',
                          'gotoOnFail': '',
                          'SunQueryParamsString': '',
                          'encoded': 'false',
                          'gx_charset': 'UTF-8'
                          }

        self._sendurlrequest(self.loginPage, formparameters)    # 2nd request for login

        smsgateresult = self._sendurlrequest(self.smsGate)     # 3rd request for hidden values
        samlrequest = re.search('name="SAMLRequest"\s+value="([+=\w\d\n\r]+)"', smsgateresult)
        samlrequest = samlrequest.group(1)

        target = re.search('name="target"\s+value="([:/.\w]+)"\s+/>', smsgateresult)
        target = target.group(1)

        formparameters = {'SAMLRequest': samlrequest,
                          'target': target}

        ssopageresult = self._sendurlrequest(self.ssoPage, formparameters)      # 4th request for hidden values

        samlresponse = re.search('NAME="SAMLResponse"\s+VALUE="([+=\w\d\n\r]+)"', ssopageresult)
        samlresponse = samlresponse.group(1)

        target = re.search('NAME="target"\s+VALUE="([:/.\w]+)">', ssopageresult)
        target = target.group(1)

        formparameters = {'SAMLResponse': samlresponse,
                          'target': target}

        samllogresult = self._sendurlrequest(self.samlLog, formparameters)      # 5th request for hidden values

        samlresponse = re.search('name="SAMLResponse"\s+value="([+=\w\d\n\r]+)"', samllogresult)
        samlresponse = samlresponse.group(1)

        formparameters = {'SAMLResponse': samlresponse}
        securitypageresult = self._sendurlrequest(self.securityPage, formparameters)     # 6th request for hidden values

        randform = re.search('<input\s+type="hidden"\s+name="randForm"\s+value="(\d+)">', securitypageresult)
        randform = randform.group(1)

        formparameters = {'recipients': recipient,
                          'content_in': message,
                          'czas': '0',
                          'content_out': message,
                          'templateId': '',
                          'sendform': 'on',
                          'composedMsg': '',
                          'randForm': randform,
                          'old_signature': '',
                          'old_content': message,
                          'MessageJustSent': 'false'
                          }

        self._sendurlrequest(self.smsPage, formparameters)      # 7th request with recipient and text message
        ct, body = self._encode_multipart_formdata()
        self._sendurlrequest(self.smsPage, body, ct)  # 8th request for confirmation
        return True
