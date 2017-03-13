# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import time
from odoo import api, models
from odoo.tools import float_is_zero, float_compare
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountExtraReport(models.AbstractModel):
    _name = 'report.account_standard_report.report_account_standard_report'

    def _generate_sql(self, data, accounts, date_to=False):
        date_clause = ''
        if date_to:
            date_clause += ' AND account_move_line.date <= ' + "'" + str(date_to) + "'" + ' '

        # clear used_context date if not it is use during the sql query
        data['form']['used_context']['date_to'] = False
        data['form']['used_context']['date_from'] = False

        query_get_data = self.env['account.move.line'].with_context(data['form'].get('used_context', {}))._query_get()
        reconcile_clause = data['reconcile_clause']
        params = [tuple(data['computed']['move_state']), tuple(accounts.ids)] + query_get_data[2]

        if data['form'].get('partner_ids'):
            partner_ids = data['form'].get('partner_ids')
            if len(partner_ids) == 1:
                partner_ids = "(%s)" % (partner_ids[0])
            else:
                partner_ids = tuple(partner_ids)
            partner_clause = ' AND account_move_line.partner_id IN ' + str(partner_ids) + ' '
        else:
            partner_clause = ' AND account_move_line.partner_id IS NOT NULL '

        query = """
            SELECT
                account_move_line.id,
                account_move_line.date,
                account_move_line.date_maturity,
                j.code,
                acc.code AS a_code,
                acc.name AS a_name,
                account_move_line.ref,
                m.name as move_name,
                account_move_line.name,
                account_move_line.debit,
                account_move_line.credit,
                account_move_line.amount_currency,
                account_move_line.currency_id,
                c.symbol AS currency_code,
                afr.name AS matching_number,
                afr_id.id AS matching_number_id,
                account_move_line.partner_id,
                account_move_line.account_id
            FROM """ + query_get_data[0] + """
                LEFT JOIN account_journal j ON (account_move_line.journal_id = j.id)
                LEFT JOIN account_account acc ON (account_move_line.account_id = acc.id)
                LEFT JOIN res_currency c ON (account_move_line.currency_id=c.id)
                LEFT JOIN account_move m ON (m.id=account_move_line.move_id)
                LEFT JOIN account_full_reconcile afr ON (afr.id=account_move_line.full_reconcile_id)
                LEFT JOIN account_full_reconcile afr_id ON (afr_id.id=account_move_line.full_reconcile_id)
            WHERE
                m.state IN %s
                AND account_move_line.account_id IN %s AND """ + query_get_data[1] + reconcile_clause + partner_clause + date_clause + """
                ORDER BY account_move_line.date"""
        self.env.cr.execute(query, tuple(params))
        return self.env.cr.dictfetchall()

    def _generate_account_dict(self, accounts):
        line_account = {}
        for account in accounts:
            line_account[account.id] = {
                'debit': 0.0,
                'credit': 0.0,
                'balance': 0.0,
                'code': account.code,
                'name': account.name,
                'active': False,
            }
        return line_account

    def _generate_init_balance_lines(self, init_account):
        rounding = self.env.user.company_id.currency_id.rounding or 0.01
        init = []
        for key, value in init_account.items():
            init_debit = value['init_debit']
            init_credit = value['init_credit']
            balance = init_debit - init_credit
            if float_is_zero(balance, rounding):
                balance = 0.0
            if not float_is_zero(init_debit, rounding) or not float_is_zero(init_credit, rounding):
                init.append({'date': 'Initial balance',
                             'date_maturity': '',
                             'debit': init_debit,
                             'credit': init_credit,
                             'code': '',
                             'a_code': value['a_code'],
                             'account_id': key,
                             'displayed_name': '',
                             'progress': balance,
                             'amount_currency': 0.0,
                             'matching_number': '',
                             'type_line': 'init'})
        return init

    def _generate_total(self, sum_debit, sum_credit, balance):
        rounding = self.env.user.company_id.currency_id.rounding or 0.01
        return {'date': 'Total',
                     'date_maturity': '',
                     'debit': sum_debit,
                     'credit': sum_credit,
                     's_debit': False if float_is_zero(sum_debit, rounding) else True,
                     's_credit': False if float_is_zero(sum_credit, rounding) else True,
                     'code': '',
                     'a_code': '',
                     'account_id': '',
                     'displayed_name': '',
                     'progress': balance,
                     'amount_currency': 0.0,
                     'matching_number': '',
                     'type_line': 'total',}

    def _generate_data(self, data, accounts, date_format):
        rounding = self.env.user.company_id.currency_id.rounding or 0.01
        with_init_balance = data['form']['with_init_balance']
        date_from = data['form']['used_context']['date_from']
        date_to = data['form']['used_context']['date_to']
        date_from_dt = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT) if date_from else False
        date_to_dt = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT) if date_to else False
        res = self._generate_sql(data, accounts, date_to=date_to)

        line_partner = {}
        partner_ids = []

        # ordered by partner
        for line in res:
            if line['partner_id'] in line_partner.keys():
                line_partner[line['partner_id']]['lines'].append(line)
            else:
                line_partner.update({line['partner_id']: {'lines': [line],
                                                          'new_lines': [], }})

        line_account = self._generate_account_dict(accounts)

        for partner, value in line_partner.items():
            init_account = {}
            new_list = []
            for r in value['lines']:
                date_move_dt = datetime.strptime(r['date'], DEFAULT_SERVER_DATE_FORMAT)

                move_matching = True if r['matching_number_id'] else False
                move_matching_in_futur = False
                if r['matching_number_id'] in data['matching_in_futur']:
                    move_matching = False
                    move_matching_in_futur = True

                # add in initiale balance only the reconciled entries a
                # and with a date less than date_from
                if with_init_balance and date_from_dt and date_move_dt < date_from_dt and move_matching:
                    if r['account_id'] in init_account.keys():
                        init_account[r['account_id']]['init_debit'] += r['debit']
                        init_account[r['account_id']]['init_credit'] += r['credit']
                    else:
                        init_account[r['account_id']] = {'init_debit': r['debit'],
                                                         'init_credit': r['credit'],
                                                         'a_code': r['a_code'], }

                else:
                    date_move = datetime.strptime(r['date'], DEFAULT_SERVER_DATE_FORMAT)
                    r['date'] = date_move.strftime(date_format)
                    r['date_maturity'] = datetime.strptime(r['date_maturity'], DEFAULT_SERVER_DATE_FORMAT).strftime(date_format)
                    r['displayed_name'] = '-'.join(
                        r[field_name] for field_name in ('move_name', 'ref', 'name')
                        if r[field_name] not in (None, '', '/')
                    )
                    # if move is matching with the future then replace matching number par *
                    if move_matching_in_futur:
                        r['matching_number'] = '*'

                    r['type_line'] = 'normal'
                    if date_from_dt and date_move_dt < date_from_dt:
                        r['type_line'] = 'init'

                    new_list.append(r)

            init_balance_lines = self._generate_init_balance_lines(init_account)

            line_partner[partner]['new_lines'] = init_balance_lines + new_list

        # remove unused partner
        for partner, value in line_partner.items():
            if not value['new_lines']:
                del line_partner[partner]

        # compute sum by partner
        # compute sum by account
        for partner, value in line_partner.items():
            balance = 0.0
            sum_debit = 0.0
            sum_credit = 0.0
            for r in value['new_lines']:
                balance += r['debit'] - r['credit']
                r['progress'] = balance
                if float_is_zero(balance, rounding):
                    r['progress'] = 0.0

                sum_debit += r['debit']
                sum_credit += r['credit']

                r['s_debit'] = False if float_is_zero(r['debit'], rounding) else True
                r['s_credit'] = False if float_is_zero(r['credit'], rounding) else True

                line_account[r['account_id']]['debit'] += r['debit']
                line_account[r['account_id']]['credit'] += r['credit']
                line_account[r['account_id']]['active'] = True
                line_account[r['account_id']]['balance'] += r['debit'] - r['credit']

            balance = sum_debit - sum_credit
            if float_is_zero(balance, rounding):
                balance = 0.0

            if data['form']['sum_partner_bottom']:
                line_partner[partner]['new_lines'].append(self._generate_total(sum_debit, sum_credit, balance))

            line_partner[partner]['debit - credit'] = balance
            line_partner[partner]['debit'] = sum_debit
            line_partner[partner]['credit'] = sum_credit

            partner_ids.append(partner)

        # remove unused account
        for key, value in line_account.items():
            if value['active'] == False:
                del line_account[key]

        return line_partner, line_account, partner_ids

    def _lines(self, data, partner):
        return data['line_partner'][partner.id]['new_lines']

    def _sum_partner(self, data, partner, field):
        if field not in ['debit', 'credit', 'debit - credit']:
            return
        return data['line_partner'][partner.id][field]

    def _account(self, data):
        return data['line_account'].values()

    @api.multi
    def render_html(self, docis, data):
        print("render")
        lang_code = self.env.context.get('lang') or 'en_US'
        date_format  = self.env['res.lang']._lang_get(lang_code).date_format

        data['reconcile_clause'], data['matching_in_futur'] = self._compute_reconcile_clause(data)

        data['form']['name_report'] = self._get_name_report(data)

        data['computed'] = {}
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']

        accounts = self._search_account(data)
        obj_partner = self.env['res.partner']

        data['line_partner'], data['line_account'], partner_ids = self._generate_data(data, accounts, date_format)

        partners = obj_partner.browse(partner_ids)
        partners = sorted(partners, key=lambda x: (x.ref, x.name))

        data['form']['date_from'] = datetime.strptime(data['form']['date_from'], DEFAULT_SERVER_DATE_FORMAT).strftime(date_format) if data['form']['date_from'] else False
        data['form']['date_to'] = datetime.strptime(data['form']['date_to'], DEFAULT_SERVER_DATE_FORMAT).strftime(date_format) if data['form']['date_to'] else False

        docargs = {
            'doc_ids': partner_ids,
            'doc_model': self.env['res.partner'],
            'data': data,
            'docs': partners,
            'time': time,
            'lines': self._lines,
            'sum_partner': self._sum_partner,
            'accounts': self._account,
        }
        return self.env['report'].render('account_standard_report.report_account_standard_report', docargs)

    def _search_account(self, data):

        type_ledger = data['form'].get('type_ledger')
        domain = [('deprecated', '=', False), ]
        if type_ledger == 'partner':
            result_selection = data['form'].get('result_selection', 'customer')
            if result_selection == 'supplier':
                acc_type = ['payable']
            elif result_selection == 'customer':
                acc_type = ['receivable']
            else:
                acc_type = ['payable', 'receivable']
            domain.append(('internal_type', 'in', acc_type))

        account_include_ids = data['form'].get('account_include_ids'))
        account_exclude_ids = data['form'].get('account_exclude_ids'))
        if account_include_ids and not account_exclude_ids:
            domain.append(('id', 'in', account_include_ids))
        elif not account_include_ids and account_exclude_ids:
            domain.append(('id', 'not in', account_exclude_ids))

        return self.env['account.account'].search(domain)

    def _compute_reconcile_clause(self, data):
        reconcile_clause = ""
        list_match_in_futur = []

        if not data['form']['reconciled']:
            reconcile_clause = ' AND account_move_line.reconciled = false '

        # when an entrie a matching number and this matching number is linked with
        # entries witch the date is gretter than date_to, then
        # the entrie is considered like unreconciled.
        if data['form']['rem_futur_reconciled'] and data['form']['date_to']:
            date_to = datetime.strptime(data['form']['date_to'], DEFAULT_SERVER_DATE_FORMAT)
            acc_ful_obj = self.env['account.full.reconcile']

            params = [date_to]
            query = """
            SELECT DISTINCT afr.id
            FROM account_full_reconcile afr
            INNER JOIN account_move_line aml ON aml.full_reconcile_id=afr.id
            AND aml.date > %s
            """
            self.env.cr.execute(query, params)
            res =  self.env.cr.dictfetchall()
            for r in res:
                list_match_in_futur.append(r['id'])

            if list_match_in_futur and not data['form']['reconciled']:
                if len(list_match_in_futur) == 1:
                    list_match_in_futur_sql = "(%s)" %(list_match_in_futur[0])
                else:
                    list_match_in_futur_sql = str(tuple(list_match_in_futur))
                reconcile_clause = ' AND (account_move_line.full_reconcile_id IS NULL OR account_move_line.full_reconcile_id IN ' + list_match_in_futur_sql + ')'

        return reconcile_clause, list_match_in_futur

    def _get_name_report(self, data):
        name = {'general':'General Ledger','partner':'Partner Ledger','journal':'Journal Ledger'}.get(data['form']['type_ledger'])
        if data['form']['summary']:
            name += ' Summary'
        return name
