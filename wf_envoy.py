"""
filename: 	wf_envoy.py
purpose:	Reads Enphase Envoy data directly, parses results and sends to the Wavefront Proxy
notes:
requirements:	Python v3.0 or later
author: 	Tony Phan
created:	19/05/2018
"""

envoy_fqdn = 'tp-lid-env01.tphome.local'
envoy_username = 'envoy'
envoy_password = '000112'

import datetime

def read_envoy_production_data( envoy_ip_addr ):
	# gets production json data from the envoy

	import urllib.request
	import json
	import socket
	import time

	socket.setdefaulttimeout(30)

	productionString = '/production.json'

	# build the full url to get the production data
	url = 'http://' + envoy_fqdn + productionString

	# https://docs.python.org/3.4/howto/urllib2.html#id5

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

	json_production_data = json.loads(string)

	# close the open response object
	#urllib.request.urlcleanup()
	response.close()

	# print pretty JSON
	#print(json.dumps(json_production_data, indent=4))

	return json_production_data
	# end of read_envoy_production_data() function

def main():

	# calls functions to get envoy data and pushes to Wavefront Proxy
	
	import json
	import time
	import socket
	
	sock = socket.socket()
	# wavefront proxy on localhost
	sock.connect(('127.0.0.1', 2878))

	production_data = read_envoy_production_data(envoy_fqdn)
	# reading timestamp
	#timestamp = time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime(production_data['production'][1]['readingTime']))
	timestamp_epoch = str(production_data['production'][1]['readingTime'])
	#print('Timestamp: ' + timestamp_epoch)

	# calculating production
	current_production = round(float(production_data['production'][1]['wNow']),2)
	# overriding envoy data when value is less than zero
	if current_production < 0:
		updated_current_production = 0
	else:
		updated_current_production = current_production
	# sending production metric to wavefront
	metric_current_production = 'envoy.production.watts' + ' ' +  str(updated_current_production) + ' ' + timestamp_epoch + ' ' +  'source=' + envoy_fqdn + ' \n'
	sock.sendall(metric_current_production.encode('utf-8'))
	#print(metric_current_production)

	# calculating consumption
	current_consumption = round(float(production_data['consumption'][0]['wNow']),2)
	updated_current_consumption = current_consumption
	# sending consumption metric to wavefront
	metric_current_consumption = 'envoy.consumption.watts' + ' ' + str(current_consumption) + ' ' + timestamp_epoch + ' ' +  'source=' + envoy_fqdn + ' \n'
	sock.sendall(metric_current_consumption.encode('utf-8'))
	#print(metric_current_consumption)

	# calculating net consumption
	updated_current_net_consumption = round(float(updated_current_production - current_consumption),2)
	# sending net consumption metric to wavefront
	metric_current_net_consumption = 'envoy.net.watts' + ' ' + str(updated_current_net_consumption) + ' ' + timestamp_epoch + ' ' +  'source=' + envoy_fqdn + ' \n'
	sock.sendall(metric_current_net_consumption.encode('utf-8'))
	#print(metric_current_net_consumption)
	
	sock.close()	

	# end of main() function

# call main() function to run program
main()
