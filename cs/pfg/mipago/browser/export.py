from Products.Five.browser import BrowserView
from Acquisition import aq_inner
from zope.annotation.interfaces import IAnnotations
from cs.pfg.mipago.config import ANNOTATION_KEY

from DateTime import DateTime
import tablib


class ExportData(BrowserView):

    def __call__(self):
        context = aq_inner(self.context)
        adapted = IAnnotations(self.context)
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
