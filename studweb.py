# -*- coding: utf-8 -*-
#
# Program to alert you when your grades have arrived in StudWeb
# @author Carl-Erik Kopseng <carlerik@ifi.uio.no>
# @date June 20 2013
# Requires: Python 3 (can easily be changed to use Python 2)
#
# Inspired by studweb.py by Sindre Frøyn <sindrf@ifi.uio.no>, 2009
#
# It works by
# - logging into studweb, 
# - parsing the results 
# - comparing those with the previously fetched results
# - printing all results or just a formatted diff (if run with -d) to screen 
# - writing the result to file for later comparison
##

import requests, re, sys, os, datetime
from bs4 import BeautifulSoup
from os.path import expanduser

config = None
studweb = None # url of studweb
s = None # The session object that persists cookies and default values across requests
r = None # Request object passed around
parser = None
latest_html = None

# The settings file
home = expanduser("~")
settings_file = home + '/.studweb.conf'
data_file = home + '/.studweb.dat'

example_config = """\
ssn = 12345678901
pin = 1234
studweb = https://studweb.uio.no
smtp_server = smtp.uio.no
smtp_username = ola.nordmann
smtp_password = p4ssw0rd
from_addr = ola.nordmann@ifi.uio.no
to_addr = ola@nordmann.no
"""

class Mailer:

    def __init__(self, config):
        self.__dict__.update(config);

    def send(self, subject, text):
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(text)
        msg['Subject'] = subject
        msg['From'] = self.from_addr
        msg['To'] = self.to_addr

        s = smtplib.SMTP_SSL(self.smtp_server)
        s.login(self.smtp_username, self.smtp_password)
        s.sendmail(self.from_addr, self.to_addr, msg.as_string())
        s.quit()

    def __str__(self):
        return str(self.__dict__)

class SubjectResult:
    def __init__(self, code, name, grade, semester):
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
        return " ".join([s.__code, s.__name, s.__grade, s.__semester])

    # for comparison
    def __eq__(s, o): 
        return s.__code == o.__code \
                and s.__grade == o.__grade \
                and s.__semester == o.__semester

    def asBytes(self):
        return self.__bytes;

class ResultParser:
    semesterTerm = None 

    def __init__(self, term):
        self.semesterTerm = term 

    def parse(self, html):
        assert html != None
        soup = BeautifulSoup(html)

        # parse the results table
        result_table = soup.table.table
        headers = result_table.find_all("th")

        index_lookup={}
        for s in [self.semesterTerm, 'Emnekode', 'Emnenavn', 'Resultat']:
            hits = [ i for i, th in enumerate(headers) if th.text.find(s) >= 0 ]
            assert len(hits) > 0, "Did not find a header with the name %s" % s
            index_lookup[s]=hits[0]

        assert len(index_lookup.values()) == 4, 'Page layout has changed!'

        # only find rows with non-blank subject code
        relevant_trs = [tr 
                for tr in result_table.find_all('tr')[1:-2] #Skip the first row with headers 
                for i,c in enumerate(tr.children)
                if i == index_lookup['Emnekode'] and c.text.strip()]

        results=set()

        for tr in relevant_trs:
            tmp = {}
            for i,c in enumerate(tr.find_all('td')):
                if i in index_lookup.values():
                    text = c.text.strip()
                    if i == index_lookup['Emnekode']:
                        tmp['code'] = text
                    if i == index_lookup[self.semesterTerm]:
                        tmp['semester'] = text
                    if i == index_lookup['Emnenavn']:
                        tmp['name'] = text
                    if i == index_lookup['Resultat']:
                        tmp['grade'] = text
            try: 
                results.add( SubjectResult( \
                        tmp['code'], tmp['name'], tmp['grade'], tmp['semester'] ))
            except KeyError as e: 
                print("feil skjedde")
                print(e)
                _print(tr)

        return results

def init_session():
    #user_agent = "User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36" 
    #extra_headers = { 'User-Agent' : user_agent }
    #s.headers.update(extra_headers) 
    global r, s, studweb
    studweb = config['studweb']
    ssn = config['ssn']
    pin_code = config['pin']

    s = requests.Session()
    r = s.get(studweb)
    soup = BeautifulSoup(r.content)
    form = soup.select("form[name=fnrForm]")[0]
    inputs = soup.select("form[name=fnrForm] input") 

    attributes = [i.attrs for i in inputs]
    form_values = {}

    for a in attributes:
        form_values[a.get('name')] = a.get('value')

    form_values['fodselsnr'] = ssn
    form_values['pinkode'] = pin_code

    # remove the field that says we need to get the pin by sms
    form_values.pop('pinmail')

    # set the submit action to be Logg inn
    form_values['WOSubmitAction'] = "Logg inn"

    action = form['action']
    r = s.post( studweb + action,
            data = form_values,
            allow_redirects=True )

    # Når innlogget, husk å logge ut
    return r

def logout(html_page):
    if not html_page: 
        raise Exception("Missing legal string argument")

    soup = BeautifulSoup(html_page)
    link = soup.find_all('a',text=re.compile('Logg ut'))
    check(link, "Could not find <a> tag with text \"Logg ut\"")
    logoutUrl =  studweb + link[0]['href']

    return s.get( logoutUrl )

def get_url_to_result_page(start_page):
    global r,s

    soup = BeautifulSoup(start_page)
    link = soup.find_all('a',text=re.compile('Se opplysninger om deg'))
    check(link, "Failed logging in. Check the configuration settings at " + settings_file)
    r = s.get(studweb + link[0]['href'])

    soup = BeautifulSoup(r.content)
    link = soup.find_all("a", title="Se dine resultater")
    check(link, "Could not find <a> tag with title \"Se dine resultater\"")

    return studweb + link[0]['href']


def check(find_result, error_msg):
    if not find_result:
        raise Exception(error_msg)

def diff(old, new):
    return new.difference(old)

def new_results():
    global parser
    parser = ResultParser('Semester') # uio version, ntnu uses 'Termin'

    return diff(old_results(), latest_results())

def old_results():
    if os.path.isfile( data_file ):
        f = open( data_file, 'r', encoding='utf8')
        previous_html = f.read()
        return parser.parse(previous_html)
    return set()

def latest_results():
    global latest_html 
    latest_html = fetch_html()
    return parser.parse(latest_html)

def store(html):
    f = open( data_file, 'w', encoding='utf8', errors='ignore')
    f.write(html)
    f.close()

def fetch_html():
    global r, s

    try : 
        r = init_session()
        r = s.get(get_url_to_result_page(r.content))
        soup = BeautifulSoup(r.content)
        results_html = soup.prettify()
    except Exception as e : 
        print('Caught error!', e)
        sys.exit(1)
    finally :
        try: 
            r = logout(r.content)
        except:
            pass # we might not be logged in

    return results_html

def modification_date(filename):
    import os.path
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

def _print(o):
    print(str(o).encode('utf-8'))

def read_config():
    config = {}
    try:
        fp = open(settings_file, 'r')
        for l in fp.readlines():
            k, v = [s.strip() for s in l.split("=")]
            config[k] = v
        fp.close()
    except FileNotFoundError:
        print("No config file found")
        fp = open(settings_file, 'w')
        fp.write(example_config)
        fp.close()
        print("Example config written to " + settings_file)
        print("Change values as necessary")
        sys.exit(1)

    return config

if __name__ == '__main__':

    config = read_config()

    mailer = Mailer(config)

    output = ""

    new = new_results()
    body = ""
    if new:
        subject = "Found new results since last check!"
        for r in new:
            body += '\n' + str(r)
        store(latest_html)
        mailer.send(subject, body)
    else:
        subject = "No new results since " + str(modification_date(data_file))

