# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    account_represented_company_ids = fields.One2many('res.company', 'account_representative_id')
    fax = fields.Char(string='Fax')
    hide_peppol_fields = fields.Char(string='Fax')
    is_coa_installed = fields.Boolean(string='coa')
    supplier_invoice_count = fields.Integer(string="Supplier Invoice Count", compute="_compute_supplier_invoice_count")

    def _compute_supplier_invoice_count(self):
        for partner in self:
            partner.supplier_invoice_count = self.env['account.move'].search_count([
                ('partner_id', '=', partner.id),
                ('move_type', '=', 'in_invoice')
            ])

    def open_partner_ledger(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_moves_all_tree")
        action['context'] = {
            'search_default_partner_id': self.id,
            'default_partner_id': self.id,
            'search_default_posted': 1,
            'search_default_trade_payable': 1,
            'search_default_trade_receivable': 1,
        }
        return action
