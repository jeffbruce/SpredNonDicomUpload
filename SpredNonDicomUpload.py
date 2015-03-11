# !/usr/bin/python

import math
import numpy as np
import pandas as pd
import pdb
import requests
import subprocess
import sys
import traceback


# TO DO
# - test that the code works for a folder
# - handle partial uploads (e.g. what happens if an upload fails part way through?  do you just repeat it?)
# - handle reconstructed images
#	- most places would download the MINC files, convert to NIfTI then analyze with FSL
# - integrate the metadata creation script (currently written in R) to be done in Python instead
# 	- low priority


# SET GLOBALS

# constants used in the upload which will need to be changed for subsequent uploads
project = 'PND11'
site = 'HSC'
project_name = project + '_' + site + '_' + 'test'
visit_num = '01'
session_num = '01'
scan_num = '01'
modality = 'MR'
field_strength = '7.0T'
acquisition_site = 'Mouse Imaging Centre (MICe)'
scanner = 'Agilent 7T Animal System'
scanner_manufacturer = 'Agilent'
scan_type = 'T2 FSE 3D MICE EX-VIVO'
quality = 'usable'
file_type = 'MINC'
flip_angle = 90  # will this always be 90?
resource_num = '01'
pi_firstname = 'Jason'
pi_lastname = 'Lerch'
# logon info 
username = raw_input('SPReD username:')
password = raw_input('SPReD password:')
credentials = (username, password)
# SPReD info
base_url = 'https://spreddev.braincode.ca/spred/data/archive/projects/'
session = requests.session()
# .csv subject metadata file created in R with GenerateSubjectMetadata.R
subject_metadata_file = 'SubjectMetadata.csv'


def check_HTTP_status_code(action, response):
	'''Check that the web service request was successful.  
	If it wasn't, exit program and print out error details.'''

	if response.status_code == 401:
		print 'You probably entered an invalid username or password.'

	if response.status_code != 200 and response.status_code != 201:
		print 'Error processing subject: ' + subj_SPReD_ID
		print 'Problem related to action: ' + action
		print 'Generated an HTTP Response Error Code: ' + str(response.status_code)
		# traceback.print_tb(traceback, limit=3)  # prints to stderr
		sys.exit()


def create_scan(MINC_filename, subj_SPReD_ID, session_name):
	'''Creates a scan in SPReD, including the upload of any associated files.'''

	# add constant key-values here
	scan_params = {
		# 'xsiType': 'xnat:mrScanData',
		# 'xnat:mrScanData/type': scan_type,  # double check that this is the format SPReD wants
		# 'xnat:mrScanData/quality': quality,
		# 'xnat:mrScanData/scanner': scanner,
		# 'xnat:mrScanData/scanner/manufacturer': scanner_manufacturer,
		# 'xnat:mrScanData/fieldStrength': field_strength
	}

	resource_params = {
		'format': file_type,
		'content': scan_type
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
	# if pslabel is not None:
	# 	scan_params['xnat:mrScanData/series_description'] = pslabel
	# if lpe is not None and nv is not None:
	# 	scan_params['xnat:mrScanData/parameters/voxelRes/x'] = float(lpe) / float(nv)
	# if lpe2 is not None and nv2 is not None:
	# 	scan_params['xnat:mrScanData/parameters/voxelRes/y'] = float(lpe2) / float(nv2)
	# if lro is not None and np is not None:
	# 	scan_params['xnat:mrScanData/parameters/voxelRes/z'] = float(lro) / (float(np) / 2)
	# if orient is not None:
	# 	scan_params['xnat:mrScanData/parameters/orientation'] = orient
	# # These are not handled well because they aren't 3D and sometimes they're int, sometimes they're float.
	# # if lpe is not None:
	# # 	scan_params['xnat:mrScanData/parameters/fov/x'] = float(lpe)
	# # if lpe2 is not None:
	# # 	scan_params['xnat:mrScanData/parameters/fov/y'] = float(lpe2)
	# # if nv is not None:
	# # 	scan_params['xnat:mrScanData/parameters/matrix/x'] = int(nv)
	# # if nv2 is not None:
	# # 	scan_params['xnat:mrScanData/parameters/matrix/y'] = int(nv2)
	# if tr is not None:
	# 	scan_params['xnat:mrScanData/parameters/tr'] = float(tr)
	# if te is not None:
	# 	scan_params['xnat:mrScanData/parameters/te'] = float(te)
	# if ti is not None:
	# 	scan_params['xnat:mrScanData/parameters/ti'] = float(ti)
	# if flip_angle is not None:
	# 	scan_params['xnat:mrScanData/parameters/flip'] = int(flip_angle)
	# if seqfil is not None:
	# 	scan_params['xnat:mrScanData/parameters/sequence'] = seqfil
	# if file_type is not None:
	# 	scan_params['xnat:mrScanData/parameters/imageType'] = file_type

	# Create scan
	url = base_url + project_name + '/subjects/' + subj_SPReD_ID + '/experiments/' + session_name + '/scans/scan' + str(int(scan_num))
	resp = session.put(url, auth=credentials, params=scan_params)

	pdb.set_trace()

	check_HTTP_status_code('creating scan', resp)

	# Create resource
	url = base_url + project_name + '/subjects/' + subj_SPReD_ID + '/experiments/' + session_name + '/scans/scan' + str(int(scan_num)) + '/resources/' + str(int(resource_num))
	resp = session.put(url, auth=credentials, params=resource_params)

	check_HTTP_status_code('creating resource', resp)

	# Upload a file
	file_to_upload = {'file':open(MINC_filename, 'rb')}
	url = base_url + project_name + '/subjects/' + subj_SPReD_ID + '/experiments/' + session_name + '/scans/scan' + str(int(scan_num)) + '/resources/' +  str(int(resource_num)) + '/files/'
	resp = session.post(url, files=file_to_upload, auth=credentials, stream=True)

	check_HTTP_status_code('creating file', resp)


def create_session(MINC_filename, subj_SPReD_ID, session_name):
	'''Creates a session in SPReD.'''

	# add constant key-values here
	session_params = {
		'xsiType': 'xnat:mrSessionData',
		# 'xnat:mrSessionData/visit_id': visit_num, 
		# # 'xnat:mrSessionData/project': project,  # won't recognize this for some reason
		# 'xnat:mrSessionData/label': session_name
		# 'xnat:mrSessionData/scanner': scanner,
		# 'xnat:mrSessionData/scanner/manufacturer': scanner_manufacturer,
		'xnat:mrSessionData/modality': modality 
		# 'xnat:mrSessionData/fieldStrength': field_strength,
		# 'xnat:mrSessionData/acquisition_site': acquisition_site
	}

	# ni = float(get_minc_field('vnmr:ni', MINC_filename))
	# nf = float(get_minc_field('vnmr:nf', MINC_filename))
	# nfid = float(get_minc_field('vnmr:nfid', MINC_filename))
	# nt = float(get_minc_field('vnmr:nt', MINC_filename))
	# tr = float(get_minc_field('vnmr:tr', MINC_filename))
	# etl = float(get_minc_field('vnmr:etl', MINC_filename))
	
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
	
	# coil = get_minc_field('vnmr:rfcoil', MINC_filename)
	# if coil is not None:
	# 	session_params['xnat:mrSessionData/coil'] = coil

	# datetime = get_minc_field('vnmr:time_submitted', MINC_filename)
	# if datetime is not None:
	# 	date = datetime[0:8]
	# 	date = insert(date, '-', 6)
	# 	date = insert(date, '-', 4)
	# 	# date should conform to YYYY-MM-DD format
	# 	session_params['xnat:mrSessionData/date'] = date
	# 	time = datetime[9:len(datetime)]
	# 	time = insert(time, ':', 4)
	# 	time = insert(time, ':', 2)
	# 	# time should conform to HH:MM:SS format
	# 	session_params['xnat:mrSessionData/time'] = time
	
	# operator = get_minc_field('study:operator', MINC_filename)
	# if operator is not None:
	# 	session_params['xnat:mrSessionData/operator'] = operator

	url = base_url + project_name + '/subjects/' + subj_SPReD_ID + '/experiments/session' + str(int(session_num))
	resp = session.put(url, auth=credentials, params=session_params)

	pdb.set_trace()

	check_HTTP_status_code('creating session', resp)


def create_subject(MINC_filename, subj_SPReD_ID, row):
	'''Creates a subject in SPReD.
	row is a row in a pandas data frame.'''

	subj_params = {
		# 'pi_firstname': pi_firstname,
		# 'pi_lastname': pi_lastname
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

	url = base_url + project_name + '/subjects/' + subj_SPReD_ID
	resp = session.put(url, auth=credentials, params=subj_params)

	pdb.set_trace()

	check_HTTP_status_code('creating subject', resp)


def get_minc_field(field_name, MINC_filename):
	'''Calls a subprocess to extract a field's value from a MINC file (MINC_filename).
	The mincinfo command is a specific command offered by MINC tools.'''

	value = None

	try:
		value = subprocess.check_output(["mincinfo", "-attvalue", field_name, MINC_filename])
		value = value.rstrip()
	except subprocess.CalledProcessError:
		pass

	return value


def insert(original, new, pos):
	'''Inserts new (char) inside original (string) at pos (int).'''
	return original[:pos] + new + original[pos:]


def upload_data():
	'''Loop through folders of mouse strains and create individual subjects to upload.'''

	# create data.frame like structure containing subject metadata
	subject_metadata = pd.read_table(filepath_or_buffer=subject_metadata_file, dtype={'Filename': str}, sep=',')

	# loop through subject metadata and call web service to create subject, session, and scan
	for index, row in subject_metadata.iterrows():

		subj_num = str(row['SubjNum'])

		# need to pad the subject number with zeros because pandas
		subj_num = zero_pad_subj_num(subj_num)

		MINC_filename = row['Filename']
		subj_SPReD_ID = project_name + '_' + subj_num
		session_name = subj_SPReD_ID + '_' + visit_num + '_' + 'SE' + session_num + '_' + modality

		create_subject(MINC_filename, subj_SPReD_ID, row)

		create_session(MINC_filename, subj_SPReD_ID, session_name)

		create_scan(MINC_filename, subj_SPReD_ID, session_name)


def zero_pad_subj_num(subj_num):
	'''Left pad the subject number with an appropriate number of zeros to fit the SPReD naming convention.
	subj_num is a string, not an integer.'''

	for i in range(len(subj_num),4):
		subj_num = '0' + subj_num

	return subj_num


def main():

	upload_data()


if __name__ == '__main__':
	main()
