from odoo import api, fields, models
from datetime import date, timedelta
import logging

_logger = logging.getLogger(__name__)


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    license_expiry_date = fields.Date(string="Licence Expiry Date")
    insurance_expiry_date = fields.Date(string="Insurance Expiry Date")
    insurance_number = fields.Char(string="Insurance Number")
    ownership_type_id = fields.Many2one('ownership.type', string="Select Ownership Type")
    registration_certificate_expiry = fields.Date(string="Registration Certificate Expiry")
    third_party_certificate_expiry = fields.Date(string="Third Party Certificate Expiry")
    zone_ii_certificate_expiry = fields.Date(string="Zone II Certificate Expiry")
    spark_arrestor_expiry = fields.Date(string="Spark Arrestor Certificate Expiry")
    chalwyn_valve_expiry = fields.Date(string="Chalwyn Valve Certificate Expiry")
    insurance_certificate_file = fields.Binary(string="Upload Insurance Certificate")
    insurance_certificate_filename = fields.Char(string="Insurance File Name")
    cicpa_certificate_file = fields.Binary(string="Upload CICPA Certificate")
    registration_certificate_file = fields.Binary(string="Upload Registration Certificate")
    third_party_certificate_file = fields.Binary(string="Upload Third Party Certificate")
    zone_ii_certificate_file = fields.Binary(string="Upload ZONE II Certificate")
    spark_arrestor_certificate_file = fields.Binary(string="Upload Spark Arrestor Certificate")
    chalwyn_valve_certificate_file = fields.Binary(string="Upload Chalwyn Valve Certificate")
    ivms_certificate_file = fields.Binary(string="Upload IVMS Certificate (No Expiry)")
    registration_certificate_start = fields.Date(string="Registration Certificate Start Date")


    @api.model
    def _check_expiry_alerts(self):
        manager_user = self.manager_id.id
        alert_email = manager_user.partner_id.email if manager_user and manager_user.partner_id and manager_user.partner_id.email else None
        from_email = (
                self.env.user.company_id.email or
                self.env.user.email
        )

        upcoming_date = date.today() + timedelta(days=7)
        vehicles = self.search([])

        expiry_fields = {
            'license_expiry_date': "Vehicle License",
            'insurance_expiry_date': "Vehicle Insurance",
            'registration_certificate_expiry': "Registration Certificate",
            'third_party_certificate_expiry': "Third Party Certificate",
            'zone_ii_certificate_expiry': "Zone II Certificate",
            'spark_arrestor_expiry': "Spark Arrestor Certificate",
            'chalwyn_valve_expiry': "Chalwyn Valve Certificate",
        }

        for vehicle in vehicles:
            for field_name, label in expiry_fields.items():
                expiry_date = getattr(vehicle, field_name)
                if expiry_date and expiry_date <= upcoming_date:
                    # Compose message
                    alert_text = f"{label} will expire on {expiry_date.strftime('%d-%m-%Y')}. Please take necessary action."
                    subject = f"Fleet Alert: {label} Expiry for {vehicle.display_name}"

                    # Log in chatter
                    vehicle.message_post(
                        body=alert_text,
                        subject=subject,
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment',
                    )

                    # Compose email body
                    email_body = f"""
                            <div style="font-family: Arial, sans-serif; color: #333;">
                                <h2 style="color: #d9534f;">Expiry Notification</h2>
                                <p>Dear User,</p>
                                <p>The following alert is scheduled for vehicle: <strong>{vehicle.display_name}</strong></p>
                                <ul><li>{alert_text}</li></ul>
                                <br/>
                                <p style="font-size: 12px; color: #999;">This is an automated notification from your Fleet Management System.</p>
                            </div>
                        """

                    try:
                        mail = self.env['mail.mail'].sudo().create({
                            'subject': subject,
                            'body_html': email_body,
                            'email_to': alert_email,
                            'email_from': from_email,
                            'auto_delete': True,
                        })
                        _logger.info(
                            f"[FLEET ALERT] Mail created (ID={mail.id}) for {vehicle.display_name}, sending to {alert_email}")
                        mail.send()
                    except Exception as e:
                        _logger.error(f"[FLEET ALERT] Failed to send email for {vehicle.name}: {str(e)}")
                        vehicle.message_post(
                            body=f"⚠ <b>Email alert failed:</b> {str(e)}",
                            message_type='comment',
                            subtype_xmlid='mail.mt_comment',
                        )