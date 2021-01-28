#!/usr/bin/env python3.7
VERSION = 'v27121'
# Tested with PowerDNS Webinterface 1.5.3

import sys
import requests
import datetime
import pandas as pd
from cmd import Cmd
from tqdm import tqdm
from shlex import split as split_quotes
from prettytable import PrettyTable
from colorama import Fore, Back, Style

username = ''
password = ''
fqdn_interface = 'dns.example.com'

if not (username and password):
	print(f'{Style.BRIGHT}{Fore.RED}Please fill your credentials!{Style.RESET_ALL}')
	exit(0)

try:
	ask_debug = sys.argv[1]
	if ask_debug == 'debug':
		debug_mode = True
except IndexError:
	debug_mode = False
	pass

s = requests.Session()

class LoginError(Exception):
	pass

class PageError(Exception):
	pass

class BreakException(Exception):
	pass

def x_return_date():
	# Return date and time
	return datetime.datetime.now().strftime("%A %d %B %H:%M")

def x_save_deleted_records(data):
	with open('deleted_records.txt', "a+") as handler:
		for line in handler:
			if data in line:
				break
		else:
			handler.write("{}\n".format(data))

def platform_login():
	url = 'https://{}/?p=login'.format(fqdn_interface)
	headers = {
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
	'Accept-Encoding' : 'gzip, deflate, br',
	'Accept-Language' : 'it',
	'Cache-Control' : 'max-age=0',
	'Connection' : 'keep-alive',
	'Content-Length' : '40',
	'Content-Type' : 'application/x-www-form-urlencoded',
	'DNT' : '1',
	'Host' : 'dns.netorange.it:444',
	'Origin' : 'https://dns.netorange.it:444',
	'Referer' : 'https://dns.netorange.it:444/?p=login',
	'Sec-Fetch-Dest' : 'document',
	'Sec-Fetch-Mode' : 'navigate',
	'Sec-Fetch-Site' : 'same-origin',
	'Sec-Fetch-User' : '?1',
	'Upgrade-Insecure-Requests' : '1',
	'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
	}

	data = {
	'username' : username,
	'password' : password
	}

	req = s.post(url ,headers=headers, data = data)

	if req.status_code != 200:
		raise PageError
	elif any('Wrong' in s for s in req.text.split()):
		raise LoginError
	else:
		if debug_mode:
			print(f'{Style.BRIGHT}{Fore.YELLOW}Logged on DNS platform{Style.RESET_ALL}')

def load_domain_list():
	url = 'https://{}/?p=domains'.format(fqdn_interface)
	headers = {
	'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
	'Accept-Encoding' : 'gzip, deflate, br',
	'Accept-Language' : 'it',
	'Connection' : 'keep-alive',
	'Cookie' : cookie_sid,
	'DNT' : '1',
	'Host' : fqdn_interface,
	'Referer' : 'https://{}/?p=overview'.format(fqdn_interface),
	'Sec-Fetch-Dest' : 'document',
	'Sec-Fetch-Mode' : 'navigate',
	'Sec-Fetch-Site' : 'same-origin',
	'Sec-Fetch-User' : '?1',
	'Upgrade-Insecure-Requests' : '1',
	'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
	}
	req = s.get(url ,headers=headers)
	if req.status_code != 200:
		raise PageError

	domain_table = pd.read_html(req.content)
	domain_master_list = domain_table[0].values.tolist()

	for domain in domain_master_list:
		domain_list.append(domain)

	for index, domain in enumerate(domain_list):
		del domain_list[index][2:5]

	for id, domain in domain_list:
		domain_dict[domain] = id

	if debug_mode:
		print(f'{Style.BRIGHT}{Fore.YELLOW}Domain list loaded{Style.RESET_ALL}')

def get_domain_records(domain_name, *opts):
	if domain_name not in domain_dict:
		print()
		print(f'{Style.BRIGHT}{Fore.RED}Requested domain is not in database{Style.RESET_ALL}')
		return('missing')

	if opts:
		try:
			opts_command = opts[0]
			if opts[0] == 'retrieve':
				record_id = opts[1]
			elif opts[0] == 'full':
				pass
			elif opts[0] == 'load':
				pass
			elif opts[0] == 'validate':
				unload_domain()
				pass
			elif opts[0] == 'full_load':
				full_records_dict[domain_name] = {}
				pass
			else:
				domain_name = opts[0]
		except Exception:
			pass

	domain_id = str(domain_dict[domain_name])
	url = 'https://{}/?p=domainedit&pp[domain_id]={}'.format(fqdn_interface, domain_id)
	headers = {
	'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
	'Accept-Encoding' : 'gzip, deflate, br',
	'Accept-Language' : 'it',
	'Connection' : 'keep-alive',
	'Cookie' : cookie_sid,
	'DNT' : '1',
	'Host' : fqdn_interface,
	'Referer' : 'https://{}/?p=domains'.format(fqdn_interface),
	'Sec-Fetch-Dest' : 'document',
	'Sec-Fetch-Mode' : 'navigate',
	'Sec-Fetch-Site' : 'same-origin',
	'Sec-Fetch-User' : '?1',
	'Upgrade-Insecure-Requests' : '1',
	'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
	}
	req = s.get(url ,headers=headers)
	if req.status_code != 200:
		raise PageError

	table = pd.read_html(req.content)
	records_list = table[0].values.tolist()

	for index, domain in enumerate(records_list):
		del records_list[index][7]

	# Delete SOA and NS record
	#cleaned_records_list = list(records_list)
	#del cleaned_records_list[0:3]

	records_table = PrettyTable()
	records_table.field_names = ['ID', 'Name', 'Type', 'Content', 'TTL', 'Priority', 'Last change']

	for record in records_list:
		id, name, type, content, ttl, priority, last_change = record
		if str(name) == 'nan':
			name = '---'
		if str(last_change) == 'nan':
			last_change = '---'
		if opts:
			if opts_command in ('load', 'validate'):
				records_dict[id] = (name, type, content, ttl, priority)
				record_ids_list.append(id)
				record_type_list.append(type)
				record_names_list.append(name)
				record_contents_list.append(content)
				record_ttl_list.append(ttl)
				record_priority_list.append(priority)

				if len(content) > 80:
					content = content[:67] + '...(Use cmd "retr ID")'

			elif opts_command == 'retrieve':
				record_found = False
				for num, record in enumerate(records_list):
					if record_id == str(record[0]):
						record_found = True
						id, name, type, content, ttl, priority, last_change = record
						if str(name) == 'nan':
							name = '---'
						if str(last_change) == 'nan':
							last_change = '---'
						print()
						print("{} '{}'".format(f'{Style.BRIGHT}ID:{Style.RESET_ALL}', id))
						print("{} '{}'".format(f'{Style.BRIGHT}Name:{Style.RESET_ALL}', name))
						print("{} '{}'".format(f'{Style.BRIGHT}Type:{Style.RESET_ALL}', type))
						print("{} '{}'".format(f'{Style.BRIGHT}Content:{Style.RESET_ALL}', content))
						print("{} '{}'".format(f'{Style.BRIGHT}TTL:{Style.RESET_ALL}', ttl))
						print("{} '{}'".format(f'{Style.BRIGHT}Priority:{Style.RESET_ALL}', priority))
						print("{} '{}'".format(f'{Style.BRIGHT}Last change:{Style.RESET_ALL}', last_change))
						return

				if not record_found:
					print()
					print(f"{Style.BRIGHT}{Fore.RED}This record ID doesn't exists on the specified domain!{Style.RESET_ALL}")
					return

			elif opts_command == 'full':
				if len(content) > 80:
					content = content[:67] + '...(Use cmd "retr ID")'

			elif opts_command == 'full_load':
				full_records_dict[domain_name][id] = {}
				full_records_dict[domain_name][id] = (name, type, content, ttl, priority)

		if not opts:
			if len(content) > 60:
				content = content[:30] + '...(Use arg "f | full")'
		if opts:
			if not opts_command == 'full_load':
				if str(name) == 'nan':
					name = '---'
				records_table.add_row([id, name, type, content, ttl, priority, last_change])
		else:
			if str(name) == 'nan':
				name = '---'
			records_table.add_row([id, name, type, content, ttl, priority, last_change])

	if opts:
		if opts_command in ('full_load', 'validate'): # Don't print records table
			return

	print(records_table)

def full_load():
	def x_full_load():
		print(f'{Style.BRIGHT}{Fore.WHITE}Loading all domains records...{Style.RESET_ALL}')
		for _, domain in tqdm(domain_list):
			if debug_mode:
				print('Full loading... {}'.format(domain))
			#if domain == 'assemblaggiototale.it':
			#	break
			get_domain_records(domain, 'full_load')

	if not full_records_dict:
		x_full_load()
	else:
		print(f'{Style.BRIGHT}{Fore.YELLOW}Full records list has already been loaded{Style.RESET_ALL}')
		print()
		answer = query_yes_no(f'{Style.BRIGHT}{Fore.YELLOW}Do you want to purge and reload ?{Style.RESET_ALL}')
		if answer:
			x_full_load()
		else:
			print()
			print(f'{Style.BRIGHT}Action aborted{Style.RESET_ALL}')
			return

def x_type_retrieve(type, debug_mode):
	for _, domain in domain_list:
		if type == 'SPF':
			SPF_NUM = 0
			last_num = len(full_records_dict[domain].items())-1
			for num, key in enumerate(full_records_dict[domain].items()):
				if key[1][1] == 'TXT':
					if 'spf' in key[1][2]:
						SPF_NUM += 1
						#print('SPF_NUM', SPF_NUM)
						if debug_mode:
							ID = key[0]
							NAME = str(key[1][0])
							TYPE = key[1][1]
							CONTENT = key[1][2]
							TTL = key[1][3]
							PRIORITY = key[1][4]
							if NAME == 'nan':
								NAME = '---'
							#print('SPF DEBUG ENABLED')
							if len(key[1][2]) > 100:
								CONTENT = str(CONTENT[:40]) + f'{Style.BRIGHT}{Fore.YELLOW}...(Use cmd "retr DOMAIN ID"){Style.RESET_ALL}'
							print('{} {} -> [ID: {}] Name: {} , Type: {} , Content: {} , TTL: {} , Priority: {}'.format(f'{Fore.GREEN}SPF record found on domain{Style.RESET_ALL}', domain, ID, NAME, TYPE, CONTENT, TTL, PRIORITY))
						else:
							print('{} {}'.format(f'{Fore.GREEN}SPF record found on domain{Style.RESET_ALL}', domain))

				if num == last_num:
					if SPF_NUM == 0:
						print('{} {}'.format(f'{Fore.RED}SPF record missing on domain{Style.RESET_ALL}', domain))

		if type == 'DKIM':
			DKIM_NUM = 0
			last_num = len(full_records_dict[domain].items())-1
			for num, key in enumerate(full_records_dict[domain].items()):
				if key[1][1] == 'TXT':
					if 'DKIM1' in key[1][2]:
						DKIM_NUM += 1
						if debug_mode:
							ID = key[0]
							NAME = str(key[1][0])
							TYPE = key[1][1]
							CONTENT = key[1][2]
							TTL = key[1][3]
							PRIORITY = key[1][4]
							#print('DKIM DEBUG ENABLED')
							if NAME == 'nan':
								NAME = '---'
							if len(key[1][2]) > 100:
								CONTENT = str(CONTENT[:40]) + f'{Style.BRIGHT}{Fore.YELLOW}...(Use cmd "retr DOMAIN ID"){Style.RESET_ALL}'
							print('{} {} -> [ID: {}] Name: {} , Type: {} , Content: {} , TTL: {} , Priority: {}'.format(f'{Fore.GREEN}DKIM record found on domain{Style.RESET_ALL}', domain, ID, NAME, TYPE, CONTENT, TTL, PRIORITY))
						else:
							print('{} {}'.format(f'{Fore.GREEN}DKIM record found on domain{Style.RESET_ALL}', domain))
				if num == last_num:
					if DKIM_NUM == 0:
						print('{} {}'.format(f'{Fore.YELLOW}DKIM record missing on domain{Style.RESET_ALL}', domain))

def x_check_spf(debug_mode):
	x_type_retrieve('SPF', debug_mode)

def x_check_dkim(debug_mode):
	x_type_retrieve('DKIM', debug_mode)

def x_add_record(domain_name, record_name, record_type, record_content, record_ttl, record_priority):
	domain_id = str(domain_dict[domain_name])
	if record_name == '---':
		post_record_name = ""
	else:
		post_record_name = record_name

	url = 'https://{}/?a[0]=domainRecords-save'.format(fqdn_interface)
	headers = {
		'Accept' : '*/*',
		'Accept-Encoding' : 'gzip, deflate, br',
		'Accept-Language' : 'it',
		'Connection' : 'keep-alive',
		'Content-type' : 'application/x-www-form-urlencoded',
		'Cookie' : cookie_sid,
		'Host' : fqdn_interface,
		'Origin' : 'https://{}'.format(fqdn_interface),
		'Referer' : 'https://{}/?p=domainedit&pp[domain_id]={}'.format(fqdn_interface, domain_id),
		'Sec-Fetch-Dest' : 'empty',
		'Sec-Fetch-Mode': 'cors',
		'Sec-Fetch-Site': 'same-origin',
		'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
		'X-Requested-With' : 'XMLHttpRequest'
		}

	data = {
		'new[0][name]': post_record_name,
		'new[0][type]': record_type,
		'new[0][content]': record_content,
		'new[0][ttl]': record_ttl,
		'new[0][prio]': record_priority,
		'extra[domain_id]': domain_id
		}

	# INPUT SANITIZE
	if record_type not in ('A', 'AAAA', 'CNAME', 'MX', 'NS', 'PTR', 'SOA', 'SPF', 'SRV', 'TXT'):
		print(f'{Style.BRIGHT}{Fore.YELLOW}Record TYPE must be on of these: A, AAAA, CNAME, MX, NS, PTR, SOA, SPF, SRV, TXT{Style.RESET_ALL}')
		return

	if not record_ttl.isdecimal():
		print(f'{Style.BRIGHT}{Fore.YELLOW}Record TTL must be a number{Style.RESET_ALL}')
		return

	if not record_priority.isdecimal():
		print(f'{Style.BRIGHT}{Fore.YELLOW}Record PRIORITY must be a number{Style.RESET_ALL}')
		return

	for id, name, type, content, ttl, priority in zip(record_ids_list, record_names_list, record_type_list, record_contents_list, record_ttl_list, record_priority_list):
		if record_type in ('A', 'AAAA', 'CNAME', 'TXT'):
			if (str(record_name) == str(name) and record_type == type):
				print()
				print('{} {}'.format(f'{Style.BRIGHT}{Fore.CYAN}Record already exists -> ID:{Style.RESET_ALL}', id))
				return

	req = s.post(url, headers=headers, data = data)
	if req.status_code != 200:
		raise PageError

	x_validate_add(domain_name, record_name, record_type, record_content, record_ttl, record_priority)

def x_edit_record(domain_name, record_id, record_name, record_type, record_content, record_ttl, record_priority):
	domain_id = str(domain_dict[domain_name])
	if record_name == '---':
		record_name = ''

	url = 'https://{}/?a[0]=domainRecords-save'.format(fqdn_interface)
	headers = {
		'Accept' : '*/*',
		'Accept-Encoding' : 'gzip, deflate, br',
		'Accept-Language' : 'it',
		'Connection' : 'keep-alive',
		'Content-type' : 'application/x-www-form-urlencoded',
		'Cookie' : cookie_sid,
		'Host' : fqdn_interface,
		'Origin' : 'https://{}'.format(fqdn_interface),
		'Referer' : 'https://{}/?p=domainedit&pp[domain_id]={}'.format(fqdn_interface, domain_id),
		'Sec-Fetch-Dest' : 'empty',
		'Sec-Fetch-Mode': 'cors',
		'Sec-Fetch-Site': 'same-origin',
		'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
		'X-Requested-With' : 'XMLHttpRequest'
		}

	data = {
		'data[0][id]': record_id,
		'data[0][name]': record_name,
		'data[0][type]': record_type,
		'data[0][content]': record_content,
		'data[0][ttl]': record_ttl,
		'data[0][prio]': record_priority,
		'extra[domain_id]': domain_id
		}

	if not record_ttl.isdecimal():
		print(f'{Style.BRIGHT}{Fore.YELLOW}Record TTL must be a number{Style.RESET_ALL}')
		return

	if not record_priority.isdecimal():
		print(f'{Style.BRIGHT}{Fore.YELLOW}Record PRIORITY must be a number{Style.RESET_ALL}')
		return

	req = s.post(url, headers=headers, data = data)
	if req.status_code != 200:
		raise PageError

	x_validate_edit(domain_name, record_id, record_name, record_type, record_content, record_ttl, record_priority)

def x_delete_record(domain_name, record_id):
	url = 'https://{}/?a[0]=domainRecords-save'.format(fqdn_interface)
	domain_id = str(domain_dict[domain_name])
	headers = {
		'Accept' : '*/*',
		'Accept-Encoding' : 'gzip, deflate, br',
		'Accept-Language' : 'it',
		'Connection' : 'keep-alive',
		'Content-type' : 'application/x-www-form-urlencoded',
		'Cookie' : cookie_sid,
		'DNT' : '1',
		'Host' : fqdn_interface,
		'Origin' : 'https://{}'.format(fqdn_interface),
		'Referer' : 'https://{}/?p=domainedit&pp[domain_id]={}'.format(fqdn_interface, domain_id),
		'Sec-Fetch-Dest' : 'empty',
		'Sec-Fetch-Mode': 'cors',
		'Sec-Fetch-Site': 'same-origin',
		'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
		'X-Requested-With' : 'XMLHttpRequest'
		}

	data = {
		'delete[]': record_id,
		'extra[domain_id]': domain_id
		}

	req = s.post(url ,headers=headers, data = data)
	if req.status_code != 200:
		raise PageError

	x_validate_delete(domain_name, record_id)

def x_validate_add(domain_name, record_name, record_type, record_content, record_ttl, record_priority):
	get_domain_records(domain_name, 'validate')
	for name, type, content, ttl, priority in zip(record_names_list, record_type_list, record_contents_list, record_ttl_list, record_priority_list):
		if type in ('A', 'AAAA'):
			if str(name) == 'nan':
				name = ''
			if debug_mode: # Check if record was correctly added
				print(record_name, '<->',  name, record_name == name)
				print(record_type, type, record_type == type)
				print(record_content, content, record_content == content)
				print(record_ttl, ttl, int(record_ttl) == int(ttl))
				print(record_priority, priority, int(record_priority) == int(priority))
				print()

		if all([record_name == name, record_type == type, record_content == content, int(record_ttl) == int(ttl), int(record_priority) == int(priority)]):
			print()
			print(f'{Style.BRIGHT}{Fore.GREEN}Record successfully added{Style.RESET_ALL}')
			return

	print(f'{Style.BRIGHT}{Fore.RED}Error while adding new record{Style.RESET_ALL}')

def x_validate_edit(domain_name, record_id, record_name, record_type, record_content, record_ttl, record_priority):
	get_domain_records(domain_name, 'validate')
	for id, name, type, content, ttl, priority in zip(record_ids_list, record_names_list, record_type_list, record_contents_list, record_ttl_list, record_priority_list):
		if record_name == str('nan'):
			record_name = '---'
		if all([int(record_id) == int(id), record_name == name, record_type == type, record_content == content, int(record_ttl) == int(ttl), int(record_priority) == int(priority)]):
			print(f'{Style.BRIGHT}{Fore.GREEN}Record successfully modified{Style.RESET_ALL}')
			return

	print(f'{Style.BRIGHT}{Fore.RED}Error while editing new record{Style.RESET_ALL}')

def x_validate_delete(domain_name, record_id):
	get_domain_records(domain_name, 'validate')
	if record_id in [data for data in record_ids_list]:
		print('{} {}'.format(f'{Style.BRIGHT}{Fore.RED}Error while trying to delete record ID:{Style.RESET_ALL}', record_id))
		return
	print()
	print('{} {} {}'.format(f'{Style.BRIGHT}{Fore.GREEN}Record ID:{Style.RESET_ALL}', record_id, f'{Style.BRIGHT}{Fore.GREEN}deleted{Style.RESET_ALL}'))

def add_record(domain_name, record_name, record_type, record_content, record_ttl, record_priority):
	if not record_ids_list:
		print(f'{Style.BRIGHT}{Fore.RED}You must load a domain!{Style.RESET_ALL}')
		return

	x_add_record(domain_name, record_name, record_type, record_content, record_ttl, record_priority)

def edit_record(domain_name, record_id, record_name, record_type, record_content, record_ttl, record_priority):
	if not record_ids_list:
		print(f'{Style.BRIGHT}{Fore.RED}You must load a domain!{Style.RESET_ALL}')
		return

	for id, type in zip(record_ids_list, record_type_list):
		if int(record_id) == int(id):
			if record_type == type:
				continue
			else:
				print(f"{Style.BRIGHT}{Fore.RED}You can't change record type!{Style.RESET_ALL}")
				return

	x_edit_record(domain_name, record_id, record_name, record_type, record_content, record_ttl, record_priority)

def delete_record(domain_name, record_id):
	try:
		if not record_ids_list:
			print(f'{Style.BRIGHT}{Fore.RED}You must load a domain!{Style.RESET_ALL}')
			return
		elif not int(record_id) in record_ids_list:
			print(f"{Style.BRIGHT}{Fore.RED}This record ID doesn't exists on the loaded domain!{Style.RESET_ALL}")
			return
	except ValueError:
		print(f'{Style.BRIGHT}{Fore.YELLOW}Only numbers are accepted!{Style.RESET_ALL}')
		return

	name, type, content, ttl, priority = records_dict[int(record_id)]
	record_table = PrettyTable()
	record_table.field_names = ['ID', 'Name', 'Type', 'Content', 'TTL', 'Priority']
	record_table.add_row([record_id, name, type, content, ttl, priority])

	print()
	print(f'{Style.BRIGHT}{Fore.CYAN}You are about to delete this record:{Style.RESET_ALL}')
	print(record_table)
	print()
	answer = query_yes_no('Are you sure ?')

	if answer:
		if type in ('SOA', 'NS'):
			print(f"{Style.BRIGHT}{Fore.RED}You can't delete 'SOA' or 'NS' type records!{Style.RESET_ALL}")
			return
		else:
			x_save_deleted_records((x_return_date(), domain_name, name, type, content, ttl, priority))
			x_delete_record(domain_name, int(record_id))
	else:
		print()
		print(f'{Style.BRIGHT}Action aborted{Style.RESET_ALL}')

def load_domain(domain_name):
	unload_domain()
	if get_domain_records(domain_name, 'load') == 'missing':
		return('missing')

def unload_domain():
	record_ids_list.clear()
	record_type_list.clear()
	record_names_list.clear()
	record_contents_list.clear()
	record_ttl_list.clear()
	record_priority_list.clear()

def query_yes_no(question, default="no"):
	"""Ask a yes/no question via input() and return their answer.

	"question" is a string that is presented to the user.
	"default" is the presumed answer if the user just hits <Enter>.
		It must be "yes" (the default), "no" or None (meaning
		an answer is required of the user).

		The "answer" return value is True for "yes" or False for "no".
	"""
	valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
	if default is None:
		prompt = " [y/n] "
	elif default == "yes":
		prompt = " [Y/n] "
	elif default == "no":
		prompt = " [y/N] "
	else:
		raise ValueError("invalid default answer: '%s'" % default)

	while True:
		sys.stdout.write(question + prompt)
		choice = input().lower()
		if default is not None and choice == '':
			return valid[default]
		elif choice in valid:
			return valid[choice]
		else:
			sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")

# ----------------------------------------------

# Declares domains list and dictionary
domain_list = []
domain_dict = {}

# Declares records dictionary
records_dict = {}

# Declares specific record lists and dictionary
full_records_dict = {}
record_ids_list = []
record_names_list = []
record_type_list = []
record_contents_list = []
record_ttl_list = []
record_priority_list = []

# Declare CMD module sys list
cmd_loaded_domain = []

try:
	platform_login() # Login to the DNS platform
	cookie_sid = 'sid=' + str(s.cookies.values()[0]) # Set cookie ID
	try:
		load_domain_list()
	except PageError:
		print(f'{Style.BRIGHT}{Fore.RED}Failed to load domains list{Style.RESET_ALL}')
except LoginError:
	print(f'{Style.BRIGHT}{Fore.RED}Login error, closing...{Style.RESET_ALL}')
	try:
		sys.exit(1)
	except SystemExit:
		import os
		os._exit(1)

def x_reload(domain_name):
	# Clean autocomplete records list
	if cmd_loaded_domain:
		domain = cmd_loaded_domain[0]
		load_domain(domain_name)

if not debug_mode:
	APP_NAME = Style.BRIGHT + Fore.GREEN + "DNS_Navigator# " + Style.RESET_ALL
else:
	APP_NAME = Style.BRIGHT + Fore.RED + "DNS_Navigator[--DEBUG--]# " + Style.RESET_ALL

if __name__ == "__main__":
	import os.path
	histfile = os.path.expanduser('~/.dns_navigator_console_history')
	histfile_size = 100
	try:
		import readline
	except ImportError:
		readline = None

	class Prompt(Cmd):
		Cmd.prompt = APP_NAME

		def preloop(self):
			if readline and os.path.exists(histfile):
				readline.read_history_file(histfile)

		def postloop(self):
			if readline:
				del_list = ('y', 'Y', 'n', 'N', 'delete')
				import re
				for num in reversed(range(1, 101)):
					hist_item =  str(readline.get_history_item(num))
					if re.findall(r"(?=(\b" + '\\b|\\b'.join(del_list) + r"\b))", hist_item):
						#print('found bad string', num)
						readline.remove_history_item(num-1)
				readline.set_history_length(histfile_size)
				readline.write_history_file(histfile)

		def complete_get(self, text, line, begidx, endidx):
			completion = []
			for _, domain in domain_list:
				completion.append(domain)
			mline = line.partition(' ')[2]
			offs = len(mline) - len(text)
			return [s[offs:] for s in completion if s.startswith(mline)]

		def complete_load(self, text, line, begidx, endidx):
			completion = []
			for _, domain in domain_list:
				completion.append(domain)
			mline = line.partition(' ')[2]
			offs = len(mline) - len(text)
			return [s[offs:] for s in completion if s.startswith(mline)]

		def complete_edit(self, text, line, begidx, endidx):
			completion = []
			for record_id in record_ids_list:
				completion.append(str(record_id))
			mline = line.partition(' ')[2]
			offs = len(mline) - len(text)
			return [s[offs:] for s in completion if s.startswith(mline)]

		def complete_delete(self, text, line, begidx, endidx):
			completion = []
			for record_id in record_ids_list:
				completion.append(str(record_id))
			mline = line.partition(' ')[2]
			offs = len(mline) - len(text)
			return [s[offs:] for s in completion if s.startswith(mline)]

		def complete_retr(self, text, line, begidx, endidx):
			completion = []
			if cmd_loaded_domain:
				for record_id in record_ids_list:
					completion.append(str(record_id))
				mline = line.partition(' ')[2]
				offs = len(mline) - len(text)
				return [s[offs:] for s in completion if s.startswith(mline)]
			else:
				for _, domain in domain_list:
					completion.append(domain)
				mline = line.partition(' ')[2]
				offs = len(mline) - len(text)
				return [s[offs:] for s in completion if s.startswith(mline)]

		def complete_spf_bulk_check(self, text, line, begidx, endidx):
			completion = []
			completion.append('debug')
			mline = line.partition(' ')[2]
			offs = len(mline) - len(text)
			return [s[offs:] for s in completion if s.startswith(mline)]

		def complete_dkim_bulk_check(self, text, line, begidx, endidx):
			completion = []
			completion.append('debug')
			mline = line.partition(' ')[2]
			offs = len(mline) - len(text)
			return [s[offs:] for s in completion if s.startswith(mline)]

		def default(self, input):
			print('Command not found')
			print()

		def emptyline(self):
			pass

		def completedefault(line):
			print(line)

		def do_exit(self, input):
			'Close the console'
			print("Closing...")
			if not debug_mode:
				del globals()['s']
				del globals()['cookie_sid']
				Prompt.postloop(self)
				try:
					sys.exit(1)
				except SystemExit:
					import os
					os._exit(1)
			return True

		def do_spf_bulk_check(self, input):
			'Bulk check for SPF records in all domains [require cmd "full_load"] --> (Syntax: spf_bulk_check | spf_bulk_check d/debug)'
			if not full_records_dict:
				print(f'{Style.BRIGHT}{Fore.YELLOW}You must launch cmd "full_load" first{Style.RESET_ALL}')
				return

			if input in ('d', 'debug'):
				x_check_spf(True)
			else:
				x_check_spf(False)

		def do_dkim_bulk_check(self, input):
			'Bulk check for DKIM records in all domains [require cmd "full_load"] --> (Syntax: dkim_bulk_check | spf_bulk_check d/debug)'
			if not full_records_dict:
				print(f'{Style.BRIGHT}{Fore.YELLOW}You must launch cmd "full_load" first{Style.RESET_ALL}')
				return

			if input in ('d', 'debug'):
				x_check_dkim(True)
			else:
				x_check_dkim(False)

		def do_get(self, input):
			'Retrieve records list'
			if cmd_loaded_domain:
				domain_name = cmd_loaded_domain[0]
				if input in ('f', 'full'):
					get_domain_records(domain_name, 'full')
					return
				elif input:
					converted_tuple = ''.join(input)
					domain_name, *opts = converted_tuple.split()
					if opts:
						if opts[0] in ('f', 'full'):
							get_domain_records(domain_name, 'full')
							return
					else:
						get_domain_records(domain_name)
						return
				else:
					get_domain_records(domain_name)
					return

			if not input:
				print(f'{Style.BRIGHT}{Fore.YELLOW}Missing argument{Style.RESET_ALL}')
				print()
				return

			converted_tuple = ''.join(input)
			domain_name, *opts = converted_tuple.split()

			if opts:
				if opts[0] in ('f', 'full'):
					get_domain_records(domain_name, 'full')
			else:
				get_domain_records(domain_name)

		def do_retr(self, input):
			'Retrieve single record --> (Syntax: retr ID [loaded]| retr DOMAIN ID [unloaded])'
			try:
				domain_name = cmd_loaded_domain[0]
				if not input.isdecimal():
					converted_tuple = ''.join(input)
					try:
						domain_name, record_id = converted_tuple.split()
					except ValueError:
						print(f'{Style.BRIGHT}{Fore.YELLOW}Missing record ID{Style.RESET_ALL}')
						return
					print('{}'.format(f'{Style.BRIGHT}{Fore.YELLOW}Domain: {Style.RESET_ALL}' + domain_name))
					get_domain_records(domain_name, 'retrieve', record_id)
				else:
					get_domain_records(domain_name, 'retrieve', input)
				return
			except IndexError:
				pass

			if not input:
				print(f'{Style.BRIGHT}{Fore.YELLOW}Missing argument (retr DOMAIN ID){Style.RESET_ALL}')
				print()
				return

			converted_tuple = ''.join(input)
			try:
				domain_name, record_id = converted_tuple.split()
				if domain_name.isdecimal():
					print(f'{Style.BRIGHT}{Fore.YELLOW}Domain first, then record ID{Style.RESET_ALL}')
					print()
					return
			except ValueError:
				if input.isdecimal():
					print(f'{Style.BRIGHT}{Fore.YELLOW}Domain first, then record ID{Style.RESET_ALL}')
					print()
				else:
					print(f'{Style.BRIGHT}{Fore.YELLOW}Missing record ID{Style.RESET_ALL}')
					print()
				return

			print('{}'.format(f'{Style.BRIGHT}{Fore.YELLOW}Domain:{Style.RESET_ALL}' + domain_name))
			get_domain_records(domain_name, 'retrieve', record_id)

		def do_full_load(self, input):
			'Load all records from all domains for certain bulk tasks'
			answer = query_yes_no(f'{Style.BRIGHT}{Fore.RED}Launch this command only if you need to perform specifics bulk tasks, are you sure ?{Style.RESET_ALL}')
			if answer:
				full_load()
				print('{} records loaded'.format(sum([len(x) for x in full_records_dict.values()])))
				print()
			else:
				print()
				print(f'{Style.BRIGHT}Action aborted{Style.RESET_ALL}')

		def do_load(self, input):
			'Load domain for changes'
			cmd_loaded_domain.clear()
			if not input:
				print(f'{Style.BRIGHT}{Fore.YELLOW}Missing argument{Style.RESET_ALL}')
				print()
				return
			else:
				if load_domain(input) != 'missing':
					cmd_loaded_domain.append(input)
					if not debug_mode:
						Cmd.prompt = Style.BRIGHT + Fore.YELLOW + "DNS_Navigator(" + input + ")# " + Style.RESET_ALL
					else:
						Cmd.prompt = Style.BRIGHT + Fore.CYAN + "DNS_Navigator(" + input + ")[--DEBUG--]# " + Style.RESET_ALL

		def reload(self, input):
			if cmd_loaded_domain:
				domain = cmd_loaded_domain[0]
				load_domain(input)

		def do_unload(self, input):
			'Unload domain'
			unload_domain()
			cmd_loaded_domain.clear()
			Cmd.prompt = APP_NAME

		def do_add(self, input):
			'Add record for a domain --> (Syntax: add NAME TYPE CONTENT TTL PRIORITY) [Use "---" for an empty NAME]'
			try:
				domain_name = cmd_loaded_domain[0]
			except IndexError:
				print(f'{Style.BRIGHT}{Fore.RED}You must load a domain!{Style.RESET_ALL}')
				print()
				return

			try:
				if not input:
					print(f'{Style.BRIGHT}{Fore.YELLOW}Missing argument{Style.RESET_ALL}')
					print(f'{Style.BRIGHT}Syntax: add NAME TYPE CONTENT TTL PRIORITY{Style.RESET_ALL}')
					print()
					return
				domain_name = cmd_loaded_domain[0]
				record_name, record_type, record_content, record_ttl, record_priority = split_quotes(input)
				add_record(domain_name, record_name, record_type, record_content, record_ttl, record_priority)
			except ValueError:
				print()
				print('{} {} {}'.format(f'{Style.BRIGHT}{Fore.YELLOW}You must give 5 objects: NAME TYPE CONTENT TTL PRIORITY. not', len(input.split()), f'{Style.RESET_ALL}'))
				return
			print()
			x_reload(domain_name)

		def do_edit(self, input):
			'Edit record on a domain --> (Syntax: edit ID NAME TYPE CONTENT TTL PRIORITY)'
			try:
				domain_name = cmd_loaded_domain[0]
			except IndexError:
				print(f'{Style.BRIGHT}{Fore.RED}You must load a domain!{Style.RESET_ALL}')
				print()
				return

			try:
				if not input:
					print(f'{Style.BRIGHT}{Fore.YELLOW}Missing argument{Style.RESET_ALL}')
					print(f'{Style.BRIGHT}Syntax: edit ID NAME TYPE CONTENT TTL PRIORITY{Style.RESET_ALL}')
					print()
					return
				domain_name = cmd_loaded_domain[0]
				record_id, record_name, record_type, record_content, record_ttl, record_priority = split_quotes(input)
				if record_type in ('SOA', 'NS'):
					print(f"{Style.BRIGHT}{Fore.RED}You can't edit 'SOA' or 'NS' type records!{Style.RESET_ALL}")
					return
				edit_record(domain_name, record_id, record_name, record_type, record_content, record_ttl, record_priority)
			except ValueError:
				print('{} {} {}'.format(f'{Style.BRIGHT}{Fore.YELLOW}You must give 6 objects: ID NAME TYPE CONTENT TTL PRIORITY. not', len(input.split()), f'{Style.RESET_ALL}'))
				print()
				return
			print()
			x_reload(domain_name)

		def do_delete(self, input):
			'Delete record for a domain --> (Syntax: delete ID)'
			try:
				domain_name = cmd_loaded_domain[0]
			except IndexError:
				print(f'{Style.BRIGHT}{Fore.RED}You must load a domain!{Style.RESET_ALL}')
				print()
				return

			if not input:
				print(f'{Style.BRIGHT}{Fore.YELLOW}Missing argument{Style.RESET_ALL}')
				print()
			else:
				try:
					domain_name = cmd_loaded_domain[0]
					delete_record(domain_name, str(input))
					x_reload(domain_name)
				except IndexError:
					print(f'{Style.BRIGHT}{Fore.RED}You must load a domain!{Style.RESET_ALL}')
					return
			print()
			#x_reload(domain_name)

		def do_count(self, input):
			'Shows the count of loaded domains'
			print()
			print('{} domains loaded'.format(len(domain_list)))

		do_EOF = do_exit
	try:
		Prompt().cmdloop()
	except KeyboardInterrupt:
		print('Closing...')
		del globals()['s']
		del globals()['cookie_sid']
		try:
			sys.exit(1)
		except SystemExit:
			import os
			os._exit(1)
