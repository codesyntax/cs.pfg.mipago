# -*- coding: utf-8 -*-
from Acquisition import aq_parent
from cs.pfg.mipago.config import ANNOTATION_KEY
from cs.pfg.mipago.config import MIPAGO_HTML_KEY
from cs.pfg.mipago.config import MIPAGO_PAYMENT_CODE
from DateTime import DateTime
from Products.CMFPlone.utils import safe_hasattr
from Products.Five.browser import BrowserView
from zope.annotation import IAnnotations
from zope.component import getMultiAdapter


class PaymentEnd(BrowserView):

    def get_payment_data(self):
        adapted = IAnnotations(self.context)
        payment_code = self.request.SESSION.get(MIPAGO_PAYMENT_CODE, None)
        if payment_code is not None:
            payments = adapted.get(ANNOTATION_KEY, {})
            return payments.get(payment_code, None)

        return None

    @property
    def form(self):
        return aq_parent(self.context)

    def get_thanks_page(self):
        if safe_hasattr(self.form, 'thanksPageOverride'):
            s = self.form.getThanksPageOverride()
            if s:
                return None

        s = getattr(self.form, 'thanksPage', None)
        if s:
            return getattr(self.form, s, None)

        return None

    def form_title(self):
        thanks = self.get_thanks_page()
        if thanks is not None:
            return thanks.Title()

        return self.form.Title()

    def get_thanks_prologue(self):
        thanks = self.get_thanks_page()
        if thanks is not None:
            return thanks.getThanksPrologue()
        return ''

    def get_thanks_epilogue(self):
        thanks = self.get_thanks_page()
        if thanks is not None:
            return thanks.getThanksEpilogue()
        return ''

    def datetime(self):
        now = DateTime()
        ploneview = getMultiAdapter((self.context, self.request), name='plone')
        return ploneview.toLocalizedTime(now, long_format=True)
