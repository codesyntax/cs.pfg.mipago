# -*- coding: utf-8 -*-
from cs.pfg.mipago.config import ANNOTATION_KEY
from cs.pfg.mipago.config import PAYMENT_STATUS_PAYED
from cs.pfg.mipago.config import PAYMENT_STATUS_SENT_TO_MIPAGO
from cs.pfg.mipago.config import PAYMENT_STATUS_ERROR_IN_MIPAGO
from cs.pfg.mipago.config import PAYMENT_STATUS_USER_IN_MIPAGO
from plone.protect.interfaces import IDisableCSRFProtection
from Products.Five.browser import BrowserView
from zope.annotation.interfaces import IAnnotations
from zope.interface import alsoProvides

import xml.etree.ElementTree as ET


class PaymentConfirmation(BrowserView):
    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        adapted = IAnnotations(self.context)
        payment_code = self.extract_payment_code()
        payment_status = self.extract_payment_status()
        payments = adapted.get(ANNOTATION_KEY, {})
        payment_data = payments.get(payment_code, {})
        payment_data['status'] = payment_status
        payments[payment_code] = payment_data
        adapted[ANNOTATION_KEY] = payments
        return 1

    def extract_payment_code(self):
        # inspect self.request
        from logging import getLogger
        log = getLogger(__name__)
        log.info('####### extract_payment_code ###########')
        log.info(self.request.items())
        log.info('####### /extract_payment_code ###########')

        param = self.request.get('param1', '')
        return self._parse_param(param)


    def _parse_param(self, param):
        root = ET.fromstring(param)
        id_item = root.find('.//id')
        if id_item is not None:
            return id_item.text

        return ''

    def extract_payment_status(self):
        # inspect self.request
        function = self.request.get('function', '')
        if function == 'onBeginPayment':
            return PAYMENT_STATUS_USER_IN_PAGO
        elif function == 'onPayONLineOK':
            return PAYMENT_STATUS_PAYED
        elif function == 'onPayONLineNOK'
            return PAYMENT_STATUS_ERROR_IN_MIPAGO

        return ''
