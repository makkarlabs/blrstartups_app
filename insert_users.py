#This script is run for the first time to update User db with group members
#The Facebook API only returns ~5000 members, so usercron.py ensures daily updates of the User table
import urllib2
import urllib
import re
import ConfigParser
import json
import MySQLdb
import logging
import traceback
from datetime import datetime
import iso8601
import sys

def sane(text, quotes=True):
    if(quotes):
        return text.encode('ascii','ignore').replace('"','')
    else:
        return text.encode('ascii','ignore')

def parse_date(datestring):
    return iso8601.parse_date(datestring).strftime('%Y-%m-%d %H:%M:%S')


class UserArchiver:

    def __init__(self, config_filename):
        self.config = ConfigParser.ConfigParser()
        try:
            self.config.read(config_filename)
        except:
            print 'Config file'+str(config_filename)+' cannot be read'
            return
        config = self.config
        self.db = MySQLdb.connect(user=config.get('db','user'), passwd=config.get('db','password'), db=config.get('db','name'))
        self.cursor = self.db.cursor()
        logging.basicConfig(filename=config.get('logging','infolog'), level=logging.INFO)

    def process_data(self, group_url=None):
        controlchar_regex = re.compile(r'[\n\r\t]')
        cursor = self.cursor
        config = self.config
        if(group_url == None):
            group_url = config.get('group','url_user')#+str(limit)
        data = urllib2.urlopen(group_url).read()
        jsondata = json.loads(data)
        for i,user in enumerate(jsondata['data']):
            try:
                self.update_user(user) 
            except Exception, err:
                print 'Some error'
                logging.error(str(datetime.now())+" "+str(err))
                traceback.print_exc(file = open(config.get('logging','errorlog'),'a'))
        self.db.commit()
        self.db.close()
        print "Archiving Complete!"
        logging.info(str(datetime.now())+' Archiving Complete for page: '+group_url)

    def update_user(self, user):
        cursor = self.cursor
        user_id = user.get('uid')
        firstname = sane(user.get('first_name'))
        middlename = ""
        if user.get('middle_name') is not None:
            middlename = sane(user.get('middle_name'))
        lastname = sane(user.get('last_name'))
        gender = ""
        if user.get('sex') != "" and user.get('sex') is not None:
            gender = user.get('sex')[0]
        location = ""
        current_location = user.get('current_location')
        if current_location is not None:
            location = current_location.get('city')+', '+current_location('state')+', '+current_location.get('country')
        link = user.get('profile_url')
        if link is None:
            link = ""
        active = 0 
        username = user.get('username')
        cursor.execute("""SELECT InsertUser(%s, %s, %s, %s, %s, %s, %s, %s, %s) """, (user_id, active, firstname, middlename, lastname, gender, location, link, username))

try:
    UserArchiver(sys.argv[1]).process_data()    
except Exception, err:
    print sys.argv[0]
    print 'Pass config file as command line argument'
    print sys.argv[1]
    print err
                
