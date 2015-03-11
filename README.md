---
output: html_document
---
# NonDicomBatchUpload Documentation

## Introduction

This is some brief documentation for the work I did for the Mouse Imaging Centre (MICe) and the Ontario Brain Institute (OBI).  The OBI is working on a big data solution for neuroscience data, called Brain-CODE, and it was my job to upload approximately 50 GB of mouse brain imaging data from MICe into the imaging side of Brain-CODE.  The imaging side of [Brain-CODE][1] uses the Stroke Patient Recovery Research Database (SPReD).

Right now it uses an R script to generate the subject metadata, then uses a Python script to map the subject metadata to the XNAT XML schema, to extract other metadata, and to structure HTTP PUT web service calls to the XNAT REST API. 

## Workflow

1. Specify folders that you want to upload along with their corresponding gf files and strain label (label used as a prefix for all the data files -- e.g. NLGN) in the GenerateSubjectMetadata.R script.  Run the script.

2. Move the .csv file that is produced to the same directory where you will run the Python script.

3. Modify globals in the Python script to specify the project name, site code, SPReD url, and folders that you want to upload to SPReD.

4. Run the Python script, supplying your username and password, and it will upload subjects, sessions, scans, and the associated files to the project and site at the specified SPReD url.

## Development Notes

- the difference between `study:start_time` and `vnmr:time_submitted` is unknown
	- these fields are contained in the MINC header; it is unclear whether they would map to SPReD session and scan, respectively
	- for MICe's purposes, there will only ever be 1 scan per session, so it doesn't matter for this implementation
- fov in XNAT must be of type integer, yet MINC header had these as type float
	- to convert to mm, had to multiply by 10
- the fov and matrix fields in XNAT are two dimensional (only x and y), however, all images at MICe are 3 dimensional without slices
	- what is the best way of handling this behaviour?  possibly supply z dimension in number of frames
- duration goes up to a maximum of around 16 hours
- extending this module to work with any non-DICOM data would be difficult
	- however, this script is still a useful code skeleton for people with their own non-DICOM data
	- the python script assumes a number of things:
		1. there is only 1 project, 1 session, 1 scan, 1 resource, and 1 file associated with a subject
		2. metadata is generated with a separate R script, and must conform to a specific schema
	- all of the QA is specific to MICe

<!---
References
-->
[1]: https://braincode.ca/