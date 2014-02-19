#!/usr/bin/env python

from hcpxnat.interface import HcpInterface

idb = HcpInterface(config='/home/NRG/mhilem01/.hcpxnat_intradb.cfg')
idb.project = 'NKI'
sessions = idb.getSessions(project='NKI')

mapping = {
    #'REST_645': 'rfMRI',
    #'MPRAGE_SIEMENS': 'T1w',
    #'REST_1400': 'rfMRI',
    #'REST_CAP': 'rfMRI',
    #'CHECKERBOARD_645': 'tfMRI',
    #'CHECKERBOARD_1400': 'tfMRI',
    #'BREATH_HOLD_1400': 'tfMRI',
    #'DIFF_137_AP': 'dMRI'
    #'MPRAGE_SIEMENS_DEFACED': 'T1w',
    #'MPRAGE_SIEMENS_MUSIC ONLY': 'T1w',
    #'FLAIR - ch32 iPAT2 -CLINICAL': 'T2w',
    'MPRAGE': 'T1w'
}

for s in sessions:
    idb.subject_label = idb.session_label = s.get('label')
    scans = idb.getSessionScans()
    print "\nModifying series_desc for session " + idb.session_label

    for s in scans:
        idb.scan_id = s.get('ID')
        sd = s.get('series_description')
        
        if not sd in mapping:
            print "+++ " + sd + " not in series desc mapping. SKIPPING..."
            continue

        print " %s %s - Scan type %s --> %s" % \
        (s.get('ID'), sd, s.get('type'), mapping[sd])

        idb.setScanElement('xnat:mrScanData', 'type', mapping[sd])
