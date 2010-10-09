#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import cgi, os, datetime
import logging
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template

# variable things
sales = ['4155555555', '4155555555'] # tom, dick
support = ['4155555555', '4155555555', '4155555555'] # tom, dick and harry
accounts = ['4155555555', '4155555555'] # tom, harry 
jobs = ['4155555555', '4155555555', '4155555555'] # harry, tom, and sue
appengineurl = 'yourappname.appspot.com'
domain = "yourdomain.com"

def log(stuff):
  # log to loggly
  try:
     result = urlfetch.fetch(url="http://logs.loggly.com/inputs/2daebbed-0c2b-40f0-b4ec-fe8b35b8f2a0", payload=stuff, method=urlfetch.POST)
  except:
	 pass
  logging.debug(stuff) 

class Pacific_tzinfo(datetime.tzinfo):
    """Implementation of the Pacific timezone."""
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-8) + self.dst(dt)

    def _FirstSunday(self, dt):
        """First Sunday on or after dt."""
        return dt + datetime.timedelta(days=(6-dt.weekday()))

    def dst(self, dt):
        # 2 am on the second Sunday in March
        dst_start = self._FirstSunday(datetime.datetime(dt.year, 3, 8, 2))
        # 1 am on the first Sunday in November
        dst_end = self._FirstSunday(datetime.datetime(dt.year, 11, 1, 1))

        if dst_start <= dt.replace(tzinfo=None) < dst_end:
            return datetime.timedelta(hours=1)
        else:
            return datetime.timedelta(hours=0)
    def tzname(self, dt):
        if self.dst(dt) == datetime.timedelta(hours=0):
            return "PST"
        else:
            return "PDT"

def isopen(department):
    # get date and hour for office in SF
    dow = int(datetime.datetime.now(Pacific_tzinfo()).weekday())
    hour = int(datetime.datetime.now(Pacific_tzinfo()).hour)
    minute = int(datetime.datetime.now(Pacific_tzinfo()).minute)
    
    if department == 'sales':
        # sales open M-F 10AM-6PM
        return dow < 6 and 9<hour<18
    if department == 'support':
        # support open all week 7AM-10PM
        return 6<hour<23
    if department == 'accounts':
        # accounting open M-F 10AM-5PM
        return dow < 6 and 9<hour<17
    if department == 'jobs':
        # HR open M-F 10AM-5PM
        return dow < 6 and 9<hour<17	
	
class PhoneHandler(webapp.RequestHandler):
  def get(self):
    calling_number = self.request.get('From')
    called_number = self.request.get('To')
    node = self.request.get('node')
    whofor = self.request.get('for')
    digits = self.request.get('Digits');

    info = "%s to %s - node: %s, digits: %s" % (calling_number or "unknown", called_number or "unknown", node or 'unknown', digits or 'unknown')
    log(info)

    # no values to templates
    template_values = ""
    numbers = ""

    # check for the door at 78 1st calling
    if calling_number == "+14154890402":
    	path = os.path.join(os.path.dirname(__file__), 'templates/door.xml')
    	self.response.headers['Content-Type'] = 'text/xml'
    	self.response.out.write(template.render(path, template_values))  
    else:
        if (digits):
            if digits == "1":
                if isopen("support"):
    	            path = os.path.join(os.path.dirname(__file__), 'templates/holdforsupport.xml')
                    numbers = support
                else:
	                path = os.path.join(os.path.dirname(__file__), 'templates/closedsupport.xml')
            elif digits == "2":
                if isopen("accounts"):
                    logging.info("%s %s" % (dow, hour))
    	            path = os.path.join(os.path.dirname(__file__), 'templates/holdforaccounts.xml')
                    numbers = accounts
                else:
	                path = os.path.join(os.path.dirname(__file__), 'templates/closedaccounts.xml')
            elif digits == "3":
                if isopen("sales"):
                    path = os.path.join(os.path.dirname(__file__), 'templates/holdforsales.xml')
                    numbers = sales
                else:
	                path = os.path.join(os.path.dirname(__file__), 'templates/closedsales.xml')
            elif digits == "4":
                if isopen("jobs"):
    	            path = os.path.join(os.path.dirname(__file__), 'templates/holdforjobs.xml')
                    numbers = jobs
                else:
	                path = os.path.join(os.path.dirname(__file__), 'templates/closedjobs.xml')
            elif digits == "0":
    	    	path = os.path.join(os.path.dirname(__file__), 'templates/message.xml')
            else:
                path = os.path.join(os.path.dirname(__file__), 'templates/hankypanky.xml')
        elif (node):
            if node == "message":
    	    	path = os.path.join(os.path.dirname(__file__), 'templates/message.xml')
            elif node == "nosale":
    	    	path = os.path.join(os.path.dirname(__file__), 'templates/nosale.xml')
            elif node == "nosupport":
    	    	path = os.path.join(os.path.dirname(__file__), 'templates/nosupport.xml')
            elif node == "noaccount":
    	    	path = os.path.join(os.path.dirname(__file__), 'templates/noaccount.xml')
            elif node == "nojob":
    	    	path = os.path.join(os.path.dirname(__file__), 'templates/nojob.xml')
            else:
    	    	path = os.path.join(os.path.dirname(__file__), 'templates/message.xml')
        else:
            # play welcome message
    	    path = os.path.join(os.path.dirname(__file__), 'templates/welcome.xml')

        template_values = {'numbers': numbers, 'calling_number': calling_number, 'whofor': whofor, 'appengineurl': appengineurl}
    	self.response.headers['Content-Type'] = 'text/xml'
        self.response.out.write(template.render(path, template_values))  

  def post(self):
    self.get()

class MainPage(webapp.RequestHandler):
  def get(self):
	# get date and hour for office in SF
    dow = int(datetime.datetime.now(Pacific_tzinfo()).weekday())
    hour = int(datetime.datetime.now(Pacific_tzinfo()).hour)
    minute = int(datetime.datetime.now(Pacific_tzinfo()).minute)
    self.response.out.write("The phone app is functioning.  I think the day of week is %d and the time is %2d:%2d for the local timezone." % (dow, hour, minute))
    self.response.out.write("<br/><br/>Sales is: %s" % ("open" if isopen("sales") else "closed"))
    self.response.out.write("<br/><br/>Accounts is: %s" % ("open" if isopen("accounts") else "closed"))
  def post(self):
    self.get()

application = webapp.WSGIApplication( [('/', MainPage), ('/phone', PhoneHandler)], debug=True) 

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()

