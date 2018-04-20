# -*- coding: utf-8 -*-
"""Definition of the MiPagoAdapter content type
"""

from Acquisition import aq_parent
from cs.pfg.mipago import mipagoMessageFactory as _
from cs.pfg.mipago.config import ANNOTATION_KEY
from cs.pfg.mipago.config import MIPAGO_HTML_KEY
from cs.pfg.mipago.config import MIPAGO_PAYMENT_CODE
from cs.pfg.mipago.config import PAYMENT_STATUS_SENT_TO_MIPAGO
from cs.pfg.mipago.config import PROJECTNAME
from cs.pfg.mipago.interfaces import IMiPagoAdapter
from Products.Archetypes import atapi
from Products.Archetypes.atapi import DisplayList
from Products.Archetypes.utils import shasattr
from Products.ATContentTypes.content import base
from Products.ATContentTypes.content import schemata
from Products.CMFCore.permissions import ModifyPortalContent
from Products.PloneFormGen.config import EDIT_TALES_PERMISSION
from Products.PloneFormGen.config import FORM_ERROR_MARKER
from Products.PloneFormGen.content.actionAdapter import FormActionAdapter
from Products.PloneFormGen.content.actionAdapter import FormAdapterSchema
from Products.TALESField import TALESString
from pymipago import make_payment_request
from zope.annotation.interfaces import IAnnotations
from zope.interface import implements
from logging import getLogger

import datetime

log = getLogger(__name__)


MiPagoAdapterSchema = FormAdapterSchema.copy() + atapi.Schema((

    # -*- Your Archetypes field definitions here ... -*-
    atapi.StringField(
        'mipago_cpr_code',
        vocabulary=DisplayList([
            ('9050299', _(u'9050299: Notebook 60, modality 1')),
            ('9052180', _(u'9052180: Notebook 60, modality 2')),
            ('9050794', _(u'9050794: Notebook 57')),
        ]),
        required=True,
        storage=atapi.AnnotationStorage(),
        searchable=False,
        widget=atapi.SelectionWidget(
            description='',
            label=_('Enter the CPR code of this payment'),
            size=7)
    ),
    atapi.StringField(
        'mipago_format',
        vocabulary=DisplayList([
            ('502', _(u'502: Notebook 60, modality 1, short format')),
            ('521', _(u'521: Notebook 60, modality 2, short format')),
            ('522', _(u'522: Notebook 60, modality 2, long format')),
            ('507', _(u'507: Notebook 57, short format')),
        ]),
        required=True,
        storage=atapi.AnnotationStorage(),
        searchable=False,
        widget=atapi.SelectionWidget(
            description='',
            label=_('Enter the format code of this payment'),
            size=3)
    ),
    atapi.StringField(
        'mipago_sender',
        required=True,
        storage=atapi.AnnotationStorage(),
        searchable=False,
        widget=atapi.StringWidget(
            description='',
            label=_('Enter the sender code'),
            size=6)
    ),

    atapi.StringField(
        'mipago_suffix',
        required=True,
        storage=atapi.AnnotationStorage(),
        searchable=False,
        widget=atapi.StringWidget(
            description='',
            label=_('Enter the suffix of this payment'),
            size=3)
    ),
    atapi.IntegerField(
        'mipago_payment_limit_date',
        required=True,
        storage=atapi.AnnotationStorage(),
        searchable=False,
        widget=atapi.IntegerWidget(
            description='',
            label=_('Enter the number of the days that the user has to pay counting from the day he fills the form'),
            size=3)
    ),
    atapi.StringField(
        'mipago_screen_language',
        required=True,
        storage=atapi.AnnotationStorage(),
        searchable=False,
        vocabulary=DisplayList([
            ('eu', 'Euskara'),
            ('es', 'Español'),
            ('en', 'English'),
        ]),
        widget=atapi.SelectionWidget(
            description='',
            label=_('Select the language of the screens'),
            format='radio',
            size=40)
    ),
    atapi.LinesField(
        'mipago_payment_modes',
        required=True,
        storage=atapi.AnnotationStorage(),
        searchable=False,
        vocabulary=DisplayList([
            ('01', _('Offline payment')),
            ('02', _('Online payment')),
        ]),
        widget=atapi.MultiSelectionWidget(
            description='',
            label=_('Select the available payment modes'),
            format='checkbox',
            size=40)
    ),
    atapi.FloatField(
        'mipago_payment_amount',
        required=True,
        storage=atapi.AnnotationStorage(),
        searchable=False,
        widget=atapi.DecimalWidget(
            description='',
            label=_('Enter the amount to be paid'),)
    ),
    atapi.IntegerField(
        'mipago_reference_number_start',
        required=True,
        storage=atapi.AnnotationStorage(),
        searchable=False,
        default=0,
        widget=atapi.IntegerWidget(
            description='',
            label=_('Enter the number of the first reference number'),
            default=_('All payments will have consecutive numbers, enter here the value of the first.'),
            size=10)
    ),
    atapi.BooleanField(
        'mipago_use_debug_environment',
        required=False,
        default=True,
        widget=atapi.BooleanWidget(
            description='',
            label=_('Check if the payments should be made on the TEST platform'),
        )
    ),

    TALESString('mipago_payment_amountOverride',
        schemata='overrides',
        searchable=0,
        required=0,
        validators=('talesvalidator',),
        default='',
        write_permission=EDIT_TALES_PERMISSION,
        read_permission=ModifyPortalContent,
        isMetadata=True,  # just to hide from base view
        widget=atapi.StringWidget(
            label=_(u"Amount Expression"),
            description=_(u"""
                A TALES expression that will be evaluated to override any value
                otherwise entered for amount value.
                Leave empty if unneeded. Your expression should evaluate as a string.
                PLEASE NOTE: errors in the evaluation of this expression will cause
                an error on form display.
            """),
            size=70,
        ),
    ),

))

schemata.finalizeATCTSchema(MiPagoAdapterSchema, moveDiscussion=False)


class InvalidReferenceNumber(Exception):
    pass

class MiPagoAdapter(FormActionAdapter):
    """Adapter for payments with MiPago"""
    implements(IMiPagoAdapter)

    meta_type = "MiPagoAdapter"
    schema = MiPagoAdapterSchema

    # title = atapi.ATFieldProperty('title')
    # description = atapi.ATFieldProperty('description')

    # -*- Your ATSchema to Python Property Bridges Here ... -*-
    def onSuccess(self, fields, REQUEST=None):
        """ Called by form to invoke custom success processing.
            return None (or don't use "return" at all) if processing is
            error-free.

            Return a dictionary like {'field_id':'Error Message'}
            and PFG will stop processing action adapters and
            return back to the form to display your error messages
            for the matching field(s).

            You may also use Products.PloneFormGen.config.FORM_ERROR_MARKER
            as a marker for a message to replace the top-of-the-form error
            message.

            For example, to set a message for the whole form, but not an
            individual field:

            {FORM_ERROR_MARKER:'Yuck! You will need to submit again.'}

            For both a field and form error:

            {FORM_ERROR_MARKER:'Yuck! You will need to submit again.',
             'field_id':'Error Message for field.'}

            Messages may be string types or zope.i18nmessageid objects.
        """
        if self.getMipago_use_debug_environment():
            log.info('Payment requests are being sent to the TEST environment')


        amount = self.get_amount()
        cpr = self.getMipago_cpr_code()
        sender = self.getMipago_sender()
        format = self.getMipago_format()
        suffix = self.getMipago_suffix()
        reference_number = self.get_reference_number()
        payment_period = self.getMipago_payment_limit_date()
        language = self.getMipago_screen_language()
        return_url = self.absolute_url() + '/payment_end'
        payment_modes = self.getMipago_payment_modes()
        period_date = datetime.datetime.now() + datetime.timedelta(days=payment_period)
        try:
            html, code = make_payment_request(cpr, sender, format, suffix, reference_number, period_date, amount, language, return_url, payment_modes, self.getMipago_use_debug_environment())
            if REQUEST is not None:
                request = REQUEST
            else:
                request = self.REQUEST

            normalized_fields = self.normalize_fields(REQUEST, fields)
            self.register_payment(code, reference_number, amount, normalized_fields)

            request.SESSION[MIPAGO_HTML_KEY] = html
            request.SESSION[MIPAGO_PAYMENT_CODE] = code

            return request.response.redirect(self.absolute_url() + '/@@redirect', lock=1)

        except Exception, e:
            log.exception(e)

            return {FORM_ERROR_MARKER: _(u'There was an error processing the payment. Please try again')}


    def get_amount(self):
        if shasattr(self, 'mipago_payment_amountOverride') and self.getRawMipago_payment_amountOverride():
            # subject has a TALES override
            amount = self.getMipago_payment_amountOverride().strip()
        else:
            amount = self.getMipago_payment_amount()

        myamount = str(amount)
        whole, decimals = myamount.split('.')
        return '{}{:0>2}'.format(whole, decimals)

    def get_reference_number(self):
        last_reference_number = self.get_last_reference_number()
        current_reference_number = last_reference_number + 1
        value = '{:0>10}'.format(current_reference_number)
        if len(value) > 10:
            raise InvalidReferenceNumber(_('Reference number is bigger than 10 digits. Please delete old reference numbers'))
        return value

    def get_last_reference_number(self):
        adapted = IAnnotations(self)
        payments = adapted.get(ANNOTATION_KEY, {})
        reference_numbers = []
        for code, data in payments.items():
            reference_numbers.append(data.get('reference_number', 0))

        if reference_numbers:
            reference_numbers.sort()
            return int(reference_numbers[-1])

        return self.getMipago_reference_number_start()


    def register_payment(self, payment_code, reference_number, amount, fields):
        adapted = IAnnotations(self)
        payments = adapted.get(ANNOTATION_KEY, {})
        payments[payment_code] = {
            'reference_number': reference_number,
            'amount': amount,
            'datetime': datetime.datetime.utcnow().isoformat(),
            'status': PAYMENT_STATUS_SENT_TO_MIPAGO,
            'fields': fields
        }

        adapted[ANNOTATION_KEY] = payments

    def normalize_fields(self, REQUEST, fields):
        result = []
        for i, field in enumerate(fields):
            result.append({
                'order': i,
                'id': field.id,
                'title': field.title,
                'value': REQUEST.get(field.id, ''),
            })
        return result

atapi.registerType(MiPagoAdapter, PROJECTNAME)
