# -*- coding: utf-8 -*-
#
# Program to alert you when your grades have arrived in StudWeb
# @author Carl-Erik Kopseng <carlerik@ifi.uio.no>
# @date June 20 2013
#
# See README.md for installation and usage examples
# Also just testrun the program with `python studweb.py` to 
# see options
#
# Inspired by studweb.py by Sindre Frøyn <sindrf@ifi.uio.no>, 2009
#
# It works by
# - logging into studweb, 
# - parsing the results 
# - comparing those with the previously fetched results
# - printing the difference to screen 
# - writing the results page to file for later comparison
##

import requests, re, sys, os, datetime, codecs, stat
from bs4 import BeautifulSoup
from os.path import expanduser

config = None
studweb_hostname = None
latest_html = None

# The settings file
home = expanduser("~")
settings_file = home + '/.studweb.conf'
data_file = home + '/.studweb.dat'
error_file = home + '/.studweb.latest_error.html'

example_config = """\
ssn = 12345678901
pin = 1234
studweb = studweb.uio.no
"""
example_mail_config = """
smtp_server = smtp.uio.no
smtp_username = ola.nordmann
smtp_password = p4ssw0rd
from_addr = ola.nordmann@ifi.uio.no
to_addr = ola@nordmann.no
"""

studweb_settings = {

    'studweb.ntnu.no': {
        'term_used_for_semester': 'Termin',
        'expand_link_text': 'Oversikt'
    },

    'studweb.uio.no': {
        'term_used_for_semester': 'Semester',
        'expand_link_text': 'Se opplysninger om deg'
    }
}


class Mailer:
    def __init__(self, config):
        needed = ['from_addr', 'to_addr', 'smtp_password', 'smtp_username']
        missing = set(needed).difference(config)

        if missing:
            print("\nMissing email config values!\n\t " + ",".join(missing))
            sys.exit(1)

        self.__dict__.update(config)

    def send(self, subject, text):
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(text, _charset='utf8')
        msg['Subject'] = subject
        msg['From'] = self.from_addr
        msg['To'] = self.to_addr

        s = smtplib.SMTP_SSL(self.smtp_server, timeout=10)
        s.login(self.smtp_username, self.smtp_password)
        s.sendmail(self.from_addr, self.to_addr, msg.as_string())
        s.quit()

    def __str__(self):
        return str(self.__dict__)

class SubjectResult:

    def __init__(self, code, name, grade, semester):
        """Expects all strings to be unicode
        This will be true if given input from BeautifulSoup, as
        as internal data structures are using unicode"
        """
        self.__code = code
        self.__name = name
        self.__grade = grade
        self.__semester = semester

        import hashlib

        self.__bytes = self.__str__().encode('utf8')
        self.__hash = hashlib.md5(self.__bytes).hexdigest()

    # for use in sets and as keys in dicts
    def __hash__(self):
        return int(self.__hash, 16)

    # as str
    def __str__(s):
        return u" ".join([s.__code, s.__name, s.__grade, s.__semester])

    # for comparison
    def __eq__(s, o):
        return s.__code == o.__code \
               and s.__grade == o.__grade \
               and s.__semester == o.__semester

    def asBytes(self):
        return self.__bytes

    def asUnicode(self):
        s = self.__str__()
        assert is_unicode_str(s)
        return s


class PageParser:

    def __init__(self, term, expand_link_text):
        self.semester_string = term
        self.expand_link_text = expand_link_text

    def parse_page_with_expanded_link_section_for_logout_url(self, html_page):
        return find_bulleted_link(html_page, 'Logg ut')

    def parse_page_with_expanded_link_section_for_results_url(self, html):
        soup = BeautifulSoup(html)
        link = soup.find_all("a", title="Se dine resultater")
        check(link, "Could not find <a> tag with title \"Se dine resultater\"", soup.prettify())

        return link[0]['href']

    def parse_start_page_for_link_url_to_expand_link_section(self, start_page_html):
        return find_bulleted_link(start_page_html, self.expand_link_text)

    def parse_login_page_for_path_to_form_handler(self, login_html):
        soup = BeautifulSoup(login_html)
        form = soup.select("form[name=fnrForm]")[0]

        return form['action']

    def parse_login_page_for_form_values(self, login_html):
        """Parses the login page for form input (also hidden with pre-set values)

        Returns a dictionary with <input:value>
        """

        soup = BeautifulSoup(login_html)
        inputs = soup.select("form[name=fnrForm] input")

        attributes = [i.attrs for i in inputs]
        form_values = {}

        for a in attributes:
            form_values[a.get('name')] = a.get('value')

        return form_values


    def parse_result_page_for_results(self, html):
        """Parses result page and returns a list of the subject results

        html - the html of the page containing the results
        """

        assert html != None
        assert is_unicode_str(html)

        soup = BeautifulSoup(html)

        # parse the results table
        result_table = soup.table.table
        headers = result_table.find_all("th")

        index_lookup = {}
        for s in [self.semester_string, 'Emnekode', 'Emnenavn', 'Resultat']:
            hits = [i for i, th in enumerate(headers) if th.text.find(s) >= 0]
            assert len(hits) > 0, "Did not find a header with the name %s" % s
            index_lookup[s] = hits[0]

        assert len(index_lookup.values()) == 4, 'Page layout has changed!'

        # only find rows with non-blank subject code
        relevant_trs = [tr
                        for tr in result_table.find_all('tr')[1:-2]  # Skip the first row with headers
                        for i, c in enumerate(tr.children)
                        if i == index_lookup['Emnekode'] and c.text.strip()]

        results = set()

        for tr in relevant_trs:
            tmp = {}
            for i, c in enumerate(tr.find_all('td')):
                if i in index_lookup.values():
                    text = c.text.strip()
                    if i == index_lookup['Emnekode']:
                        tmp['code'] = text
                    if i == index_lookup[self.semester_string]:
                        tmp['semester'] = text
                    if i == index_lookup['Emnenavn']:
                        tmp['name'] = text
                    if i == index_lookup['Resultat']:
                        tmp['grade'] = text
            try:
                results.add(SubjectResult(
                    tmp['code'], tmp['name'], tmp['grade'], tmp['semester']))
            except KeyError as e:
                print("En feil skjedde. Fortsetter ...")
                print(e)
                print(tr)

        return results


def is_unicode_str(s):
    if sys.version_info >= (3, 0, 0):
        # for Python 3
        return not isinstance(s, bytes)
    else:
        # for Python 2 
        return isinstance(s, unicode)


def log_into_start_page(session, parser):
    # user_agent = "User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36"
    # extra_headers = { 'User-Agent' : user_agent }
    # s.headers.update(extra_headers)
    global studweb_hostname

    studweb_hostname = config['studweb']
    ssn = config['ssn']
    pin_code = config['pin']

    r = session.get(studweb_url())

    form_values = parser.parse_login_page_for_form_values(r.content)
    action = parser.parse_login_page_for_path_to_form_handler(r.content)

    # start filling in the values
    form_values['fodselsnr'] = ssn
    form_values['pinkode'] = pin_code

    # remove the field that says we need to get the pin by sms
    form_values.pop('pinmail')

    # set the submit action to be Logg inn
    form_values['WOSubmitAction'] = "Logg inn"

    r = session.post(studweb_url() + action,
                     data=form_values,
                     allow_redirects=True)

    # Når innlogget, husk å logge ut
    return r.content

def studweb_url():
    return 'https://' + config['studweb']

def logout(session, parser, html_page):
    if not html_page:
        raise Exception("No html received")

    logout_url = parser.parse_page_with_expanded_link_section_for_logout_url(html_page)
    session.get(studweb_url() + logout_url)


def check(find_result, error_msg, failing_html):
    if not find_result:
        f = codecs.open(error_file, 'w', encoding='utf8')
        decoded = codecs.decode(failing_html, 'iso8859-1')
        f.write(decoded)
        f.close()
        raise Exception(error_msg)


def diff(old, new):
    return new.difference(old)


def new_results(parser):
    return diff(old_results(parser), latest_results(parser))


def old_results(parser):
    if os.path.isfile(data_file):
        f = codecs.open(data_file, 'r', encoding='utf8')
        previous_html = f.read()
        f.close()
        return parser.parse_result_page_for_results(previous_html)
    return set()


def latest_results(parser):
    global latest_html

    session = requests.Session()  # The session object that persists cookies and default values across requests
    html = None

    try:
        login_page = log_into_start_page(session, parser)
        try:
            check(login_page,
                  "Failed parsing start page for expand link section. Check the configuration settings at " + settings_file,
                  login_page)
        except Exception as e:
            # try to get the error message
            error_msg = BeautifulSoup(login_page).select("#alert-box ul li")
            if error_msg:
                print_error("Caught error when trying to log in: \n" + error_msg[0].get_text())
                sys.exit(1)
            else:
                raise e

        url = parser.parse_start_page_for_link_url_to_expand_link_section(login_page)

        check(url, "Failed parsing start page for expand link section.", login_page)

        html = session.get(studweb_url() + url).content

        result_page_url = parser.parse_page_with_expanded_link_section_for_results_url(html)

        r = session.get(studweb_url() + result_page_url)

        html = BeautifulSoup(r.content).prettify()

    except Exception as e:
        print_error('Failed parsing: ' + str(e))
    finally:
        try:
            logout(session, parser, html)
        except Exception as e:
            print_error('Failed to log out:' + str(e))
            raise e
            # pass  # we might not be logged in

    # Saved to be stored later on
    latest_html = html

    return parser.parse_result_page_for_results(latest_html)


def find_bulleted_link(html, text_to_match):
    soup = BeautifulSoup(html)

    a = soup.find(lambda tag: tag.name == 'a' and tag.has_attr('href') and text_to_match in tag.text)

    check(a, 'Did not find "' + text_to_match + '".', html)

    return a['href']


def store(html):
    f = codecs.open(data_file, 'w', encoding='utf8', errors='ignore')
    f.write(html)
    f.close()


def get_parser(studweb_hostname):
    options = studweb_settings[studweb_hostname]

    if not options:
        raise Exception('No suitable page parser found.')

    return PageParser(options['term_used_for_semester'], options['expand_link_text'])


def modification_date(filename):
    import os.path

    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)


# Standardize printing of text for Python 2 and Python 3
def _print(s):
    assert is_unicode_str(s), "Not unicode: " + s
    if sys.version_info < (3, 0, 0):
        write = sys.stdout.write
    else:
        write = sys.stdout.buffer.write

    write((s + '\n').encode('utf-8'))


def print_error(s):
    sys.stderr.write((s + '\n').encode('utf-8'))
    sys.stderr.flush()


def read_config():
    config = None
    if os.path.isfile(settings_file):
        check_permissions()

        config = {}
        fp = open(settings_file, 'r')
        for l in fp.readlines():
            if len(l.strip()) == 0: continue

            k, v = [s.strip() for s in l.split("=")]
            config[k] = v
        fp.close()

    return config


def write_example_config(include_mail_config):
    fp = open(settings_file, 'w')
    fp.write(example_config)
    if include_mail_config:
        fp.write(example_mail_config)
    fp.close()

    # Make the file readable and writable by user only
    os.chmod(settings_file, stat.S_IRUSR | stat.S_IWUSR)

    print("Example config written to " + settings_file)
    print("Change values as necessary")


def send_mail(subject, body, config):
    mailer = Mailer(config)

    _print(u"\nMailing results to " + config['to_addr'])
    mailer.send(subject, body)
    _print(u"\nMail sent successfully")


def check_permissions():
    mode = os.stat(settings_file).st_mode

    if mode & stat.S_IROTH or mode & stat.S_IRGRP:
        print("The settings file should only be readable by the user!")
        print("Use `chmod 400 ~/.studweb.conf` to make it private")
        sys.exit(1)


if __name__ == '__main__':

    import argparse

    argument_parser = argparse.ArgumentParser(description="Retreive studweb results")
    argument_parser.add_argument("--mail",
                                 help="Use the built-in mailer instead of relying on cron to mail the results",
                                 action="store_true")
    argument_parser.add_argument("--quiet", help="Prevent output when there are no new results", action="store_true")
    argument_parser.add_argument("--config", help="Creates a default config file. Pass --mail to add email values",
                                 action="store_true")
    args = argument_parser.parse_args()

    body = ""
    subject = None
    config = read_config()

    if not config:

        if args.config:
            write_example_config(args.mail)
        else:
            print("No config file found. Try passing --help for more info")

        sys.exit(1)

    new = new_results(get_parser(config['studweb']))

    if new:
        subject = u"Found new results since last check!"
        _print(subject)

        for result in new:
            result = result.asUnicode()
            body += u"\n - " + result

        _print(u"\nNew results:" + body)

        _print(u"\nStoring results ...")
        store(latest_html)

        if args.mail:
            send_mail(subject, body, config)

    elif not args.quiet:
        _print(u"No new results since " + str(modification_date(data_file)))

    sys.exit(0)
