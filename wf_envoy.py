"""
filename: 		wf_envoy.py
purpose:		Reads Enphase Envoy data directly, parses results and sends to the Wavefront Proxy
notes:
requirements:	Python v3.0 or later
author: 		Tony Phan
created:		19/05/2018
"""

envoy_fqdn = 'tp-lid-env01.tphome.local'
envoy_username = 'envoy'
envoy_password = '000112'

import datetime

def read_envoy_prod_data( envoy_ip_addr ):
	# gets production json data from the envoy

	import urllib.request
	import json
	import socket
	import time

	socket.setdefaulttimeout(30)

	prodStr = '/production.json'

	# build the full url to get the production data
	url = 'http://' + envoy_fqdn + prodStr

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

	json_prod_data = json.loads(string)

	# close the open response object
	#urllib.request.urlcleanup()
	response.close()

	# print pretty JSON
	#print(json.dumps(json_prod_data, indent=4))

	return json_prod_data
	# end of read_envoy_prod_data() function

def main():

	# calls functions to get envoy data and pushes to Wavefront Proxy

	import json
	import time
	import socket

	sock = socket.socket()
	# wavefront proxy on localhost
	sock.connect(('127.0.0.1', 2878))

	prod_data = read_envoy_prod_data(envoy_fqdn)
	# reading timestamp
	#timestamp = time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime(prod_data['production'][1]['readingTime']))
	epoch = str(prod_data['production'][1]['readingTime'])
	#print('Timestamp: ' + epoch)

	# calculating production
	cur_prod = round(float(prod_data['production'][1]['wNow']),2)
	# overriding envoy data when value is less than zero
	if cur_prod < 0:
		upd_cur_prod  = 0
	else:
		upd_cur_prod  = cur_prod
	# sending production metric to wavefront
	met_cur_prod = 'envoy.production.watts' + ' ' +  str(upd_cur_prod ) + ' ' + epoch + ' ' +  'source=' + envoy_fqdn + ' \n'
	sock.sendall(met_cur_prod.encode('utf-8'))
	#print(met_cur_prod)

	# calculating consumption
	cur_cons = round(float(prod_data['consumption'][0]['wNow']),2)
	# sending consumption metric to wavefront
	met_cur_cons = 'envoy.consumption.watts' + ' ' + str(cur_cons) + ' ' + epoch + ' ' +  'source=' + envoy_fqdn + ' \n'
	sock.sendall(met_cur_cons.encode('utf-8'))
	#print(met_cur_cons)

	# calculating net consumption
	upd_cur_net_cons = round(float(upd_cur_prod  - cur_cons),2)
	# sending net consumption metric to wavefront
	met_cur_net_cons = 'envoy.net.watts' + ' ' + str(upd_cur_net_cons) + ' ' + epoch + ' ' +  'source=' + envoy_fqdn + ' \n'
	sock.sendall(met_cur_net_cons.encode('utf-8'))
	#print(met_cur_net_cons)

	sock.close()

	# end of main() function

# call main() function to run program
main()
