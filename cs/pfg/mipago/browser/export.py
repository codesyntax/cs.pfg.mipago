# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from Acquisition import aq_parent
from cs.pfg.mipago.config import ANNOTATION_KEY
from DateTime import DateTime
from Products.CMFPlone.utils import safe_hasattr
from Products.Five.browser import BrowserView
from zope.annotation.interfaces import IAnnotations

import tablib


class ExportData(BrowserView):

    def get_annotation_context(self):
        parent = aq_parent(self.context)
        if safe_hasattr(parent, 'isTranslation') and \
               parent.isTranslation() and not parent.isCanonical():
            # look in the canonical version to see if there is
            # a matching (by id) save-data adapter.
            # If so, call its onSuccess method
            cf = parent.getCanonical()
            target = cf.get(self.context.getId())
            if target is not None and target.meta_type == 'MiPagoAdapter':
                return target

        return self.context

    def __call__(self):
        context = aq_inner(self.context)
        annotation_context = self.get_annotation_context()
        adapted = IAnnotations(annotation_context)
        payments = adapted.get(ANNOTATION_KEY, {})
        headers = ['payment_code', 'reference_number', 'amount', 'datetime', 'status'] # no-qa
        values = []
        for payment_code, payment in payments.items():
            items = []
            items.append(payment_code)
            items.append(payment.get('reference_number'))
            items.append(payment.get('amount'))
            items.append(payment.get('datetime'))
            items.append(payment.get('status'))
            for field in payment.get('fields', []):
                if field.get('id') not in headers:
                    headers.append(field.get('id'))
                items.append(field.get('value'))

            values.append(items)

        data = tablib.Dataset(*values, headers=headers)
        data.append(items)

        dt = DateTime()
        filename = dt.strftime('%Y-%m-%d-%h-%m-%s-{}.xls'.format(context.getId())) # no-qa
        self.request.response.setHeader(
            'Content-Disposition',
            'inline; filename={0}'.format(filename)
        )

        self.request.response.setHeader(
            'Content-Type',
            'application/vnd.ms-excel'
        )
        return data.export('xls')
