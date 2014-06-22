StudWeb results reporter
========================

> Retrieves your results from StudWeb, the student administration page, and mails you any new development since the last time you ran the script. 

# Installation
Two options, depending on whether you are a student at UiO or not

## UiO users
I have tried to make it as simple as possible for users at the University of Oslo by creating a script (`cronscript.sh`) that points at a valid Python 2.7 installation directory with all requirements pre-installed and executes the script that resides in my home directory. Simply copy-paste the following commands into a terminal, one-by-one.

        # generate config file 
        ~carlerik/src/studweb/cronscript.sh --config
        
        # edit the config file
        nano ~/.studweb.conf
        
        # test that the script is working - it should output your latest grades from studweb!
        ~carlerik/src/studweb/cronscript.sh

        # install crontab settings for polling StudWeb every 30 minutes
        crontab ~carlerik/src/studweb/cron_example

## Everyone else

        #Clone the repository 
        git clone git@github.com:fatso83/studweb.git

        cd studweb
        
        # install the requirements
        pip install -r requirements.txt
        
        # create config file
        python studweb.py --config 
        
        # edit the file using whatever editor you fancy (gedit, vim, emacs, nano)
        nano ~/.studweb.conf

        # test the script is working
        python studweb.py
        
        # edit the cron config to point to the valid path
        nano cron_example
        
        # install the cron file
        crontab cron_example
        
# Usage
Try running `python studweb.py -h` to see options. Passing `--config` will generate an example configuration file in $HOME/.studweb.conf that is suitable for use in a cron script. Edit this with your own configuration values, such as your social security number and pin code. It is created user readable only per default for this reason.

## Example run

        ~/scripts $ python studweb.py --mail

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
    
    */30 * * * * python2.7 /path/to/script/studweb.py --quiet
    
For your convenience I have created an example cronfile that can be installed simply by executing `crontab cron_example` in the script directory. The paths assume that the script is in ~carlerik/src/studweb

## University of Oslo
I have pre-configured 

# Mail
You can generate an example config with relevant values for sending mail by executing `python studweb --config --mail` the first time the script is run. 

## University of Oslo
For the UiO smtp server the username and password are the same as your regular authentication values and the server is called `smtp.uio.no`


# Tested environments found to be working
- Python 2.7.6 (OS X, 10.9.3)
- Python 2.7.7 (Red Hat Enterprise Linux 5.10 - the version running at smaragd.ifi.uio.no)
- Python 3.4.0 (OS X, 10.9.3)
- Python 3.4.0 (Ubuntu 14.04 LTS)

# Environments found problematic

## Python 2.6.7 (Ubuntu 14.04)
- There is an issue with smtplib where it hangs when calling `smtplib.SMTP_SSL()`, causing it to timeout.
