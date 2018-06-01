# -*- coding: utf-8 -*-
from copy import deepcopy
from cs.pfg.mipago import mipagoMessageFactory as _
from cs.pfg.mipago.config import ANNOTATION_KEY
from cs.pfg.mipago.config import PAYMENT_STATUS_ERROR_IN_MIPAGO
from cs.pfg.mipago.config import PAYMENT_STATUS_PAYED
from cs.pfg.mipago.config import PAYMENT_STATUS_SENT_TO_MIPAGO
from cs.pfg.mipago.config import PAYMENT_STATUS_UNPAYED
from cs.pfg.mipago.config import PAYMENT_STATUS_USER_IN_MIPAGO
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from zope.annotation.interfaces import IAnnotations
from zope.i18n import translate

import datetime
import json
import pytz


class ManagePayments(BrowserView):

    def get_payments(self):
        adapted = IAnnotations(self.context)
        payments = adapted.get(ANNOTATION_KEY, {})
        results = []
        for payment_code, data in payments.items():
            new_data = deepcopy(data)
            new_data.update({'payment_code': payment_code})
            new_data['status'] = self.translate_status(data.get('status', ''))
            new_data['datetime'] = self.localize_datetime(data.get('datetime', ''))
            new_data['amount'] = self.translate_amount(data.get('amount', ''))
            new_data['fields'] = self.translate_fields(data.get('fields', []))
            results.append(new_data)

        results.sort(key=lambda x: x.get('reference_number'))
        return results

    def translate_amount(self, value):
        return u'{}.{} €'.format(value[:-2], value[-2:])

    def translate_status(self, value):
        if value == PAYMENT_STATUS_SENT_TO_MIPAGO:
            return translate(_(u'User redirected to MiPago'))
        elif value == PAYMENT_STATUS_PAYED:
            return translate(_(u'Payment completed successfuly'))
        elif value == PAYMENT_STATUS_UNPAYED:
            return translate(_(u'Payment NOT completed'))
        elif value == PAYMENT_STATUS_USER_IN_MIPAGO:
            return translate(_(u'User reached Mi Pago'))
        elif value == PAYMENT_STATUS_ERROR_IN_MIPAGO:
            return translate(_(u'There was an error during the payment in Mi Pago'))



        return translate(_(u'Unkown status'))

    def localize_datetime(self, value):
        # datetime value is stored in UTC without timezone information
        # so we need to add the UTC timezone and then convert to the
        # appropriate timezone
        try:
            utc = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
            dt_utc = pytz.timezone('UTC').localize(utc)
            value = dt_utc.astimezone(pytz.timezone('Europe/Madrid'))
            return value.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return ''

    def translate_fields(self, value):
        data = json.dumps(value, indent=True)
        return data


class DeletePayments(BrowserView):

    def __call__(self):
        messages = IStatusMessage(self.request)
        adapted = IAnnotations(self.context)
        payments = adapted.get(ANNOTATION_KEY, {})

        if self.request.get('pcodes', []) is not None:
            pcodes = self.request.get('pcodes')
            for pcode in pcodes:
                if pcode in payments:
                    del payments[pcode]
            adapted[ANNOTATION_KEY] = payments
            messages.add(_(u'Payments were deleted'), type=u"info")
        else:
            messages.add(_(u'Nothing was deleted'), type=u"error")

        return self.request.response.redirect(self.context.absolute_url() + '/manage_payments')
