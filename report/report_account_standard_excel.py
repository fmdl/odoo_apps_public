# -*- coding: utf-8 -*-

from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class AccountStandardExcel(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, report):

        bold = workbook.add_format({'bold': True})
        currency_format = workbook.add_format({'num_format': '_ * #,##0.00_) ;_ * - #,##0.00 ;_ * "-"??_) ;_ @_ '})
        report_format = workbook.add_format({'font_size': 24})

        data = report.pre_print_report()

        sheet = workbook.add_worksheet(data['name_report'])
        sheet.write(0, 4, data['name_report'], report_format)
        sheet.write(2, 0, 'Company:', bold)
        sheet.write(3, 0, data['res_company'],)
        sheet.write(4, 0, 'Print on %s' % data['time'])

        sheet.write(2, 2, 'Start Date : %s ' % data['date_from'] if data['date_from'] else '')
        sheet.write(3, 2, 'End Date : %s ' % data['date_to'] if data['date_to'] else '')

        sheet.write(2, 4, 'Target Moves:', bold)
        sheet.write(3, 4, 'All Entries' if data['target_move'] == 'all' else 'All Posted Entries')

        sheet.write(2, 6, 'Only UnReconciled Entries' if data['reconciled'] == False else 'With Reconciled Entries', bold)
        sheet.write(3, 6, 'With entries matched with other entries dated after End Date.' if data['rem_futur_reconciled'] else '')

        all_lines = []
        for group_by in data['group_by_data']['ids']:
            for line in data['lines_group_by'][group_by]['new_lines']:
                if line['type_line'] != 'total':
                    all_lines.append(line)

        header = ['Date', 'JRNL', 'Account', 'Journal entries', 'Ref', 'Partner', 'Due Date', 'Debit', 'Credit', 'Balance', 'Currency', 'Match.']
        # Head
        head = [
            {'name': 'Date',
             'larg': 10,
             'col': {}},
            {'name': 'JRNL',
             'larg': 10,
             'col': {}},
            {'name': 'Account',
             'larg': 10,
             'col': {}},
            {'name': 'Journal entries',
             'larg': 20,
             'col': {}},
            {'name': 'Ref',
             'larg': 40,
             'col': {}},
            {'name': 'Partner',
             'larg': 20,
             'col': {}},
            {'name': 'Due Date',
             'larg': 10,
             'col': {}},
            {'name': 'Debit',
             'larg': 15,
             'col': {'total_function': 'sum', 'format': currency_format}},
            {'name': 'Credit',
             'larg': 15,
             'col': {'total_function': 'sum', 'format': currency_format}},
            {'name': 'Balance',
             'larg': 15,
             'col': {'format': currency_format}},
            {'name': 'Currency',
             'larg': 15,
             'col': {'format': currency_format}},
            {'name': 'Match.',
             'larg': 10,
             'col': {}},
        ]

        row = 6
        row += 1
        start_row = row
        for i, line in enumerate(all_lines):
            i += row
            sheet.write(i, 0, line['date'])
            sheet.write(i, 1, line['code'])
            sheet.write(i, 2, line['a_code'])
            sheet.write(i, 3, line['move_name'])
            sheet.write(i, 4, line['displayed_name'])
            sheet.write(i, 5, line['partner_name'])
            sheet.write(i, 6, line['date_maturity'])
            sheet.write(i, 7, line['debit'], currency_format)
            sheet.write(i, 8, line['credit'], currency_format)
            sheet.write(i, 9, line['progress'], currency_format)
            sheet.write(i, 10, line['amount_currency'], currency_format)
            sheet.write(i, 11, line['matching_number'])
        row = i

        for j, h in enumerate(head):
            sheet.set_column(j, j, h['larg'])

        table = []
        for h in head:
            col = {}
            col['header'] = h['name']
            col.update(h['col'])
            table.append(col)

        sheet.add_table(start_row, 0, row + 1, len(head) - 1,
                        {'total_row': 1,
                         'columns': table,
                         'style': 'Table Style Light 9',
                         })


AccountStandardExcel('report.account_standard_report.report_account_standard_excel', 'account.report.standard.ledger')
#'account_standard_report.report_account_standard_excel')
