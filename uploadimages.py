#!/usr/bin/env python

from hcpxnat.interface import HcpInterface
from optparse import OptionParser
from datetime import datetime
import subprocess as sp
import logging
import dicom
import json
import sys
import os

## OPTION PARSER ##
parser = OptionParser(usage='\n(DICOM):' +
    '\npython uploadimages.py --dicom -s /data/intradb/ftp/NKI/DICOM -H intradb.humanconnectome.org -p PROJ -a nki.das' +
    '\n(NIFTI):' +
    '\npython uploadimages.py --nifti -s /data/intradb/ftp/NKI/NIFTI -H intradb.humanconnectome.org -p PROJ -m map.json')
parser.add_option("-d", "--dicom", action="store_true", dest="dicom", default=False)
parser.add_option("-n", "--nifti", action="store_true", dest="nifti", default=False)
parser.add_option("-s", "--source", action="store", type="string", dest="source",
    help='Source of images to upload. ')
parser.add_option("-H", "--hostname", action="store", type="string", dest="host",
    help='Hostname where images are to be uploaded')
parser.add_option("-p", "--project", action="store", type="string", dest="project",
    help='XNAT project shortname')
parser.add_option("-a", "--anon-script", action="store", type="string", dest="anon",
    help='Optional anonymization script used by DicomRemap')
parser.add_option("-m", "--scan-map", action="store", type="string", dest="map",
    help='Json mapping all files to an XNAT series_desc.\n' +
         'If there is no mapping defined, assumes directories match series_desc.')
parser.add_option("-u", "--gen-uid", action="store_true", dest="uid", default=False,
    help='Optional flag that will generate an SOPInstanceUID for DICOMs')
(opts, args) = parser.parse_args()
if not (opts.dicom or opts.nifti):
    opts.print_help()
    sys.exit()
if opts.nifti and not opts.map:
    print "A json file containing the scan-file mapping must be provided. (-m)"
    opts.print_help()
####################

### LOG SETUP ###
log = logging.getLogger('uploadimages')
log.setLevel(logging.DEBUG)
dt = datetime.strftime(datetime.today(), '%Y%m%d')
imgtype = 'dicom' if opts.dicom else 'nifti'
fh = logging.FileHandler('log/'+imgtype+'upload-'+dt+'.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)
#################

### LOAD SCAN MAP ###
if opts.map:
    with open(opts.map) as data:
        scan_file_map = json.load(data)
#####################

SCRIPTDIR = os.path.abspath(os.path.curdir) + '/'
DCMADDRESS = 'dicom://' + opts.host + ':8104/HCP'
#idb = HcpInterface(config='/home/NRG/mhilem01/.hcpxnat_intradb_dev.cfg')
idb = HcpInterface(config='/data/intradb/home/hileman/.hcpxnat_intradb.cfg')
idb.url = 'https://' + opts.host

def get_subjects_from(directory):
    """
    Assumes the source directory contains subject labels
    """
    os.chdir(directory)
    dirs = [d for d in os.listdir(os.curdir)
                if os.path.isdir(os.path.join(os.curdir, d))]
    subs = []
    for d in dirs:
        if d.isdigit():
            subs.append(d)
    return subs

def process_dicoms(sub_label, dirname, fnames):
    """
    Recursively processes each subject directory,
    adding the directory name as a subject label
    to each DICOM resource header within the dir
    """
    msg = "Updating DICOM headers for subject " + sub_label + " ..."
    log.info(msg)
    print msg

    for f in fnames:
        file_path = os.path.join(opts.source, dirname, f)

        if not os.path.isfile(file_path):
            continue

        print ' '*4 + file_path
        log.info('--> ' + file_path)
        try:
            dcm = dicom.read_file(file_path)
            if opts.uid:
                dcm.SOPInstanceUID = generate_uid()
                print "SOPInstanceUID: " + dcm.SOPInstanceUID
            dcm.StudyDescription = opts.project
            dcm.PatientName = sub_label
            dcm.PatientID = sub_label
            #dcm[0x0008,0x0018].value = dcm[0x0002,0x0003].value
            #print dcm
            dcm.save_as(file_path)
        except IOError:
            msg = "No such file or dirctory: " + file_path
            print msg
            log.error(msg)
        except ImportError:
            msg = "Import error when reading DICOM."
            print msg
            log.error(msg)
            print sys.exc_info()[0]
            sys.exit()

def generate_uid():
    return '01.' + str(datetime.strftime(datetime.today(), '%Y%m%d%S%f'))

def upload_dicom():
    """
    Upload DICOM with updated headers using DicomRemap tool.
    """
    command = [SCRIPTDIR + 'DicomBrowser/bin/DicomRemap','-d', SCRIPTDIR + opts.anon,
                '-o', DCMADDRESS, opts.source]
    print command
    log.info('Starting DICOM upload from ' + opts.source + ' to ' + DCMADDRESS)
    try:
        proc = sp.call(command)
    except OSError:
        log.error('OSError - Check DicomRemap and subject/source directory')
        print "OSError Exception:\n"
        print "Make sure your paths to DicomRemap, the script, " + \
              "and subject directory are correct."
        print proc.returncode
    log.info('Finished DICOM upload')

def upload_nifti():
    """
    """
    if not idb.subjectExists():
        msg = idb.subject_label + " doesn't exist on " + idb.url + ". SKIPPING ..."
        print msg
        log.warning(msg)
        return

    scans = idb.getSessionScans()

    # Loops through intradb scans and json map and uploads files where series_desc matches
    for scan in scans:
        for mapping in scan_file_map:
            if scan['series_description'] == mapping['series_desc']:
                msg = "Scan: " + scan['ID'] + " - " + scan['series_description']
                print msg
                log.info(msg)
                idb.scan_id = scan.get('ID')
                log.info('Creating NIFTI resource')
                idb.createScanResource('NIFTI')

                for f in mapping['files']:
                    abspath = os.path.join(opts.source, idb.subject_label, f)
                    if not os.path.isfile(abspath):
                        msg = abspath + " does not exist for " + idb.subject_label
                        print msg
                        log.warning(msg)
                        continue
                    idb.scan_resource = 'NIFTI'
                    log.info("Putting NIFTI resource - " + abspath)
                    idb.putScanResource(abspath)

if __name__ == "__main__":
    subjects = get_subjects_from(opts.source)
    idb.project = opts.project

    if opts.dicom:
        msg = "== Applying anonymize script: " + opts.anon
        print msg
        log.info(msg)
        for sub in subjects:
            os.path.walk(sub, process_dicoms, sub)
        upload_dicom()
    elif opts.nifti:
        for sub in subjects:
            idb.subject_label = sub
            idb.session_label = sub
            msg = "\n== Uploading NIFTI for subject " + sub + "..."
            print msg
            log.info(msg)
            upload_nifti()
    else:
        print "Either --dicom or --nifti must be specified."
        parser.print_help()
        sys.exit(-1)
