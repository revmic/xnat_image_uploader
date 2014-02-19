#!/usr/bin/env python

from hcpxnat.interface import HcpInterface

idb = HcpInterface(config='/home/NRG/mhilem01/.hcpxnat_intradb.cfg')
idb.project = 'NKI'
sessions = idb.getSessions(project='NKI')

for s in sessions:
    idb.subject_label = idb.session_label = s.get('label')
    
    idb.setExperimentElement('xnat:mrSessionData', 'scanner', 'MRC35390')
    idb.setExperimentElement('xnat:mrSessionData', 'acquisition_site', 'Nathan Kline Institute for Psychiatric Research')

