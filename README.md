StudWeb results reporter
========================

Retrieves your results from StudWeb, the student administration page, and mails you any new development since the last time you ran the script. 

# Usage
The first time you run the command it will generate an example configuration file in $HOME/.studweb.conf. Edit this with your own configuration values, such as username and password for your mail server. For the UiO server the username and password are the same as your regular authentication values.

## Example run
        ~/scripts $ python studweb.py

        New results:
         - MAT100B Grunnkurs i matematisk analyse med beregninger B Høst 2002
         - INF101 Grunnkurs i objektorientert programmering A Høst 2002
         - INF1820 Introduksjon til språk- og kommunikasjonsteknologi A Vår 2013
         - INF5261 Utvikling av mobile informasjonssystemer Bestått Høst 2013
         - INF2820 Datalingvistikk Godkjent Vår 2014

        Storing results ...

        Mailing results to myuser@ifi.uio.no

        Mail sent successfully


# Setting up a cron job to check regularly
    
    # Ignore the console output
    * * * * * /path/to/script/studweb.py > /dev/null


# Tested environments found to be working
- Python 2.7.6 (OS X, 10.9.3)
- Python 3.4.0 (OS X, 10.9.3)
- Python 3.4.0 (Ubuntu 14.04 LTS)

# Environments found problematic

## Python 2.6.7 (Ubuntu 14.04)
- There is an issue with smtplib where it hangs when calling `smtplib.SMTP_SSL()`, causing it to timeout.
