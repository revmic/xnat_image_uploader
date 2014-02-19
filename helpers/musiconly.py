#!/usr/bin/env python

from hcpxnat.interface import HcpInterface

idb = HcpInterface(config='/home/NRG/mhilem01/.hcpxnat_intradb.cfg')
idb.project = 'NKI'
sessions = idb.getSessions(project='NKI')

for s in sessions:
    idb.subject_label = idb.session_label = s.get('label')
    scans = idb.getSessionScans()

    for s in scans:
        idb.scan_id = s.get('ID')
        sd = s.get('series_description')

        if 'MUSIC' in sd:
            print s
