# -*- coding: utf-8 -*-

{
    'name': 'Standard Accounting Report',
    'version': '1.1',
    'category': 'Accounting & Finance',
    'author': 'Florent de Labarre',
    'description': """Standard Accounting Report""",
    'summary': 'Standard Accounting Report',
    'website': 'https://github.com/fmdl',
    'depends': ['account', 'report_xlsx'],
    'data': [
        'data/report_paperformat.xml',
        'data/account_report.xml',
        'report/report_account_standard_report.xml',
        'views/account_view.xml',
        'views/account_standard.xml',
        'wizard/account_standard_report_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
