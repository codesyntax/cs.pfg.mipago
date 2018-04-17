# -*- coding: utf-8 -*-
from cs.pfg.mipago.config import ANNOTATION_KEY
from cs.pfg.mipago.config import PAYMENT_STATUS_PAYED
from Products.Five.browser import BrowserView
from zope.annotation.interfaces import IAnnotations


class PaymentConfirmation(BrowserView):
    def __call__(self):
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
        return ''

    def extract_payment_status(self):
        # inspect self.request
        return ''
