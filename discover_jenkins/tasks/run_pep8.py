# -*- coding: utf-8 -*-
import os
import sys
import pep8
from optparse import make_option
import django
from django.conf import settings
from discover_jenkins.utils import check_output, get_app_locations


class Pep8Task(object):

    if django.VERSION < (1, 8):
        option_list = (
            make_option(
                "--pep8-exclude",
                dest="pep8-exclude",
                default=pep8.DEFAULT_EXCLUDE + ",migrations",
                help="exclude files or directories which match these "
                     "comma separated patterns (default: %s)" %
                     pep8.DEFAULT_EXCLUDE
            ),
            make_option(
                "--pep8-select", dest="pep8-select",
                help="select errors and warnings (e.g. E,W6)",
            ),
            make_option(
                "--pep8-ignore", dest="pep8-ignore",
                help="skip errors and warnings (e.g. E4,W)",
            ),
            make_option(
                "--pep8-max-line-length",
                dest="pep8-max-line-length", type='int',
                help="set maximum allowed line length (default: %d)" %
                     pep8.MAX_LINE_LENGTH
            ),
            make_option(
                "--pep8-rcfile", dest="pep8-rcfile",
                help="PEP8 configuration file"
            ),
        )

    def __init__(self, **options):
        if options.get('pep8_file_output', True):
            output_dir = options['output_dir']
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            self.output = open(os.path.join(output_dir, 'pep8.report'), 'w')
        else:
            self.output = sys.stdout

        self.pep8_rcfile = options['pep8-rcfile'] or self.default_config_path()
        self.pep8_options = {'exclude': options['pep8-exclude'].split(',')}
        if options['pep8-select']:
            self.pep8_options['select'] = options['pep8-select'].split(',')
        if options['pep8-ignore']:
            self.pep8_options['ignore'] = options['pep8-ignore'].split(',')
        if options['pep8-max-line-length']:
            self.pep8_options['max_line_length'] = \
                                                options['pep8-max-line-length']

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("--pep8-exclude",
            dest="pep8-exclude",
            default=pep8.DEFAULT_EXCLUDE + ",migrations",
            help="exclude files or directories which match these "
                 "comma separated patterns (default: %s)" %
                 pep8.DEFAULT_EXCLUDE)
        parser.add_argument("--pep8-select", dest="pep8-select",
            help="select errors and warnings (e.g. E,W6)")
        parser.add_argument("--pep8-ignore", dest="pep8-ignore",
            help="skip errors and warnings (e.g. E4,W)")
        parser.add_argument("--pep8-max-line-length",
            dest="pep8-max-line-length", type='int',
            help="set maximum allowed line length (default: %d)" %
                 pep8.MAX_LINE_LENGTH)
        parser.add_argument("--pep8-rcfile", dest="pep8-rcfile",
            help="PEP8 configuration file")

    def teardown_test_environment(self, **kwargs):
        locations = get_app_locations()

        class JenkinsReport(pep8.BaseReport):
            def error(instance, line_number, offset, text, check):
                code = super(JenkinsReport, instance).error(
                    line_number, offset, text, check,
                )

                if not code:
                    return
                sourceline = instance.line_offset + line_number
                self.output.write(
                    '%s:%s:%s: %s\n' %
                    (instance.filename, sourceline, offset + 1, text),
                )

        pep8style = pep8.StyleGuide(
            parse_argv=False, config_file=self.pep8_rcfile,
            reporter=JenkinsReport, **self.pep8_options
        )

        for location in locations:
            pep8style.input_dir(os.path.relpath(location))

        self.output.close()

    @staticmethod
    def default_config_path():
        rcfile = getattr(settings, 'PEP8_RCFILE', 'pep8.rc')
        return rcfile if os.path.exists(rcfile) else None
