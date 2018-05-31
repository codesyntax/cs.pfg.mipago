# -*- coding: utf-8 -*-
"""Definition of the MiPagoAdapter content type
"""
from AccessControl import ClassSecurityInfo
from Acquisition import aq_parent
from cs.pfg.mipago import mipagoMessageFactory as _
from cs.pfg.mipago.config import ANNOTATION_KEY
from cs.pfg.mipago.config import MIPAGO_HTML_KEY
from cs.pfg.mipago.config import MIPAGO_PAYMENT_CODE
from cs.pfg.mipago.config import PAYMENT_STATUS_SENT_TO_MIPAGO
from cs.pfg.mipago.config import PROJECTNAME
from cs.pfg.mipago.interfaces import IMiPagoAdapter
from logging import getLogger
from Products.Archetypes import atapi
from Products.Archetypes.atapi import DisplayList
from Products.Archetypes.utils import shasattr
from Products.ATContentTypes.content import base
from Products.ATContentTypes.content import schemata
from Products.CMFCore.permissions import ModifyPortalContent
from Products.PloneFormGen.config import EDIT_ADDRESSING_PERMISSION
from Products.PloneFormGen.config import EDIT_ADVANCED_PERMISSION
from Products.PloneFormGen.config import EDIT_PYTHON_PERMISSION
from Products.PloneFormGen.config import EDIT_TALES_PERMISSION
from Products.PloneFormGen.config import MIME_LIST
from Products.PloneFormGen.config import FORM_ERROR_MARKER
from Products.PloneFormGen.content.actionAdapter import FormActionAdapter
from Products.PloneFormGen.content.actionAdapter import FormAdapterSchema
from Products.PloneFormGen.content.formMailerAdapter import formMailerAdapterSchema
from Products.PloneFormGen.content.formMailerAdapter import FormMailerAdapter
from Products.PythonField import PythonField
from Products.PythonScripts.PythonScript import PythonScript
from Products.TALESField import TALESString
from Products.TemplateFields import ZPTField
from pymipago import make_payment_request
from zope.annotation.interfaces import IAnnotations
from zope.interface import implements

import datetime

log = getLogger(__name__)


default_script = """
## Python Script
##bind container=container
##bind context=context
##bind subpath=traverse_subpath
##parameters=fields, ploneformgen, request
##title=
##
# Available parameters:
#  fields  = HTTP request form fields as a dict. Example:
#            fields['fieldname1'] has the value the user
#            entered/selected in the form
#
#  request = The current HTTP request.
#            Access fields by request.form["myfieldname"]
#
#  ploneformgen = PloneFormGen object
#
# Return the amount to be payed by the end user as a float number

assert False, "Please complete your script"
"""


MiPagoAdapterSchema = formMailerAdapterSchema.copy() + atapi.Schema((

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
    atapi.DateTimeField(
        'mipago_payment_limit_date',
        required=True,
        storage=atapi.AnnotationStorage(),
        searchable=False,
        widget=atapi.CalendarWidget(
            description='',
            show_hm=False,
            label=_('Enter the limit date to do the payment'),
        )
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

    atapi.StringField(
        'mipago_payment_description_es',
        required=True,
        storage=atapi.AnnotationStorage(),
        searchable=False,
        widget=atapi.StringWidget(
            description='',
            label=_('Concept description in spanish '),
            )
    ),

    atapi.StringField(
        'mipago_payment_description_eu',
        required=True,
        storage=atapi.AnnotationStorage(),
        searchable=False,
        widget=atapi.StringWidget(
            description='',
            label=_('Concept description in basque '),
            )
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
            default=_('All payments will have consecutive numbers, enter here the value of the first.'), # no-qa
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

    atapi.StringField(
        'citizen_surname1',
        schemata='citizendata',
        searchable=0,
        required=0,
        vocabulary='fieldsDisplayList',
        widget=atapi.SelectionWidget(
            label=_(u'Citizen surname1 field'),
            description=_(u"Select which field of the form has the citizen's 1st surname"),
            ),
        ),

    atapi.StringField(
        'citizen_surname2',
        schemata='citizendata',
        searchable=0,
        required=0,
        vocabulary='fieldsDisplayList',
        widget=atapi.SelectionWidget(
            label=_(u'Citizen surname2 field'),
            description=_(u"Select which field of the form has the citizen's 2nd surname"),
            ),
        ),

    atapi.StringField(
        'citizen_name',
        schemata='citizendata',
        searchable=0,
        required=0,
        vocabulary='fieldsDisplayList',
        widget=atapi.SelectionWidget(
            label=_(u'Citizen name field'),
            description=_(u"Select which field of the form has the citizen's name"),
            ),
        ),

    atapi.StringField(
        'citizen_nif',
        schemata='citizendata',
        searchable=0,
        required=0,
        vocabulary='fieldsDisplayList',
        widget=atapi.SelectionWidget(
            label=_(u'Citizen nif field'),
            description=_(u"Select which field of the form has the citizen's nif"),
            ),
        ),

    atapi.StringField(
        'citizen_address',
        schemata='citizendata',
        searchable=0,
        required=0,
        vocabulary='fieldsDisplayList',
        widget=atapi.SelectionWidget(
            label=_(u'Citizen address field'),
            description=_(u"Select which field of the form has the citizen's address"),
            ),
        ),

    atapi.StringField(
        'citizen_city',
        schemata='citizendata',
        searchable=0,
        required=0,
        vocabulary='fieldsDisplayList',
        widget=atapi.SelectionWidget(
            label=_(u'Citizen city field'),
            description=_(u"Select which field of the form has the citizen's city"),
            ),
        ),


    atapi.StringField(
        'citizen_postal_code',
        schemata='citizendata',
        searchable=0,
        required=0,
        vocabulary='fieldsDisplayList',
        widget=atapi.SelectionWidget(
            label=_(u'Citizen postal code field'),
            description=_(u"Select which field of the form has the citizen's postal code"),
            ),
        ),

    atapi.StringField(
        'citizen_territory',
        schemata='citizendata',
        searchable=0,
        required=0,
        vocabulary='fieldsDisplayList',
        widget=atapi.SelectionWidget(
            label=_(u'Citizen territory field'),
            description=_(u"Select which field of the form has the citizen's territory"),
            ),
        ),

    atapi.StringField(
        'citizen_country',
        schemata='citizendata',
        searchable=0,
        required=0,
        vocabulary='fieldsDisplayList',
        widget=atapi.SelectionWidget(
            label=_(u'Citizen country field'),
            description=_(u"Select which field of the form has the citizen's country"),
            ),
        ),

    atapi.StringField(
        'citizen_phone',
        schemata='citizendata',
        searchable=0,
        required=0,
        vocabulary='fieldsDisplayList',
        widget=atapi.SelectionWidget(
            label=_(u'Citizen phone field'),
            description=_(u"Select which field of the form has the citizen's phone"),
            ),
        ),

    atapi.StringField(
        'citizen_email',
        schemata='citizendata',
        searchable=0,
        required=0,
        vocabulary='fieldsDisplayList',
        widget=atapi.SelectionWidget(
            label=_(u'Citizen email field'),
            description=_(u"Select which field of the form has the citizen's email"),
            ),
        ),

    atapi.TextField(
        'message_top_description_spanish',
        schemata='messages',
        searchable=0,
        required=0,
        allowable_content_types='text/plain',
        default_output_type='text/plain',
        default_content_type='text/plain',
        widget=atapi.TextAreaWidget(
            label=_(u'Override the value of the payment title in spanish'),
            description=_(u"Write here the spanish text that will override the default name of the payment coming from the payment service configuration"),
            ),
        ),

    atapi.TextField(
        'message_top_description_basque',
        schemata='messages',
        searchable=0,
        required=0,
        allowable_content_types='text/plain',
        default_output_type='text/plain',
        default_content_type='text/plain',
        widget=atapi.TextAreaWidget(
            label=_(u'Override the value of the payment title in basque'),
            description=_(u"Write here the basque text that will override the default name of the payment coming from the payment service configuration"),
            ),
        ),


    atapi.TextField(
        'message_4_spanish',
        schemata='messages',
        searchable=0,
        required=0,
        allowable_content_types='text/plain',
        default_output_type='text/plain',
        default_content_type='text/plain',
        widget=atapi.TextAreaWidget(
            label=_(u'Override the value of message 4 in spanish'),
            description=_(u"Write here the spanish text that will override the value shown on the header of the PDF file"),
            ),
        ),

    atapi.TextField(
        'message_4_basque',
        schemata='messages',
        searchable=0,
        required=0,
        allowable_content_types='text/plain',
        default_output_type='text/plain',
        default_content_type='text/plain',
        widget=atapi.TextAreaWidget(
            label=_(u'Override the value of message 4 in basque'),
            description=_(u"Write here the basque text that will override the value shown on the header of the PDF file"),
            ),
        ),


    atapi.TextField(
        'message_2_spanish',
        schemata='messages',
        searchable=0,
        required=0,
        allowable_content_types='text/plain',
        default_output_type='text/plain',
        default_content_type='text/plain',
        default='''La tasa objeto de esta liquidación está sujeta a la Ley 13/1998, de 29 de mayo, de tasas y precios públicos de la Adminsitración de la Comunidad Autónoma del Páis Vasco.''',
        widget=atapi.TextAreaWidget(
            label=_(u'Override the value of message 2 in spanish'),
            description=_(u"Write here the spanish text that will override the value shown in the PDF file"),
            ),
        ),

    atapi.TextField(
        'message_2_basque',
        schemata='messages',
        searchable=0,
        required=0,
        allowable_content_types='text/plain',
        default_output_type='text/plain',
        default_content_type='text/plain',
        default='''13/1998 Legeak, maiatzaren 29koa, Euskal Autonomia Erkidegoko Administrazioaren tasa eta prezio publikoei buruzkoa, kitapen honen gaia den tasa arautzen du.''',
        widget=atapi.TextAreaWidget(
            label=_(u'Override the value of message 2 in basque'),
            description=_(u"Write here the basque text that will override the value shown in the PDF file"),
            ),
        ),

    atapi.TextField(
        'message_3_spanish',
        schemata='messages',
        searchable=0,
        required=0,
        allowable_content_types='text/plain',
        default_output_type='text/plain',
        default_content_type='text/plain',
        default='''Contra esta liquidación podrá interponerse, en el plazo de 15 días desde su notificación, un recurso de reposición ante el órgano que dictó la resolución, o, en su defecto o contra su resolución, reclamación económico-administrativa ante el "Tribunal Económico-Administrativo de Esukadi", en el mismo plazo.''',
        widget=atapi.TextAreaWidget(
            label=_(u'Override the value of message 3 in spanish'),
            description=_(u"Write here the spanish text that will override the value shown in the PDF file"),
            ),
        ),

    atapi.TextField(
        'message_3_basque',
        schemata='messages',
        searchable=0,
        required=0,
        allowable_content_types='text/plain',
        default_output_type='text/plain',
        default_content_type='text/plain',
        default='''Kitapenaren kontra berraztertzeko errekurtsoa aurkeztu ahal izango zaio kitapena egin duen organoari, edo, bestela, ebazpenaren kontra Administrazioarekiko diru erreklamazioa jarri ahal izango da Euskadiko Ekonomia Ardularitzako Epaitegian, jakinarazpena jaso eta 15 eguneko epean.''',
        widget=atapi.TextAreaWidget(
            label=_(u'Override the value of message 3 in basque'),
            description=_(u"Write here the basque text that will override the value shown in the PDF file"),
            ),
        ),


    atapi.StringField(
        'image_1_link',
        schemata='messages',
        searchable=0,
        required=0,
        widget=atapi.StringWidget(
            label=_(u'1st image shown in the payment documents'),
            description=_(u"Add the URL of the 1st image shown in the payment documents. You will need to send it to the Payment Service Administrators and get the URL from them."),
            size=50,
            ),
    ),

    atapi.StringField(
        'image_2_link',
        schemata='messages',
        searchable=0,
        required=0,
        widget=atapi.StringWidget(
            label=_(u'2nd image shown in the payment documents'),
            description=_(u"Add the URL of the 2nd image shown in the payment documents. You will need to send it to the Payment Service Administrators and get the URL from them."),
            size=50,
            ),
    ),

    atapi.StringField(
        'pdf_generator_template',
        schemata='messages',
        searchable=0,
        required=0,
        widget=atapi.StringWidget(
            label=_(u'PDF generator template'),
            description=_(u"Add the URL of the XSLT template that renders the PDF file. You will hardly need to change this. Contact the Payment Service Administrators for more information."),
            size=50,
            ),
    ),

    atapi.BooleanField(
        'mipago_use_amountOverride',
        schemata='overrides',
        required=False,
        default=False,
        widget=atapi.BooleanWidget(
            label=_('Check if you need to calculate the amount using a python script'),
        )
    ),

    PythonField(
        'mipago_payment_amountOverride',
        schemata='overrides',
        searchable=0,
        required=0,
        default=default_script,
        write_permission=EDIT_PYTHON_PERMISSION,
        read_permission=ModifyPortalContent,
        isMetadata=True,  # just to hide from base view
        widget=atapi.TextAreaWidget(
            label=_(u'Amount calculation script'),
            rows=20,
            visible={'view': 'invisible', 'edit': 'visible'},
            description=_(u'Write here the script that calculates the amount'),
        ),
    ),

))

# Hide unneeded fields coming from formMailerAdapter
MiPagoAdapterSchema['additional_headers'].widget.visible = {'view': 'invisible', 'edit': 'invisible'}
MiPagoAdapterSchema['bcc_recipients'].widget.visible = {'view': 'invisible', 'edit': 'invisible'}
MiPagoAdapterSchema['bccOverride'].widget.visible = {'view': 'invisible', 'edit': 'invisible'}
MiPagoAdapterSchema['cc_recipients'].widget.visible = {'view': 'invisible', 'edit': 'invisible'}
MiPagoAdapterSchema['ccOverride'].widget.visible = {'view': 'invisible', 'edit': 'invisible'}
MiPagoAdapterSchema['gpg_keyid'].widget.visible = {'view': 'invisible', 'edit': 'invisible'}
MiPagoAdapterSchema['recipient_name'].default = ''
MiPagoAdapterSchema['recipient_name'].widget.visible = {'view': 'invisible', 'edit': 'invisible'}
MiPagoAdapterSchema['recipientOverride'].widget.visible = {'view': 'invisible', 'edit': 'invisible'}
MiPagoAdapterSchema['replyto_field'].widget.visible = {'view': 'invisible', 'edit': 'invisible'}
MiPagoAdapterSchema['senderOverride'].widget.visible = {'view': 'invisible', 'edit': 'invisible'}
MiPagoAdapterSchema['subject_field'].widget.visible = {'view': 'invisible', 'edit': 'invisible'}
MiPagoAdapterSchema['subjectOverride'].widget.visible = {'view': 'invisible', 'edit': 'invisible'}
MiPagoAdapterSchema['xinfo_headers'].widget.visible = {'view': 'invisible', 'edit': 'invisible'}


# Change some labels and descriptions
MiPagoAdapterSchema['to_field'].widget.label = _(u'Extract Recipient From')
MiPagoAdapterSchema['to_field'].widget.description = _(u"""Choose a form field from which you wish to extract input for the To header. If you choose anything other than "None", the user will not receive any email. Be very cautious about allowing unguarded user input for this purpose.""")

# Change schematas
MiPagoAdapterSchema.changeSchemataForField('to_field', 'email')
MiPagoAdapterSchema.changeSchemataForField('recipient_email', 'email')
MiPagoAdapterSchema.changeSchemataForField('msg_subject', 'email')

MiPagoAdapterSchema.changeSchemataForField('body_pre', 'email')
MiPagoAdapterSchema.changeSchemataForField('body_post', 'email')
MiPagoAdapterSchema.changeSchemataForField('body_footer', 'email')
MiPagoAdapterSchema.changeSchemataForField('showAll', 'email')
MiPagoAdapterSchema.changeSchemataForField('showFields', 'email')
MiPagoAdapterSchema.changeSchemataForField('includeEmpties', 'email')
MiPagoAdapterSchema.changeSchemataForField('body_pt', 'email')
MiPagoAdapterSchema.changeSchemataForField('body_type', 'email')


MiPagoAdapterSchema.moveField('to_field', before='recipient_email')
MiPagoAdapterSchema.moveField('execCondition', pos='bottom')

schemata.finalizeATCTSchema(MiPagoAdapterSchema, moveDiscussion=False)


class InvalidReferenceNumber(Exception):
    pass


class MiPagoAdapter(FormMailerAdapter):
    """Adapter for payments with MiPago"""
    implements(IMiPagoAdapter)

    meta_type = "MiPagoAdapter"
    schema = MiPagoAdapterSchema

    # title = atapi.ATFieldProperty('title')
    # description = atapi.ATFieldProperty('description')

    security = ClassSecurityInfo()

    security.declarePrivate('updateScript')
    def updateScript(self, body):
        # Regenerate Python script object

        # Sync set of script source code and
        # creation of Python Script object.

        bodyField = self.schema["mipago_payment_amountOverride"]
        script = PythonScript(self.title_or_id())
        script = script.__of__(self)

        script.ZPythonScript_edit("fields, ploneformgen, request", body)

        PythonField.set(bodyField, self, script)

    security.declarePrivate('setMipago_payment_amountOverride')
    def setMipago_payment_amountOverride(self, body):
        # Make PythonScript construction to take parameters
        self.updateScript(body)

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


        amount = self.get_amount(REQUEST)
        cpr = self.getMipago_cpr_code()
        sender = self.getMipago_sender()
        format = self.getMipago_format()
        suffix = self.getMipago_suffix()
        reference_number = self.get_reference_number()
        language = self.getMipago_screen_language()
        return_url = self.absolute_url() + '/payment_end'
        payment_modes = self.getMipago_payment_modes()
        period_date = self.getMipago_payment_limit_date().asdatetime().date()
        extra = {}

        # Extra messages
        if self.getMessage_2_spanish():
            if 'message2' not in extra:
                extra['message2'] = {}
            extra['message2'].update(
                {'es': self.getMessage_2_spanish()}
            )
        if self.getMessage_2_basque():
            if 'message2' not in extra:
                extra['message2'] = {}

            extra['message2'].update(
                {'eu': self.getMessage_2_spanish()}
            )

        if self.getMessage_3_spanish():
            if 'message3' not in extra:
                extra['message3'] = {}
            extra['message3'].update(
                {'es': self.getMessage_3_spanish()}
            )
        if self.getMessage_3_basque():
            if 'message3' not in extra:
                extra['message3'] = {}

            extra['message3'].update(
                {'eu': self.getMessage_3_spanish()}
            )

        if self.getMessage_4_spanish():
            if 'message4' not in extra:
                extra['message4'] = {}
            extra['message4'].update(
                {'es': self.getMessage_4_spanish()}
            )
        if self.getMessage_4_basque():
            if 'message4' not in extra:
                extra['message4'] = {}

            extra['message4'].update(
                {'eu': self.getMessage_4_spanish()}
            )

        if self.getMessage_top_description_spanish():
            if 'message_payment_title' not in extra:
                extra['message_payment_title'] = {}

            extra['message_payment_title'].update(
                {'es': self.getMessage_top_description_spanish()}
            )

        if self.getMessage_top_description_basque():
            if 'message_payment_title' not in extra:
                extra['message_payment_title'] = {}

            extra['message_payment_title'].update(
                {'eu': self.getMessage_top_description_basque()}
            )

        # Citizen data
        if self.getCitizen_name() != '#NONE#':
            field_name = self.getCitizen_name()
            extra['citizen_name'] = REQUEST.get(field_name)
        if self.getCitizen_surname1() != '#NONE#':
            field_name = self.getCitizen_surname1()
            extra['citizen_surname_1'] = REQUEST.get(field_name)
        if self.getCitizen_surname2() != '#NONE#':
            field_name = self.getCitizen_surname2()
            extra['citizen_surname_2'] = REQUEST.get(field_name)
        if self.getCitizen_nif() != '#NONE#':
            field_name = self.getCitizen_nif()
            extra['citizen_nif'] = REQUEST.get(field_name)
        if self.getCitizen_address() != '#NONE#':
            field_name = self.getCitizen_address()
            extra['citizen_address'] = REQUEST.get(field_name)
        if self.getCitizen_city() != '#NONE#':
            field_name = self.getCitizen_city()
            extra['citizen_city'] = REQUEST.get(field_name)
        if self.getCitizen_postal_code() != '#NONE#':
            field_name = self.getCitizen_postal_code()
            extra['citizen_postal_code'] = REQUEST.get(field_name)
        if self.getCitizen_territory() != '#NONE#':
            field_name = self.getCitizen_territory()
            extra['citizen_territory'] = REQUEST.get(field_name)
        if self.getCitizen_country() != '#NONE#':
            field_name = self.getCitizen_country()
            extra['citizen_country'] = REQUEST.get(field_name)
        if self.getCitizen_phone() != '#NONE#':
            field_name = self.getCitizen_phone()
            extra['citizen_phone'] = REQUEST.get(field_name)
        if self.getCitizen_email() != '#NONE#':
            field_name = self.getCitizen_email()
            extra['citizen_email'] = REQUEST.get(field_name)


        # Payment concept / description
        if self.getMipago_payment_description_es() != '#NONE#':
            if 'mipago_payment_description' not in extra:
                extra['mipago_payment_description'] = {}

            extra['mipago_payment_description'].update(
                {'es': self.getMipago_payment_description_es()}
            )

        if self.getMipago_payment_description_eu() != '#NONE#':
            if 'mipago_payment_description' not in extra:
                extra['mipago_payment_description'] = {}

            extra['mipago_payment_description'].update(
                {'eu': self.getMipago_payment_description_eu()}
            )

        # Logo URLs
        if self.getImage_1_link():
            extra['logo_1_url'] = self.getImage_1_link()

        if self.getImage_2_link():
            extra['logo_2_url'] = self.getImage_2_link()

        # PDF Template
        if self.getPdf_generator_template():
            extra['pdf_xslt_url'] = self.getPdf_generator_template()


        try:
            html, code = make_payment_request(cpr, sender, format, suffix, reference_number, period_date, amount, language, return_url, payment_modes, self.getMipago_use_debug_environment(), extra)
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


    def get_amount(self, REQUEST):
        if self.getMipago_use_amountOverride():
            if REQUEST is not None:
                data = self.sanifyFields(REQUEST.form)
            else:
                data = {}
            amount = self.executeCustomScript(data, aq_parent(self), REQUEST)
        else:
            amount = self.getMipago_payment_amount()

        myamount = str(amount)
        whole, decimals = myamount.split('.')
        return '{}{:0<2}'.format(whole, decimals)

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

    def fieldsDisplayList(self):
        """ returns display list of fields with simple values """

        return self.fgFieldsDisplayList(
            withNone=True,
            noneValue='#NONE#',
            objTypes=(
                'FormSelectionField',
                'FormStringField',
                )
            )

    security.declarePrivate('executeCustomScript')
    def executeCustomScript(self, result, form, req):
        # Execute in-place script

        # @param result Extracted fields from REQUEST.form
        # @param form PloneFormGen object

        field = self.schema["mipago_payment_amountOverride"]
        # Now pass through PythonField/PythonScript abstraction
        # to access bad things (tm)
        # otherwise there are silent failures
        script = atapi.ObjectField.get(field, self)

        log.debug("Executing Custom Script Adapter " + self.title_or_id() + " fields:" + str(result))

        self.checkWarningsAndErrors()

        response = script(result, form, req)
        return response

    security.declarePrivate('checkWarningsAndErrors')
    def checkWarningsAndErrors(self):
        # Raise exception if there has been bad things with the script compiling

        field = self.schema["mipago_payment_amountOverride"]

        script = atapi.ObjectField.get(field, self)

        if len(script.warnings) > 0:
            log.warn("Python script " + self.title_or_id() + " has warning:" + str(script.warnings))

        if len(script.errors) > 0:
            log.error("Python script "  + self.title_or_id() +  " has errors: " + str(script.errors))
            raise ValueError("Python script "  + self.title_or_id() + " has errors: " + str(script.errors))


    security.declarePrivate('sanifyFields')
    def sanifyFields(self, form):
        # Makes request.form fields accessible in a script
        #
        # Avoid Unauthorized exceptions since REQUEST.form is inaccesible

        result = {}
        for field in form:
            result[field] = form[field]
        return result


atapi.registerType(MiPagoAdapter, PROJECTNAME)
