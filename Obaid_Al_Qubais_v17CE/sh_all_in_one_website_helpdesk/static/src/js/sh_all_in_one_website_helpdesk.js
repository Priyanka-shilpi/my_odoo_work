/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from '@web/core/l10n/translation';
publicWidget.registry.WebsiteHelpdeskForm = publicWidget.Widget.extend({

    selector: '.sh_helpdesk_ticket_process_form',

    events: {
        'change #category': '_onChangeCategory',
        'change #contact_name': '_onChangeContactName',
        'change #email': '_onChangeEmail',
        'change #mobile': '_onChangeMobile',
        'click #submit_ticket': '_onClickSubmitTicket',
        'change #upload': '_onChangeCheckDocument',
    },

    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
    },

    start: async function () {
        const def = await this._super.apply(this, arguments);

        const result = await this.rpc("/subcategory-data", {
            category_id: $("#category").val()
        });
        const parsedResult = JSON.parse(result);

        if (parsedResult && Object.keys(parsedResult).length) {
            console.log("\n\n =------->",parsedResult.length);
            parsedResult.sub_categories.forEach(data => {
                const optionHTML = `<option value="${data.id}">${data.name}</option>`;
                $("#subcategory").append(optionHTML);
            });
        }

        return def;
    },


    _onChangeCategory: async function (ev) {
        const result = await this.rpc("/subcategory-data", {
            category_id: $("#category").val()
        });
        const parsedResult = JSON.parse(result);

        if (parsedResult) {
            // Clear existing options before adding new ones
            $("#subcategory").empty();

            parsedResult.sub_categories.forEach(data => {
                const optionHTML = `<option value="${data.id}">${data.name}</option>`;
                $("#subcategory").append(optionHTML);
            });
        }
    },


    _onChangeContactName: function (ev) {
        if ($('#contact_name').val() != '') {
            $('#error_name').hide();
            $('#error_name').html('');
            $('#error_name').css('margin-top:0px');
        }
    },

    _onChangeEmail: function (ev) {
        if ($('#email').val() != '') {
            $('#error_email').hide();
            $('#error_email').html('');
            $('#error_email').css('margin-top:0px');
        }
    },

    _onChangeMobile: function (ev) {
        if ($('#mobile').val() != '') {
            $('#error_mobile').hide();
            $('#error_mobile').html('');
            $('#error_mobile').css('margin-top:0px');
        }
    },

    _onClickSubmitTicket: function (ev) {
        var recaptcha = $('#g-recaptcha-response').val()
        ev.preventDefault();
        $.ajax({
            url: "/check-validation",
            data: {
                'contact_name': $('#contact_name').val(),
                'email': $('#email').val(),
                'mobile': $('#mobile').val(),
                'recaptcha': recaptcha,
            },
            type: "post",
            cache: false,
            success: function (result) {
                var datas = JSON.parse(result);

                if (datas.name_msg) {
                    $('#error_name').show();
                    $('#error_name').html(datas.name_msg);
                    $('#error_name').css('margin-top:10px');
                    $('#error_email').hide();
                    $('#error_mobile').hide();
                    return false;
                }
                if (datas.email_msg) {
                    $('#error_email').show();
                    $('#error_email').html(datas.email_msg);
                    $('#error_email').css('margin-top:10px');
                    $('#error_name').hide();
                    $('#error_mobile').hide();
                    return false;
                }
                if (datas.mobile_msg) {
                    $('#error_mobile').show();
                    $('#error_mobile').html(datas.mobile_msg);
                    $('#error_mobile').css('margin-top:10px');
                    $('#error_email').hide();
                    $('#error_name').hide();
                    return false;
                }

                if (datas.recaptcha_msg) {
                    $('#error_recaptcha').show();
                    $('#error_recaptcha').html(datas.recaptcha_msg);
                    $('#error_recaptcha').css('margin-top:10px');
                    return false;
                }
                return $("#frm_id").submit();
            },
        });
    },

    _onChangeCheckDocument: function (ev) {
        var input = ev.target;
        if (input.files && input.files[0]) {
            var fileSize = input.files[0].size; // in bytes
            var maxSize = parseInt(input.getAttribute('document_limit')) * 1024; // convert to bytes
    
            if (fileSize > maxSize) {
                // Display an alert with file size information
                var fileSizeInKB = fileSize / 1024; // convert to KB
                var formattedSize = fileSizeInKB.toFixed(2) + ' KB'; // format to two decimal places
                var maxFileSizeInKB = maxSize / 1024; // convert to KB
                var formattedMaxSize = maxFileSizeInKB.toFixed(2) + ' KB'; // format to two decimal places
    
                alert('File size exceeds the limit. Your file size: ' + formattedSize + '. Maximum allowed size: ' + formattedMaxSize);
    
                // Optionally, you can clear the selected file
                input.value = '';
            }
        }
    }
    

})