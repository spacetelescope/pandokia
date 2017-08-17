import os
import sys

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from pprint import pprint
from collections import OrderedDict


def recast(s):
    x = s
    try:
        x = int(x)
    except ValueError:
        try:
            x = float(x)
        except ValueError:
            try:
                if x.lower() == 'none':
                    x = None
            except ValueError:
                # Cannot recast; return original
                return s

    # If we made it through, return cast
    return x


class PDKConfigParser(configparser.ConfigParser):
    def getlist(self, section, option, **kwargs):
        value = self.get(section, option)
        return list(filter(None, (x.strip() for x in value.splitlines())))

    def getlist_auto(self, section, option, **kwargs):
        return [recast(x) for x in self.getlist(section, option)]

    def getlist_nested(self, section, option, **kwargs):
        delim=','
        if 'delim' in kwargs:
            delim = kwargs['delim']

        result = []
        records = self.getlist(section, option)
        for record in records:
            record = record.split(delim)
            for idx, value in enumerate(record):
                value = value.strip()
                record[idx] = recast(value)
            result.append(record)

        return result


class Misconfigured(Exception):
    pass


CONFIG_BASIC = 'config.ini'
CONFIG_EXTENDED = 'config.d'
CONFIG_DEFAULT_PATH = os.path.join(sys.prefix, 'etc', 'pandokia', CONFIG_BASIC)
CONFIG_DEFAULT_DICT = OrderedDict((
    ('database',
        OrderedDict((
            ('password_type', 'string'),
            ('backend', ''),
            ('db', ''),
            ('host', ''),
            ('user', ''),
            ('password', ''),
        )),
    ),
    ('access_control',
        OrderedDict((
            ('users', ''),
            ('admins', ''),
        )),
    ),
    ('pandokia',
        OrderedDict((
            ('debug', 'false'),
            ('statuses', 'P\nF\nE\nD\nM'),
            ('status_names', 'pass\nfail\nerror\ndisable\nmissing'),
            ('exclude_dirs', ''),
            ('runner_glob', ''),
            ('default_qid_expire_days', '30'),
            ('default_user_email_preferences', ''),
            ('recurring_prefix', 'daily'),
            ('flagok_file', ''),
        ))
    ),
    ('cgi',
        OrderedDict((
            ('url', ''),
            ('server_maintenance', 'false'),
            ('enable_magic_html_log', 'false'),
        ))
    ),
))

if 'PDK_CONFIG' in os.environ:
    PDK_CONFIG = os.path.join(os.environ['PDK_CONFIG'], CONFIG_BASIC)
elif 'PDK_CONFIG' not in os.environ:
    PDK_CONFIG = CONFIG_DEFAULT_PATH

if not os.path.exists(PDK_CONFIG):
    raise Misconfigured('Set PDK_CONFIG or create {}'.format(CONFIG_DEFAULT_PATH))

config = PDKConfigParser(inline_comment_prefixes=['#', ';'])
config.read_dict(CONFIG_DEFAULT_DICT)
config.read(PDK_CONFIG)
