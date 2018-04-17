# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
from cs.pfg.mipago.config import MIPAGO_HTML_KEY


class RedirectView(BrowserView):

    def __call__(self):
        html = self.request.SESSION.get(MIPAGO_HTML_KEY)
        if html is not None:
            return html
