# !/usr/bin/python

# from collections import namedtuple

import datetime
import math
import os
import numpy as np
import pandas as pd
import pdb
import requests
import subprocess
import sys
import zipfile
import zlib

spred_log_file = 0

def check_HTTP_status_code(action, response, subj_spred_ID):
	'''
	Check that the web service request was successful.  
	If it wasn't, exit program and print out error details.
	action is the action that was being performed when the error occurred,
	response is the response object returned by the REST API call,
	subj_spred_ID is the well-formatted SPReD ID of the subject.
	'''

	if response.status_code == 401:
		print 'You probably entered an invalid username or password.'

	# for some reason the user doesn't have permission to delete the subject
	# ask admin to delete subject, and skip subject for the time being
	if response.status_code == 403 and action == 'deleting subject':
		print 'You do not have permission to delete subject ' + subj_spred_ID
		print 'Ask administrator of SPReD project to delete subject ' + subj_spred_ID

	if response.status_code != 200 and response.status_code != 201:
		print 'Error processing subject: ' + subj_spred_ID
		print 'Problem related to action: ' + action
		print 'Generated an HTTP Response Error Code: ' + str(response.status_code)
		spred_log_file.writelines(' '.join(['Problem', action, 'for subject', subj_spred_ID]))
		spred_log_file.close()
		sys.exit()


def create_scan(MINC_filename, subj_spred_ID, session_name, project_constants):
	'''
	Summary:
		Creates a scan in SPReD, including the upload of any associated files.
	Args:
		MINC_filename: The name of the MINC file to upload.
		subj_spred_ID: The well-formatted SPReD ID for the subject.
		session_name: The well-formatted session name.
		project_constants: A dictionary containing metadata related to the project and upload.
	'''

	# Create scan
	scan_params = get_scan_metadata(MINC_filename, project_constants)
	url = project_constants['base_url'] + project_constants['project_name'] + '/subjects/' + subj_spred_ID + '/experiments/' + session_name + '/scans/scan' + str(int(project_constants['scan_num']))
	resp = project_constants['session'].put(url, params=scan_params)
	check_HTTP_status_code('creating scan', resp, subj_spred_ID)

	# Create resource
	resource_params = get_resource_metadata(project_constants)
	url = project_constants['base_url'] + project_constants['project_name'] + '/subjects/' + subj_spred_ID + '/experiments/' + session_name + '/scans/scan' + str(int(project_constants['scan_num'])) + '/resources/' + str(int(project_constants['resource_num']))
	resp = project_constants['session'].put(url, params=resource_params)
	check_HTTP_status_code('creating resource', resp, subj_spred_ID)

	# Upload the distortion corrected image 
	url = project_constants['base_url'] + project_constants['project_name'] + '/subjects/' + subj_spred_ID + '/experiments/' + session_name + '/scans/scan' + str(int(project_constants['scan_num'])) + '/resources/' +  str(int(project_constants['resource_num'])) + '/files/'
	zip_name = subj_spred_ID + '_distortion_corrected' + '.zip'
	upload_zip(file_names=[MINC_filename], zip_name=zip_name, url=url, subj_spred_ID=subj_spred_ID, action='upload distortion corrected', project_constants=project_constants)

	# Create resource
	resource_params = get_resource_metadata(project_constants)
	url = project_constants['base_url'] + project_constants['project_name'] + '/subjects/' + subj_spred_ID + '/experiments/' + session_name + '/scans/scan' + str(int(project_constants['scan_num'])) + '/resources/' + str(int(project_constants['resource_num']) + 1)
	resp = project_constants['session'].put(url, params=resource_params)
	check_HTTP_status_code('creating resource', resp, subj_spred_ID)

	# Upload additional registrations of an image
	file_names = get_registration_files(MINC_filename)
	# pdb.set_trace()
	url = project_constants['base_url'] + project_constants['project_name'] + '/subjects/' + subj_spred_ID + '/experiments/' + session_name + '/scans/scan' + str(int(project_constants['scan_num'])) + '/resources/' +  str(int(project_constants['resource_num']) + 1) + '/files/'
	zip_name = subj_spred_ID + '_registrations' + '.zip'
	upload_zip(file_names=file_names, zip_name=zip_name, url=url, subj_spred_ID=subj_spred_ID, action='upload resampled and stats registrations', project_constants=project_constants)

	# Notify user of success and print information about the upload to a logfile
	notify_user_of_success(subj_spred_ID, MINC_filename)
	print_to_logfile(subj_spred_ID, MINC_filename)


def create_session(MINC_filename, subj_spred_ID, session_name, project_constants):
	'''
	Summary:
		Creates a session in SPReD.
	Args:
		MINC_filename: The name of the MINC file to upload.
		subj_spred_ID: The well-formatted SPReD ID for the subject.
		session_name: The well-formatted session name.
		project_constants: A dictionary containing metadata related to the project and upload.
	'''

	session_params = get_session_metadata(MINC_filename, session_name, project_constants)
	url = project_constants['base_url'] + project_constants['project_name'] + '/subjects/' + subj_spred_ID + '/experiments/' + session_name
	resp = project_constants['session'].put(url, params=session_params)
	check_HTTP_status_code('creating session', resp, subj_spred_ID)


def create_subject(MINC_filename, subj_spred_ID, row, project_constants):
	'''
	Summary:
		Creates a subject in SPReD.
	Args:
		MINC_filename: The name of the MINC file to upload.
		subj_spred_ID: The well-formatted SPReD ID for the subject.
		row: A row in a pandas data frame with subject metadata.
		project_constants: A dictionary containing metadata related to the project and upload.
	'''

	# Determine if the subject already exists.
	url = project_constants['base_url'] + project_constants['project_name'] + '/subjects/' + subj_spred_ID
	resp = project_constants['session'].get(url)
	
	# If the subject already exists, delete it, so it can be created again.
	if resp.status_code != 404:
		url = project_constants['base_url'] + project_constants['project_name'] + '/subjects/' + subj_spred_ID + '?removeFiles=true'
		resp = project_constants['session'].delete(url)
		check_HTTP_status_code('deleting subject', resp, subj_spred_ID)

	# Create the subject with PUT.
	subj_params = get_subject_metadata(row, project_constants)
	url = project_constants['base_url'] + project_constants['project_name'] + '/subjects/' + subj_spred_ID
	resp = project_constants['session'].put(url, params=subj_params)
	check_HTTP_status_code('creating subject', resp, subj_spred_ID)


def get_minc_field(field_name, MINC_filename):
	'''
	Summary:
		Calls a subprocess to extract a field's value from a MINC file. The mincinfo command is a specific command offered by MINC tools.
	Args:
		field_name: A valid field name from a MINC file.
		MINC_filename: The MINC file to extract the field value from.
	Returns:
		value: The value associated with the specified field from a MINC file.
	'''

	value = None

	try:
		value = subprocess.check_output(["mincinfo", "-attvalue", field_name, MINC_filename])
		value = value.rstrip()
	except subprocess.CalledProcessError:
		pass

	return value


def get_registration_files(MINC_filename):
	'''
	Summary:
		Given a filename of a distortion corrected mouse image, return a list of all registration files to be uploaded associated with the original file (e.g. lsq6, lsq12, nlin, processed).
	Args:
		MINC_filename: The name of the MINC file being uploaded for which to find the associated registration files.
	Returns:
		registration_files: A list of associated registration files (lsq6, lsq12, nlin, stats_volumes) for a MINC file.
	'''

	# can't just look for a 'processed' folder because there might be several processed folders
	# see other notes on this matter

	path_tuple = os.path.split(MINC_filename)
	basename = path_tuple[1]
	current_dir = path_tuple[0]
	parent_dir = os.path.dirname(current_dir)
	grandparent_dir = os.path.dirname(parent_dir)
	all_items = os.listdir(grandparent_dir)

	for item in all_items:
		if 'processed' in item:
			processed_dir = os.path.join(grandparent_dir, item)
			break

	processed_subj_dir = os.path.join(processed_dir, basename[0:-4])
	resampled_dir = os.path.join(processed_subj_dir, 'resampled')
	stats_dir = os.path.join(processed_subj_dir, 'stats-volumes')
	registration_files = []

	resampled_files = os.listdir(resampled_dir)
	for registration in resampled_files:
		registration_files.append(os.path.join(resampled_dir, registration))

	stats_files = os.listdir(stats_dir)
	for registration in stats_files:
		registration_files.append(os.path.join(stats_dir, registration))

	return registration_files


def get_resource_metadata(project_constants):
	'''
	Summary:
		Populate resource metadata.
	Args:
		project_constants: A dictionary containing metadata related to the project and upload.
	Returns:
		resource_params: A dictionary of name:value pairs needed to upload SPReD resources.
	'''

	resource_params = {
		'format': project_constants['file_type'],
		'content': project_constants['scan_type']
	}

	return resource_params


def get_scan_metadata(MINC_filename, project_constants):
	'''
	Summary:
		Extract scan metadata from a MINC file (MINC_filename) and return a dictionary mapping XNAT XML (keys) to MINC metadata (values).
	Args:
		MINC_filename: A filename specifying the MINC file to upload.
		project_constants: A dictionary containing metadata related to the project and upload.
	Returns:
		scan_params: A dictionary containing relevant scan metadata name value pairs for a given MINC file.
	'''

	# constant key-value pairs go here which are the same for every subject
	scan_params = {
		'xsiType': 'xnat:mrScanData',
		'xnat:mrScanData/type': project_constants['scan_type'],  # double check that this is the format SPReD wants
		'xnat:mrScanData/quality': project_constants['quality'],
		'xnat:mrScanData/scanner': project_constants['scanner'],
		'xnat:mrScanData/scanner/manufacturer': project_constants['scanner_manufacturer'],
		'xnat:mrScanData/fieldStrength': project_constants['field_strength']
	}

	# retrieve relevant fields from the mincheader
	pslabel = get_minc_field('vnmr:pslabel', MINC_filename)
	seqfil = get_minc_field('vnmr:seqfil', MINC_filename)
	lpe = get_minc_field('vnmr:lpe', MINC_filename)
	lpe2 = get_minc_field('vnmr:lpe2', MINC_filename)
	lro = get_minc_field('vnmr:lro', MINC_filename)
	nv = get_minc_field('vnmr:nv', MINC_filename)
	nv2 = get_minc_field('vnmr:nv2', MINC_filename)
	np = get_minc_field('vnmr:np', MINC_filename)
	orient = get_minc_field('vnmr:orient', MINC_filename)
	tr = get_minc_field('vnmr:tr', MINC_filename)
	te = get_minc_field('vnmr:te', MINC_filename)
	ti = get_minc_field('vnmr:ti', MINC_filename)

	# omitted xnat:mrScanData/startTime = time since it's in the session anyway
	# time must be of type xs:time

	# fov and matr don't allow 3D values
	# fov must have integer values, yet MINC has them in float values
	if pslabel is not None:
		scan_params['xnat:mrScanData/series_description'] = pslabel
	if lpe is not None and nv is not None:
		scan_params['xnat:mrScanData/parameters/voxelRes/x'] = float(lpe) / float(nv)
	if lpe2 is not None and nv2 is not None:
		scan_params['xnat:mrScanData/parameters/voxelRes/y'] = float(lpe2) / float(nv2)
	if lro is not None and np is not None:
		scan_params['xnat:mrScanData/parameters/voxelRes/z'] = float(lro) / (float(np) / 2)
	if orient is not None:
		scan_params['xnat:mrScanData/parameters/orientation'] = orient
	# These are not handled well because they aren't 3D and sometimes they're int, sometimes they're float.
	# if lpe is not None:
	# 	scan_params['xnat:mrScanData/parameters/fov/x'] = float(lpe)
	# if lpe2 is not None:
	# 	scan_params['xnat:mrScanData/parameters/fov/y'] = float(lpe2)
	# if nv is not None:
	# 	scan_params['xnat:mrScanData/parameters/matrix/x'] = int(nv)
	# if nv2 is not None:
	# 	scan_params['xnat:mrScanData/parameters/matrix/y'] = int(nv2)
	if tr is not None:
		scan_params['xnat:mrScanData/parameters/tr'] = float(tr)
	if te is not None:
		scan_params['xnat:mrScanData/parameters/te'] = float(te)
	if ti is not None:
		scan_params['xnat:mrScanData/parameters/ti'] = float(ti)
	if project_constants['flip_angle'] is not None:
		scan_params['xnat:mrScanData/parameters/flip'] = int(project_constants['flip_angle'])
	if seqfil is not None:
		scan_params['xnat:mrScanData/parameters/sequence'] = seqfil
	if project_constants['file_type'] is not None:
		scan_params['xnat:mrScanData/parameters/imageType'] = project_constants['file_type']

	return scan_params


def get_session_metadata(MINC_filename, session_name, project_constants):
	'''
	Summary:
		Extract session metadata from a MINC file (MINC_filename) and return a dictionary mapping XNAT XML (keys) to MINC metadata (values).
	Args:
		MINC_filename: A filename specifying the MINC file to upload.
		session_name: A string representing the well-formatted SPReD session name.
		project_constants: A dictionary containing metadata related to the project and upload.
	Returns:
		session_params: A dictionary containing relevant session metadata name value pairs for a given MINC file.
	'''

	# add constant key-values here
	session_params = {
		'xsiType': 'xnat:mrSessionData',
		'xnat:mrSessionData/visit_id': int(project_constants['visit_num']), 
		'xnat:mrSessionData/project': project_constants['project_name'],  # don't include this!  it generates a 403 for some reason
		'xnat:mrSessionData/label': session_name,
		'xnat:mrSessionData/scanner': project_constants['scanner'],
		'xnat:mrSessionData/scanner/manufacturer': project_constants['scanner_manufacturer'],
		'xnat:mrSessionData/modality':  project_constants['modality'],
		'xnat:mrSessionData/fieldStrength': project_constants['field_strength'],
		'xnat:mrSessionData/acquisition_site': project_constants['acquisition_site']
	}

	ni = float(get_minc_field('vnmr:ni', MINC_filename))
	nf = float(get_minc_field('vnmr:nf', MINC_filename))
	nfid = float(get_minc_field('vnmr:nfid', MINC_filename))
	nt = float(get_minc_field('vnmr:nt', MINC_filename))
	tr = float(get_minc_field('vnmr:tr', MINC_filename))
	etl = float(get_minc_field('vnmr:etl', MINC_filename))
	
	# duration isn't handled properly for some reason
	# this is a confirmed bug on XNAT's end
	# if ni is not None and nf is not None and nfid is not None and nt is not None and tr is not None and etl is not None:
	# 	duration_secs = int(ni) * int(nf) * int(nfid) * int(nt) * int(tr)  / int(etl)
	# 	# format duration value into xs:duration format
	# 	hours = math.floor(duration_secs / (60*60))
	# 	leftover = duration_secs - hours*60*60
	# 	minutes = math.floor(leftover / 60)
	# 	leftover = leftover - minutes*60
	# 	seconds = leftover
	# 	xs_duration = 'PT' + str(int(hours)) + 'H' + str(int(minutes)) + 'M' + str(int(seconds)) + 'S'
	# 	session_params['xnat:mrSessionData/duration'] = xs_duration
	
	coil = get_minc_field('vnmr:rfcoil', MINC_filename)
	if coil is not None:
		session_params['xnat:mrSessionData/coil'] = coil

	datetime = get_minc_field('vnmr:time_submitted', MINC_filename)
	if datetime is not None:
		date = datetime[0:8]
		date = insert(date, '-', 6)
		date = insert(date, '-', 4)
		# date should conform to YYYY-MM-DD format
		session_params['xnat:mrSessionData/date'] = date
		time = datetime[9:len(datetime)]
		time = insert(time, ':', 4)
		time = insert(time, ':', 2)
		# time should conform to HH:MM:SS format
		session_params['xnat:mrSessionData/time'] = time
	
	operator = get_minc_field('study:operator', MINC_filename)
	if operator is not None:
		session_params['xnat:mrSessionData/operator'] = operator

	return session_params


def get_subject_metadata(row, project_constants):
	'''
	Summary:
		Extracts subject metadata from a row from a pandas data frame (row) and creates a dictionary mapping XNAT XML (keys) to MINC metadata (values).
	Args:
		row: A row in a pandas data frame representing subject metadata.
		project_constants: A dictionary containing metadata related to the project and upload.
	Returns:
		subj_params: A dictionary containing subject metadata.
	'''

	subj_params = {
		'pi_firstname': project_constants['pi_firstname'],
		'pi_lastname': project_constants['pi_lastname']
	}
	
	if pd.notnull(row['Genotype']):
		subj_params['group'] = row['Genotype']
	if pd.notnull(row['dob']):
		subj_params['dob'] = row['dob']
	if pd.notnull(row['gender']):
		subj_params['gender'] = row['gender']
	if pd.notnull(row['handedness']):
		subj_params['handedness'] = row['handedness']
	if pd.notnull(row['race']):
		subj_params['race'] = row['race']
	if pd.notnull(row['ethnicity']):
		subj_params['ethnicity'] = row['ethnicity']
	if pd.notnull(row['weight']):
		subj_params['weight'] = row['weight']
	if pd.notnull(row['height']):
		subj_params['height'] = row['height']

	return subj_params


def init_log_file(project_constants):
	'''
	Summary:
		Creates a log file to record subjects that were successfully uploaded to braincode.
	Args:
		project_constants: A dictionary containing metadata related to the project and upload.
	Returns:
		spred_log_file: The log file handle.
	'''

	# log files will be found in this subdirectory.
	log_dir_name = 'logs'

	if not os.path.isdir(log_dir_name):
		os.makedirs(log_dir_name)

	todays_datetime = datetime.datetime.now()
	fname = log_dir_name + '/' + str(todays_datetime) + ' spred braincode upload.txt'
	spred_log_file = open(fname, 'w')
	spred_log_file.writelines('Uploaded the following subjects and related information into project: ' + project_constants['project_name'] + '\n')
	spred_log_file.writelines('Uploaded data to the following url: ' + project_constants['base_url'] + '\n')
	spred_log_file.writelines('Data was uploaded by user: ' + project_constants['username'] + '\n')
	spred_log_file.writelines('\n')
	spred_log_file.writelines('SPReD_id' + ',' + 'MINC_filename' + '\n')

	return spred_log_file


def init_project_constants():
	'''
	Summary:
		Initialize project constants used for the upload, such as the PI first and last name, constant scanning parameters, etc.  Decided against using collections.namedtuple().
	Returns:
		project_constants: A dictionary containing name:value pairs constant throughout the project.  This is preferred over global variables so that the module can potentially be imported down the line.
	'''

	project = 'PND11'
	site = 'HSC'

	username = raw_input('SPReD username:')
	password = raw_input('SPReD password:')

	session = requests.session()
	session.auth = (username, password)

	project_constants = {
		# project details
		'project': project,
		'site': site,
		'project_name': project + '_' + site + '_' + 'test',
		'visit_num': '01',
		'session_num': '01',
		'scan_num': '01',
		'resource_num': '01',
		'pi_firstname': 'Jason',
		'pi_lastname': 'Lerch',
		'acquisition_site': 'Mouse Imaging Centre (MICe)',
		'base_url': 'https://spreddev.braincode.ca/spred/data/archive/projects/',
		# scanning parameters
		'modality': 'MR',
		'field_strength': '7.0T',
		'scanner': 'Agilent 7T Animal System',
		'scanner_manufacturer': 'Agilent',
		'scan_type': 'T2 FSE 3D MICE EX-VIVO',
		'quality': 'usable',
		'file_type': 'MINC',
		'flip_angle': 90,  # will this always be 90?
		# logon info
		'username': username,
		'password': password,
		'session': 	session,
		# upload parameters
		'subject_metadata_file': 'SubjectMetadata.csv',
		'automatic_upload': False  # upload is interactive by default
	}

	return project_constants


def insert(original, new, pos):
	'''Inserts new (char) inside original (string) at pos (int).'''

	return original[:pos] + new + original[pos:]


def notify_user_of_success(subj_spred_ID, MINC_filename):
	'''Notifies the user of the successful creation of a collective subject, session, scan.'''

	print 'Successfully created subject: ' + subj_spred_ID


def print_to_logfile(subj_spred_ID, MINC_filename):
	'''Prints a line to the log file containing the SPReD_ID of the subject and the file associated with that subject.'''

	spred_log_file.writelines(','.join([subj_spred_ID, MINC_filename]) + '\n')


def upload_data(project_constants):
	'''
	Summary:
		Loop through folders of mouse strains, create subjects, sessions, scans, then upload the data.
	Args:
		project_constants: A dictionary containing metadata related to the project and upload.
	'''

	# Create data.frame-like structure using pandas containing subject metadata.
	subject_metadata = pd.read_table(filepath_or_buffer=project_constants['subject_metadata_file'], dtype={'Filename': str}, sep=',')

	# Loop through subject metadata, dispatch other methods calling web services to create subject, session, and scan.
	# Use status_code variable to keep track of whether the upload was successful.
	for index, row in subject_metadata.iterrows():

		subj_num = str(row['SubjNum'])
		subj_num = zero_pad_subj_num(subj_num)

		MINC_filename = row['Filename']
		subj_spred_ID = project_constants['project_name'] + '_' + subj_num
		session_name = subj_spred_ID + '_' +  project_constants['visit_num'] + '_' + 'SE' +  project_constants['session_num'] + '_' +  project_constants['modality']
		are_you_sure = ''

		if os.path.exists(MINC_filename):

			# Only accept 'y' and 'n' as valid user input for choosing to create a subject entity.
			# Don't give user option if it's an automatic upload.
			while are_you_sure != 'y' and are_you_sure != 'n':
				if project_constants['automatic_upload'] == True:
					are_you_sure = 'y'
				else:
					are_you_sure = raw_input("Create subject %s" % subj_spred_ID + " with file %s? (y/n): " % MINC_filename)
				if are_you_sure == 'y':
					create_subject(MINC_filename, subj_spred_ID, row, project_constants)
					create_session(MINC_filename, subj_spred_ID, session_name, project_constants)
					create_scan(MINC_filename, subj_spred_ID, session_name, project_constants)
				elif are_you_sure == 'n':
					pass
				else:
					print 'Please enter either y or n'

		else:

			print MINC_filename + ' does not exist!  No subject data uploaded.'


def upload_zip(file_names, zip_name, url, subj_spred_ID, action, project_constants):
	'''
	Summary:
		Uploads a zip file containing a bunch of files relating to a SPReD subject to a specific url.
	Args:
		file_names: A list of string paths to files.
		zip_name: A string specifying the zip file name to upload.
		url: A string specifying the location to upload files to.
		subj_spred_ID: The well-formatted SPReD ID.
		action: A string specifying whether distortion corrected files or stats volumes are being uploaded.
	Returns:
		Nothing.  Just uploads a zip file using the XNAT web services.
	'''

	# Create .zip file containing the all files in the file list to be uploaded.
	# Hopefully faster than uploading the uncompressed files, but has added step of zipping the files.
	with zipfile.ZipFile(file=zip_name, mode='a') as zf:
		for file_name in file_names:
			zf.write(filename=file_name, compress_type=zipfile.ZIP_DEFLATED)

	# Upload a file
	file_to_upload = {'file':open(zip_name, 'rb')}
	resp = project_constants['session'].post(url, files=file_to_upload, stream=True)
	check_HTTP_status_code(action, resp, subj_spred_ID)

	# Delete the .zip file created to upload once it's done uploading
	os.remove(zip_name)

	# Possibly return success/fail
	

def zero_pad_subj_num(subj_num):
	'''
	Summary:
		This method ensures that a subject number is 4 digits by zero-padding it if necessary.
	Args:
		subj_num: A string specifying the subject number.
	Returns:
		subj_num: The zero-padded subject number.
	'''

	for i in range(len(subj_num),4):
		subj_num = ''.join('0', subj_num)

	return subj_num


def main():
	'''
	Summary:
		The main control flow of the upload program.
	'''

	global spred_log_file

	project_constants = init_project_constants()

	# run script automatically or interactively
	if len(sys.argv) > 1:
		if sys.argv[1] == '-a':
			project_constants['automatic_upload'] = True

	spred_log_file = init_log_file(project_constants)

	upload_data(project_constants)

	spred_log_file.close()


if __name__ == '__main__':

	main()