# -*- coding: utf-8 -*-
"""Common configuration constants
"""

PROJECTNAME = 'cs.pfg.mipago'

MIPAGO_HTML_KEY = 'mipago_show_html'
MIPAGO_PAYMENT_CODE = 'mipago_payment_code'

ANNOTATION_KEY = 'cs.pfg.mipago.payments'

PAYMENT_STATUS_SENT_TO_MIPAGO = 1
PAYMENT_STATUS_PAYED = 2
PAYMENT_STATUS_UNPAYED = 3


ADD_PERMISSIONS = {
    # -*- extra stuff goes here -*-
    'MiPagoAdapter': 'cs.pfg.mipago: Add MiPagoAdapter',
}
