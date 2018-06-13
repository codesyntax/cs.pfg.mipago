# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from Acquisition import aq_parent
from cs.pfg.mipago.config import ANNOTATION_KEY
from DateTime import DateTime
from Products.CMFPlone.utils import safe_hasattr
from Products.Five.browser import BrowserView
from StringIO import StringIO
from zope.annotation.interfaces import IAnnotations

import csv
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
        headers = set()
        for payment_code, payment in payments.items():
            item = {}
            item['payment_code'] = payment_code
            item['reference_number'] = payment.get('reference_number')
            item['amount'] = payment.get('amount')
            item['datetime'] = payment.get('datetime')
            item['status'] = payment.get('status')
            for field in payment.get('fields', []):
                item[field.get('id')] = field.get('value')

            values.append(item)
            headers = headers.union(item.keys())

        st = StringIO()
        writer = csv.DictWriter(st, fieldnames=list(headers))
        writer.writeheader()
        writer.writerows(values)

        data = tablib.Dataset(headers=headers)
        data.csv = st.getvalue()


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
