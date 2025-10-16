from odoo import models, fields, api
import os
from odoo.exceptions import ValidationError

class biometricattendance(models.Model):
    _name = "biometric.attendance"

    file = fields.Binary("Upload Biometric Attendance File", required=True)
    filename = fields.Char("File Name")

    def _check_file_extension(self):
        if self.file:
            file_data = self.file
            file_extension = os.path.splitext(filename)[1].lower()
            if file_extension not in ['.xls', '.xlsx']:
                raise ValidationError("The file must be an Excel file (.xls or .xlsx)")



    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        return res

    def upload_file(self):
        return {'type': 'ir.actions.act_window_close'}

    def biometric_attendance(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Upload Biometric Attendance',
            'res_model': 'biometric.attendance',
            'view_mode': 'form',
            'view_id': self.env.ref('SchoolManagementSystem.view_biometric_attendance_popup_form').id,
            'target': 'new',
        }