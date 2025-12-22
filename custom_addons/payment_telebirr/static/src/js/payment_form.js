/** @odoo-module **/

import paymentForm from 'payment.payment_form';

paymentForm.include({
    /**
     * @override
     */
    _prepareInlineForm: function (provider, paymentOptionId, flow) {
        if (provider !== 'telebirr') {
            return this._super(...arguments);
        }
        // Telebirr uses redirect flow, no inline form needed
        return Promise.resolve();
    },

    /**
     * @override
     */
    _processRedirectPayment: function (provider, paymentOptionId, processingValues) {
        if (provider !== 'telebirr') {
            return this._super(...arguments);
        }
        
        // Redirect to Telebirr payment page
        const formData = processingValues;
        if (formData.api_url) {
            window.location.href = formData.api_url;
        }
    },
});
