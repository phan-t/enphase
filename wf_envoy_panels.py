"""
filename: 	wf_envoy_panels.py
purpose:	Reads Enphase Envoy panel data directly, parses results and sends to the Wavefront Proxy
notes:
requirements:	Python v3.0 or later
author: 	Tony Phan
created:	19/05/2018
"""

envoy_fqdn = 'tp-lid-env01.tphome.local'
envoy_username = 'envoy'
envoy_password = '000112'
json_inverter_file = 'inverter_list.json'

import datetime

def read_inverter_data( json_inverter_file ):
	# define a list of inverters related to their array position

	import json
	
	with open(json_inverter_file) as json_file:
		json_inverter_data = json.load(json_file)
	
	# print pretty JSON
	#print(json.dumps(json_inverter_data, indent=4))
	return json_inverter_data
	# end of read_inverter_data() function	

def read_envoy_panel_data( envoy_fqdn, envoy_username, envoy_password ):
	# gets panel json data from the envoy
	# panel readings require digest authentication

	import urllib.request
	import json
	import socket
	import time

	socket.setdefaulttimeout(30)

	panelString = '/api/v1/production/inverters/'

	# build the full url to get the panel data
	url = 'http://' + envoy_fqdn + panelString

	# https://docs.python.org/3.4/howto/urllib2.html#id5

	# to request Authorization header for basic Authentication, replace HTTPDigestAuthHandler object to HTTPBasicAuthHandler
	passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
	passman.add_password(None, url, envoy_username, envoy_password)
	#authhandler = urllib.request.HTTPBasicAuthHandler(passman)
	authhandler = urllib.request.HTTPDigestAuthHandler(passman)

	opener = urllib.request.build_opener(authhandler)
	urllib.request.install_opener(opener)

	try:
		response = urllib.request.urlopen(url,  timeout=30)
	except urllib.error.URLError as error:
		print('Data was not retrieved because error: {}\nURL: {}'.format(error.reason, url) )
		quit()  # exit the script, some error happened
	except socket.timeout:
		print('Connection to {} timed out, '.format( url))
		quit()  # exit the script, cannot connect

	try:
		# convert bytes to string type and string type to dict
		string = response.read().decode('utf-8')
	except urllib.error.URLError as error:
		print('Reading of data stopped because error:{}\nURL: {}'.format(error.reason, url) )
		response.close()  # close the connection on error
		quit()  # exit the script, some error happened
	except socket.timeout:
		print('Reading data at {} had a socket timeout getting inventory, '.format( url))
		response.close()  # close the connection on error
		quit()  # exit the script, read data timeout

	json_panel_data = json.loads(string)

	# close the open response object
	#urllib.request.urlcleanup()
	response.close()

	# print pretty JSON
	#print(json.dumps(json_panel_data, indent=4))

	return json_panel_data
	# end of function read_envoy_panel_data()

def main():

	# calls functions to get envoy data and pushes to Wavefront Proxy
	
	import json
	import socket

	sock = socket.socket()
	# wavefront proxy on localhost
	sock.connect(('127.0.0.1', 2878))
	
	inverter_data = read_inverter_data(json_inverter_file)

	panel_data = read_envoy_panel_data(envoy_fqdn, envoy_username, envoy_password)	
	for p in panel_data:
		for i in inverter_data:
			if p['serialNumber'] == i['serialNumber']:
				panel_name = i['name']
				panel_serial = i['serialNumber']
				panel_direction = i['direction']
				panel_last_watts = p['lastReportWatts']
				#panel_last_timestamp = time.strftime("%d %b %Y %H:%M:%S %Z", time.localtime(p['lastReportDate']))
				panel_last_timestamp_epoch = str(p['lastReportDate'])
				if panel_last_watts <= 1:
					updated_panel_last_watts = 0
				else:
					updated_panel_last_watts = panel_last_watts
				#updated_panel_data = panel_name + ',' + panel_serial + ',' + panel_direction + ',' + str(round(float(panel_last_watts),2)) + ',' + panel_last_timestamp		
				# sending panel production metric to wavefront
				metric_panel_current_production = 'envoy.production.watts' + '.' + panel_name + ' ' + str(round(float(updated_panel_last_watts),2)) + ' ' + panel_last_timestamp_epoch + ' ' + 'source=' + envoy_fqdn + ' ' + 'direction=' + '"' + panel_direction + '"' + ' \n'
				sock.sendall(metric_panel_current_production.encode('utf-8'))
				#print(metric_panel_current_production)
	
	sock.close()

	# end of main() function

# call main() function to run program
main()
