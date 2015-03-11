#! /usr/bin/python
import shutil
import requests

# download a file using url
def download_file(url, payload):
    # get a file-like object and copy it to a file. This will avoid reading the whole thing into memory at once.
    response = requests.get(url, auth=payload, stream=True) 
    with open('brain.nrrd', 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response    

if __name__ == '__main__':
    username = raw_input('SPReD username:')
    password = raw_input('SPReD password:')
    payload = (username, password)

    subject_name = 'PND11_HSC_test'

    # subject params
    subject_params = {
        'group': 'WT',
        'dob': 'WT',
        'gender': 'WT',
        'handedness': 'WT',
        'race': 'WT',
        'ethnicity': 'WT',
        'weight': 'WT',
        'height': 'WT',
    }

    # download
    url = 'http://10.30.13.240:8080/spred/data/projects/STRAIN/subjects/spred_S00427/experiments/spred_E00757/scans/scan1/resources/6735/files/brain.nrrd'
    download_file(url, payload)

    # create a subject
    url = 'https://spreddev.braincode.ca/spred/data/archive/projects/PND11_HSC_test/subjects/PND11_HSC_test_9998'
    requests.put(url, auth=payload)
    # create a session
    url = 'http://10.30.13.240:8080/spred/data/archive/projects/STRAIN/subjects/subject7/experiments/session1?xnat:mrSessionData/Date=02/03/15'
    requests.put(url, auth=payload)
    # create a scan
    url = 'http://10.30.13.240:8080/spred/data/archive/projects/STRAIN/subjects/subject7/experiments/session1/scans/scan1?xsiType=xnat:mrScanData&xnat:mrScanData/type=T1'
    requests.put(url, auth=payload)
    # Create resource
    url = 'http://10.30.13.240:8080/spred/data/archive/projects/STRAIN/subjects/subject7/experiments/session1/scans/scan1/resources/45?format=DICOM&content=T1_RAW'
    requests.put(url, auth=payload)
    # Upload a file
    file_to_upload = {'file':open('/home/sliang/Documents/rest_api/data/subject1/session1/scan1/brain.nrrd', 'rb')}
    url = 'http://10.30.13.240:8080/spred/data/archive/projects/STRAIN/subjects/subject7/experiments/session1/scans/scan1/resources/45/files/'
    requests.post(url, files=file_to_upload, auth=payload, stream=True)

    url = 'https://spreddev.braincode.ca/spred/data/archive/projects/PND11_HSC_test/subjects/PND11_HSC_test_0101/experiments/PND11_HSC_test_0101_01_SE05_MR/scans/scan1?xsiType=xnat:mrScanData&xnat:mrScanData/type=T1'
    resp = session.put(url, auth=payload)