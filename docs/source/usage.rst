====================
Installation & Usage
====================

Pre Configuration
-----------------

To use you payment adapter, you need to contact Basque Government's
Payment Service to get the proper connection codes. Once you get your institution
code and have enabled one or more payment modes and suffixes you can use it.


Installation
------------

To install cs.pfg.mipago, you need to add it to the egg list of your
buildout file, as follows::

    [buildout]
    ...
    eggs =
       ...
       cs.pfg.mipago

And then run your buildout::

    $ buildout -vv

During the install process it will download the required dependencies.


Install the addon
-----------------

Restart your Plone instance, go to the addons control panel and install
this addon.

From now on you will be able to add a "MiPago Adapter" to your PloneFormGen forms.

Usage
-----

1. Create a PloneFormGen based form.

2. Add a MiPago adapter and fill the form with the codes provided by the Payment Service.

.. note:: For the moment only the CPR code 9052180 with payment format 521 works. cs.pfg.mipago depends on pymipago_ and this library only supports those payment modes.

3. You can configure not only the basic data to make a payment, but also you can dynamically override the way to calculate the amount to be payed using a Python Script. You can also override some default messages shown in the payment documents and the logos shown there. You can also configure to send an email after the payment is completed. All this configuration can be made from the edit tabs of the payment adapter.

4. Edit your thank-you page, and configure **not to show any field information**. Add a generic text.

.. note:: We can not show the user entered information because this payment adapter redirects the user to a website where he needs to complete the payment and the user is then redirected back to the form. Due to those redirects, Plone loses the reference of the form fields filled by the user.

5. Ask the Payment Service Admins to add http://your-server.com/your-form-url/payment_confirmation
   as the confirmation URL for the payments of the suffix configured in this form. This way, the form will
   receive all the confirmation messages and will be able to track the payments.

Manage payments
---------------

The payment adapter has an option to see the informtion of the payments. Just go
to the `Manage Payments` tab.


.. _pymipago: https://pypi.org/project/pymipago/
