===============
SMS OVH Enpoint
===============

This module provide OVH SMS Endpoint.

Usage
=====

* Buy SMS package on https://www.ovh.com/
* Create your application on this page : https://eu.api.ovh.com/createApp/
* Excecute this python script to get your consumer key and set the access right settings::

   # -*- encoding: utf-8 -*-

   import ovh

   # Put your application key
   application_key='your_application_key'

   # Put your application secret
   application_secret='your_application_secret'

   # Put your endpoint default = 'ovh-eu'
   endpoint = 'ovh-eu'

   # create a client using configuration
   client = ovh.Client(endpoint, application_key=application_key, application_secret=application_secret, consumer_key='' )

   # Request RO, /me API access
   ck = client.new_consumer_key_request()
   ck.add_rules(ovh.API_READ_ONLY, "/me")

   # Request token
   validation = ck.request()

   print "Please visit %s to authenticate, and come back here." % validation['validationUrl']
   raw_input("and press Enter to continue...")

   # Print your consumer Key
   print "Welcome", client.get('/me')['firstname']
   print "Btw, your 'consumerKey' is '%s'" % validation['consumerKey']

   # Request RW, /me and /sms API access
   ck.add_recursive_rules(ovh.API_READ_ONLY, "/me")
   ck.add_recursive_rules(ovh.API_READ_WRITE, "/sms")

   raw_input("and press Enter to close...")

* Install this module
* Go to Settings > Technical > Iap Account configuration and select OVH.
* Only use international phone number ex : +33123456789 (Install phone_validation module)
