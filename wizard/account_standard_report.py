# -*- coding: utf-8 -*-

import calendar

from datetime import datetime, timedelta
from odoo import api, models, fields, _
from odoo.tools import float_is_zero
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


D_LEDGER = {'general': {'name': _('General Ledger'),
                        'group_by': 'account_id',
                        'model': 'account.account',
                        'short': 'code',
                        },
            'partner': {'name': _('Partner Ledger'),
                        'group_by': 'partner_id',
                        'model': 'res.partner',
                        'short': 'name',
                        },
            'journal': {'name': _('Journal Ledger'),
                        'group_by': 'journal_id',
                        'model': 'account.journal',
                        'short': 'code',
                        },
            'open': {'name': _('Open Ledger'),
                     'group_by': 'account_id',
                     'model': 'account.account',
                     'short': 'code',
                     },
            'aged': {'name': _('Aged Balance'),
                     'group_by': 'partner_id',
                     'model': 'res.partner',
                     'short': 'name',
                     },
            }


class AccountStandardLedgerPeriode(models.TransientModel):
    _name = 'account.report.standard.ledger.periode'

    name = fields.Char('Name')
    date_from = fields.Datetime('Date from')
    date_to = fields.Datetime('Date to')


class AccountStandardLedgerLines(models.TransientModel):
    _name = 'account.report.standard.ledger.line'

    report_id = fields.Many2one('account.report.standard.ledger')
    account_id = fields.Many2one('account.account')
    type = fields.Selection([('0_init', 'Initial'), ('1_init_line', 'Init Line'), ('2_line', 'Line'),('3_total', 'Total')], string='Type')
    journal_id = fields.Many2one('account.journal')
    partner_id = fields.Many2one('res.partner')
    move_id = fields.Many2one('account.move')
    date = fields.Date()
    date_maturity = fields.Date()
    debit = fields.Float()
    credit = fields.Float()
    balance = fields.Float()
    progress = fields.Float()
    full_reconcile_id = fields.Many2one('account.full.reconcile')


class AccountStandardLedger(models.TransientModel):
    _name = 'account.report.standard.ledger'
    _description = 'Account Standard Ledger'

    def _get_periode_date(self):
        lang_code = self.env.user.lang or 'en_US'
        date_format = self.env['res.lang']._lang_get(lang_code).date_format

        today_year = fields.datetime.now().year

        last_day = self.env.user.company_id.fiscalyear_last_day or 31
        last_month = self.env.user.company_id.fiscalyear_last_month or 12
        periode_obj = self.env['account.report.standard.ledger.periode']
        periode_obj.search([]).unlink()
        periode_ids = periode_obj
        for year in range(today_year, today_year - 4, -1):
            date_from = datetime(year - 1, last_month, last_day) + timedelta(days=1)
            date_to = datetime(year, last_month, last_day)
            user_periode = "%s - %s" % (date_from.strftime(date_format),
                                        date_to.strftime(date_format),
                                        )
            vals = {
                'name': user_periode,
                'date_from': date_from.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'date_to': date_to.strftime(DEFAULT_SERVER_DATE_FORMAT), }
            periode_ids += periode_obj.create(vals)
        return False

    type_ledger = fields.Selection([('general', 'General Ledger'), ('partner', 'Partner Ledger'), ('journal', 'Journal Ledger'), ('open', 'Open Ledger'), ('aged', 'Aged Balance')], string='Type', default='general', required=True,
                                   help=' * General Ledger : Journal entries group by account\n'
                                   ' * Partner Leger : Journal entries group by partner, with only payable/recevable accounts\n'
                                   ' * Journal Ledger : Journal entries group by journal, without initial balance\n'
                                   ' * Open Ledger : Openning journal at Start date\n')
    summary = fields.Boolean('Trial Balance', default=False,
                             help=' * Check : generate a trial balance.\n'
                             ' * Uncheck : detail report.\n')
    amount_currency = fields.Boolean("With Currency", help="It adds the currency column on report if the currency differs from the company currency.")
    reconciled = fields.Boolean('With Reconciled Entries', default=True,
                                help='Only for entrie with a payable/receivable account.\n'
                                ' * Check this box to see un-reconcillied and reconciled entries with payable.\n'
                                ' * Uncheck to see only un-reconcillied entries. Can be use only with parnter ledger.\n')
    partner_ids = fields.Many2many(comodel_name='res.partner', string='Partners', domain=['|', ('is_company', '=', True), ('parent_id', '=', False)], help='If empty, get all partners')
    account_methode = fields.Selection([('include', 'Include'), ('exclude', 'Exclude')], string="Methode")
    account_in_ex_clude = fields.Many2many(comodel_name='account.account', string='Accounts', help='If empty, get all accounts')
    sum_group_by_top = fields.Boolean('Sum on Top', default=False, help='See the sum of element on top.')
    sum_group_by_bottom = fields.Boolean('Sum on Bottom', default=True, help='See the sum of element on top.')
    init_balance_history = fields.Boolean('Initial balance with history.', default=True,
                                          help=' * Check this box if you need to report all the debit and the credit sum before the Start Date.\n'
                                          ' * Uncheck this box to report only the balance before the Start Date\n')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True, default=lambda self: self.env['account.journal'].search([]),
                                   help='Select journal, for the Open Ledger you need to set all journals.')
    date_from = fields.Date(string='Start Date', help='Use to compute initial balance.')
    date_to = fields.Date(string='End Date', help='Use to compute the entrie matched with futur.')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    periode_date = fields.Many2one('account.report.standard.ledger.periode', 'Periode', default=_get_periode_date, help="Auto complete Start and End date.")
    month_selec = fields.Selection([(1, '01 Junary'), (2, '02 Febuary'), (3, '03 March'), (4, '04 April'), (5, '05 May'), (6, '06 June'),
                                    (7, '07 Jully'), (8, '08 August'), (9, '09 September'), (10, '10 October'), (11, '11 November'), (12, '12 December')],
                                   string='Month')
    result_selection = fields.Selection([('customer', 'Receivable Accounts'),
                                         ('supplier', 'Payable Accounts'),
                                         ('customer_supplier', 'Receivable and Payable Accounts')
                                         ], string="Partner's", required=True, default='customer')
    report_name = fields.Char('Report Name')
    compact_account = fields.Boolean('Compacte account.', default=False)
    reset_exp_acc_start_date = fields.Boolean('Reset expenses/revenue account at start date', default=True)
    lines_ids = fields.One2many('account.report.standard.ledger.line', 'report_id', string='Lines')

    @api.onchange('account_in_ex_clude')
    def on_change_summary(self):
        if self.account_in_ex_clude:
            self.account_methode = 'include'
        else:
            self.account_methode = False

    @api.onchange('type_ledger')
    def on_change_type_ledger(self):
        if self.type_ledger in ('partner', 'journal', 'open', 'aged'):
            self.compact_account = False
        if self.type_ledger == 'aged':
            self.date_from = False
        if self.type_ledger not in ('partner', 'aged',):
            self.reconciled = True
            return {'domain': {'account_in_ex_clude': []}}
        self.account_in_ex_clude = False
        return {'domain': {'account_in_ex_clude': [('internal_type', 'in', ('receivable', 'payable'))]}}

    @api.onchange('periode_date')
    def on_change_periode_date(self):
        if self.periode_date:
            self.date_from = self.periode_date.date_from
            self.date_to = self.periode_date.date_to
            if self.month_selec:
                self.on_change_month_selec()

    @api.onchange('month_selec')
    def on_change_month_selec(self):
        if self.periode_date and self.month_selec:
            date_from = datetime.strptime(self.periode_date.date_from, DEFAULT_SERVER_DATETIME_FORMAT)
            date_from = datetime(date_from.year, self.month_selec, 1)
            date_to = datetime(date_from.year, self.month_selec, calendar.monthrange(date_from.year, self.month_selec)[1])
            self.date_from = date_from.strftime(DEFAULT_SERVER_DATE_FORMAT)
            self.date_to = date_to.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif self.periode_date and not self.month_selec:
            self.on_change_periode_date()

    def print_pdf_report(self):
        self.ensure_one()
        self.compute_data()
        return {
            'name': _("Ledger Lines"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.report.standard.ledger.line',
            'type': 'ir.actions.act_window',
            'domain': "[('report_id','=',%s)]" % (self.id),
            'target': 'current',
        }

        return self.env['report'].with_context(landscape=True).get_action(self, 'account_standard_report.report_account_standard_report', data={'active_id': self.id})

    def print_excel_report(self):
        self.ensure_one()
        return self.env['report'].get_action(self, 'account_standard_report.report_account_standard_excel')

    def pre_compute_form(self):
        if self.type_ledger in ('partner', 'journal', 'open', 'aged'):
            self.compact_account = False
            self.reset_exp_acc_start_date = False
        if self.type_ledger == 'aged':
            self.date_from = False
        if self.type_ledger not in ('partner', 'aged',):
            self.reconciled = True
            self.partner_ids = False

    def compute_data(self):
        self.lines_ids.unlink()

        if self.type_ledger != 'open':
            self._sql_unaffected_earnings()

        self._sql_init_balance()

        self._sql_init_unreconcillied_table()

        if self.type_ledger != 'open':
            self._sql_lines()


    def _sql_unaffected_earnings(self):
        unaffected_earnings_account = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_unaffected_earnings').id)], limit=1)
        company = self.env.user.company_id

        query = """
        INSERT INTO account_report_standard_ledger_line
            (report_id, create_uid, create_date, account_id, type, date, debit, credit, balance)
        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            %s AS account_id,
            '0_init' AS type,
            %s AS date,
            COALESCE(SUM(account_move_line.debit), 0) AS debit,
            COALESCE(SUM(account_move_line.credit), 0) AS credit,
            COALESCE(SUM(account_move_line.balance), 0) AS balance
        FROM
            account_move_line
            LEFT JOIN account_account acc ON (account_move_line.account_id = acc.id)
            LEFT JOIN account_account_type acc_type ON (acc.user_type_id = acc_type.id)
            LEFT JOIN account_move m ON (account_move_line.move_id = m.id)
        WHERE
            m.state IN %s
            AND account_move_line.company_id = %s
            AND account_move_line.date < %s
            AND acc_type.include_initial_balance = 'f'
        """

        params = [
            self.id,
            self.env.uid,
            unaffected_earnings_account.id,
            self.date_from,
            ('posted',) if self.target_move == 'posted' else ('posted', 'draft',),
            company.id,
            self.date_from, ]

        self.env.cr.execute(query, tuple(params))

    def _sql_init_balance(self):
        company = self.env.user.company_id
        # initial balance partner
        query = """
        INSERT INTO account_report_standard_ledger_line
            (report_id, create_uid, create_date, account_id, partner_id, type, date, debit, credit, balance)

        WITH matching_in_futur_before_init (id) AS
        (
        SELECT DISTINCT
            afr.id
        FROM
            account_full_reconcile afr
        INNER JOIN account_move_line aml ON aml.full_reconcile_id=afr.id
        WHERE
            aml.company_id = %s
            AND aml.date >= %s
        )
        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            MIN(account_move_line.account_id) AS account_id,
            MIN(account_move_line.partner_id) AS partner_id,
            '0_init' AS type,
            %s AS date,
            COALESCE(SUM(account_move_line.debit), 0) AS debit,
            COALESCE(SUM(account_move_line.credit), 0) AS credit,
            COALESCE(SUM(account_move_line.balance), 0) AS balance
        FROM
            account_move_line
            LEFT JOIN account_account acc ON (account_move_line.account_id = acc.id)
            LEFT JOIN account_account_type acc_type ON (acc.user_type_id = acc_type.id)
            LEFT JOIN account_move m ON (account_move_line.move_id = m.id)
            LEFT JOIN matching_in_futur_before_init mif ON (account_move_line.full_reconcile_id = mif.id)
       	WHERE
            m.state IN %s
            AND account_move_line.company_id = %s
            AND account_move_line.date < %s
            AND (acc_type.type NOT IN ('payable', 'receivable') OR (account_move_line.full_reconcile_id IS NOT NULL AND NOT account_move_line.full_reconcile_id = mif.id))
        GROUP BY
            account_move_line.partner_id, account_move_line.account_id
        """

        params = [
            # matching_in_futur
            company.id,
            self.date_from,

            # init_account_table
            self.id,
            self.env.uid,
            self.date_from,
            ('posted',) if self.target_move == 'posted' else ('posted', 'draft',),
            company.id,
            self.date_from,]

        self.env.cr.execute(query, tuple(params))

    def _sql_init_unreconcillied_table(self):
        company = self.env.user.company_id
        # init_unreconcillied_table
        query = """INSERT INTO account_report_standard_ledger_line
            (report_id, create_uid, create_date, account_id, type, journal_id, partner_id, move_id,date, date_maturity, debit, credit, balance, progress, full_reconcile_id)

        WITH matching_in_futur_before_init (id) AS
        (
        SELECT DISTINCT
            afr.id
        FROM
            account_full_reconcile afr
        INNER JOIN account_move_line aml ON aml.full_reconcile_id=afr.id
        WHERE
            aml.company_id = %s
            AND aml.date >= %s
        )

        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            account_move_line.account_id,
            '1_init_line' AS type,
            account_move_line.journal_id,
            account_move_line.partner_id,
            account_move_line.move_id,
            account_move_line.date,
            account_move_line.date_maturity,
            account_move_line.debit,
            account_move_line.credit,
            account_move_line.balance,
            NULL as progress,
            account_move_line.full_reconcile_id
        FROM
            account_move_line
            LEFT JOIN account_account acc ON (account_move_line.account_id = acc.id)
            LEFT JOIN account_account_type acc_type ON (acc.user_type_id = acc_type.id)
            LEFT JOIN account_move m ON (account_move_line.move_id = m.id)
            LEFT JOIN matching_in_futur_before_init mif ON (account_move_line.full_reconcile_id = mif.id)
       	WHERE
            m.state IN %s
            AND account_move_line.company_id = %s
            AND account_move_line.date < %s
        	AND acc_type.type IN ('payable', 'receivable') AND (account_move_line.full_reconcile_id IS NULL OR account_move_line.full_reconcile_id = mif.id)
        ORDER BY
            account_move_line.date
        """

        params = [
            # matching_in_futur
            company.id,
            self.date_from,
            # init_unreconcillied_table
            self.id,
            self.env.uid,
            ('posted',) if self.target_move == 'posted' else ('posted', 'draft',),
            company.id,
            self.date_from,
            ]

        self.env.cr.execute(query, tuple(params))

    def _sql_lines(self):
        company = self.env.user.company_id
        # lines_table
        query = """
        INSERT INTO account_report_standard_ledger_line
            (report_id, create_uid, create_date, account_id, type, journal_id, partner_id, move_id,date, date_maturity, debit, credit, balance, progress, full_reconcile_id)
        SELECT
            %s AS report_id,
            %s AS create_uid,
            NOW() AS create_date,
            account_move_line.account_id,
            '2_line' AS type,
            account_move_line.journal_id,
            account_move_line.partner_id,
            account_move_line.move_id,
            account_move_line.date,
            account_move_line.date_maturity,
            account_move_line.debit,
            account_move_line.credit,
            account_move_line.balance,
            NULL as progress,
            account_move_line.full_reconcile_id
        FROM
            account_move_line
            LEFT JOIN account_journal j ON (account_move_line.journal_id = j.id)
            LEFT JOIN account_account acc ON (account_move_line.account_id = acc.id)
            LEFT JOIN account_account_type acc_type ON (acc.user_type_id = acc_type.id)
            LEFT JOIN account_move m ON (account_move_line.move_id = m.id)
        WHERE
            m.state IN %s
            AND account_move_line.company_id = %s
            AND account_move_line.date >= %s
            AND account_move_line.date <= %s
        ORDER BY
            account_move_line.date
        """

        params = [
            # lines_table
            self.id,
            self.env.uid,
            ('posted',) if self.target_move == 'posted' else ('posted', 'draft',),
            company.id,
            self.date_from,
            self.date_to,
        ]

        self.env.cr.execute(query, tuple(params))

    def _search_account(self):
        type_ledger = self.type_ledger
        domain = [('deprecated', '=', False), ]
        if type_ledger in ('partner', 'aged',):
            result_selection = self.result_selection
            if result_selection == 'supplier':
                acc_type = ['payable']
            elif result_selection == 'customer':
                acc_type = ['receivable']
            else:
                acc_type = ['payable', 'receivable']
            domain.append(('internal_type', 'in', acc_type))

        account_in_ex_clude = self.account_in_ex_clude.ids
        acc_methode = self.account_methode
        if account_in_ex_clude:
            if acc_methode == 'include':
                domain.append(('id', 'in', account_in_ex_clude))
            elif acc_methode == 'exclude':
                domain.append(('id', 'not in', account_in_ex_clude))
        return self.env['account.account'].search(domain)

    def _get_name_report(self):
        report_name = D_LEDGER[self.type_ledger]['name']
        if self.summary:
            report_name += _(' Balance')
        self.report_name = report_name
