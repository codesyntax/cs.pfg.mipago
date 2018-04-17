# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
from Acquisition import aq_parent


class PaymentEnd(BrowserView):

    def __call__(self):
        parent = aq_parent(self.context)
        return self.request.response.redirect(self.context.absolute_url() + '/fg_result_view')

