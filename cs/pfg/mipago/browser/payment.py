# -*- coding: utf-8 -*-
from Acquisition import aq_parent
from cs.pfg.mipago.config import ANNOTATION_KEY
from cs.pfg.mipago.config import MIPAGO_HTML_KEY
from cs.pfg.mipago.config import MIPAGO_PAYMENT_CODE
from Products.Five.browser import BrowserView
from zope.annotation import IAnnotations


class PaymentEnd(BrowserView):

    def get_payment_data(self):
        adapted = IAnnotations(self.context)
        payment_code = self.request.SESSION.get(MIPAGO_PAYMENT_CODE, None)
        if payment_code is not None:
            payments = adapted.get(ANNOTATION_KEY, {})
            return payments.get(payment_code, None)

        return None

