# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class AccountPartnerLedgerPeriode(models.TransientModel):
    _name = 'account.report.partner.ledger.periode'

    name = fields.Char('Name')
    date_from = fields.Datetime('Date from')
    date_to = fields.Datetime('Date to')


class AccountStandardLedger(models.TransientModel):
    _inherit = "account.common.partner.report"
    _name = "account.report.standard.ledger"
    _description = "Account Standard Ledger"

    type_ledger = fields.Selection([('general','General Ledger'),('partner','Partner Ledger'),('journal','Journal Ledger')], string='Type', default='general', required=True)
    summary = fields.Boolean('Summary', dafault=False)
    amount_currency = fields.Boolean("With Currency", help="It adds the currency column on report if the currency differs from the company currency.")
    reconciled = fields.Boolean('With Reconciled Entries')
    rem_futur_reconciled = fields.Boolean('With entries matched with other entries dated after End Date.', default=False, help="Reconciled Entries matched with futur is considered like unreconciled. Matching number in futur is replace by *.")
    partner_ids = fields.Many2many(comodel_name='res.partner', string='Partners', domain=['|', ('is_company', '=', True), ('parent_id', '=', False)], help='If empty, get all partners')
    account_exclude_ids = fields.Many2many(comodel_name='account.account', string='Accounts to exclude', help='If empty, get all accounts')
    account_include_ids = fields.Many2many(comodel_name='account.account', string='Accounts to include', help='If empty, get all accounts')
    with_init_balance = fields.Boolean('With Initial Balance at Start Date of reconcilled entries', default=False)
    sum_partner_top = fields.Boolean('Sum partner on Top', default=False)
    sum_partner_bottom = fields.Boolean('Sum partner on Bottom', default=True)

    # on change type
    #account_exclude_ids = fields.Many2many(comodel_name='account.account', string='Accounts to exclude', domain=[('internal_type', 'in', ('receivable', 'payable'))], help='If empty, get all accounts')


    def _get_periode_date(self):
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format

        today_year = fields.datetime.now().year

        last_day = self.env.user.company_id.fiscalyear_last_day or 31
        last_month = self.env.user.company_id.fiscalyear_last_month or 12
        periode_obj = self.env['account.report.partner.ledger.periode']
        periode_obj.search([]).unlink()
        periode_ids = periode_obj
        for year in range(today_year, today_year - 4, -1):
            date_from = datetime(year - 1, last_month, last_day) + timedelta(days=1)
            date_to = datetime(year, last_month, last_day)
            user_periode  = "%s - %s" % (date_from.strftime(date_format),
                                        date_to.strftime(date_format),
                                        )
            vals = {
                    'name':user_periode,
                    'date_from': date_from.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'date_to': date_to.strftime(DEFAULT_SERVER_DATE_FORMAT),}
            periode_ids += periode_obj.create(vals)
        return False

    periode_date = fields.Many2one('account.report.partner.ledger.periode', 'Periode', default=_get_periode_date, help="Auto complete Start and End date.")

    @api.onchange('periode_date')
    def on_change_periode_date(self):
        if self.periode_date:
            self.date_from = self.periode_date.date_from
            self.date_to = self.periode_date.date_to

    @api.onchange('date_to')
    def onchange_date_to(self):
        if self.date_to == False:
            self.rem_futur_reconciled = False
        else:
            self.rem_futur_reconciled = True

    @api.multi
    def pre_print_report(self, data):
        data['form'].update({'partner_ids': self.partner_ids.ids,
                             'account_exclude_ids': self.account_exclude_ids.ids,
                             })
        return super(AccountStandardLedger, self).pre_print_report(data)

    # FIXME : find an other solution to pass context instead of rewrite this code
    def _print_report(self, data):
        if self.date_from == False or self.reconciled == False:
            self.with_init_balance = False
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled,
                             'rem_futur_reconciled': self.rem_futur_reconciled,
                             'with_init_balance': self.with_init_balance,
                             'amount_currency': self.amount_currency,
                             'sum_partner_top': self.sum_partner_top,
                             'sum_partner_bottom': self.sum_partner_bottom,
                             'type_ledger': self.type_ledger,
                             'summary': self.summary,
                             })
        print(data)
        return self.env['report'].with_context(landscape=True).get_action(self, 'account_standard_report.report_account_standard_report', data=data)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
