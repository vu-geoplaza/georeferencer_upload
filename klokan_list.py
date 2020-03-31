import csv
import re
import CdmApi, pprint
import requests_cache
requests_cache.install_cache('requests_cache')
# Get all record ptrs
nick = 'krt'
ptrs = CdmApi.getAllPtr(nick)

def sanitize(val):
    # sanitizer for empty fields
    txt=''
    if not isinstance(val, dict):
        txt=val.replace(';;',';')
    return txt

def convert(md, pmd):
    # convert to csv row
    row={}

    row['dpi'] = 300

    y = re.findall(r'\d{4}', md['ggc002'])
    if len(y)>0:
        row['date'] = y[0] # take first 4 consecutive numbers from JvU
    else:
        row['date'] = ''

    row['creator'] = sanitize(md['ggc006'])
    row['publisher'] = sanitize(md['ggc021'])
    matches=re.findall(r'1:(?:\d|\.)*',sanitize(md['ggc020']))
    if len(matches)>0:
        row['scale']=matches[0]

    matches=re.findall(r'(\d{1,3}) x (\d{1,3}) cm', sanitize(md['ggc009']))
    if len(matches)==1:
        row['physical_width'] = matches[0][0]
        row['physical_height'] = matches[0][1]
    else:
        row['physical_width'] = 0
        row['physical_height'] = 0

    if pmd:
        row['id'] = pmd['lok001']
        row['file'] = '%s.tif' % pmd['lok001']
        row['title'] = '%s, uit: %s' % (pmd['title'], md['title'])
        row['link'] = 'http://imagebase.ubvu.vu.nl/cdm/ref/collection/krt/id/%s' % pmd['dmrecord']
        row['viewer']='http://imagebase.ubvu.vu.nl/cdm/deepzoom/collection/krt/id/%s/show/%s' % (md['dmrecord'], pmd['dmrecord'])
    else:
        row['dmrecord'] = md['dmrecord']
        row['file'] = '%s.tif' % md['lok001']
        row['title'] = md['title']
        row['link'] = 'http://imagebase.ubvu.vu.nl/cdm/ref/collection/krt/id/%s' % md['dmrecord']
        row['viewer']='http://imagebase.ubvu.vu.nl/cdm/deepzoom/collection/krt/id/%s' % (md['dmrecord'])
    return row


# open csv
with open('ubvu_maps.csv', mode='w', newline='', encoding='utf-8') as csv_file:
    fieldnames = ['dmrecord', 'title', 'file', 'link', 'dpi', 'viewer', 'date', 'creator', 'publisher', 'scale', 'physical_width', 'physical_height']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    # loop through ptrs and get metadata
    for ptr in ptrs:
        print(ptr)
        metadata = CdmApi.getMetadata(nick, ptr)
        if 'code' not in metadata: # some broken items?
            print(metadata)
            if CdmApi.isCpd(nick, ptr):
                cpd = CdmApi.getCpdPages(nick, ptr)
                n = 0
                if cpd['type'] != 'Monograph':
                    for page in cpd['page']:
                        pageptr = page['pageptr']
                        page_metadata = CdmApi.getMetadata(nick, pageptr)
                        writer.writerow(convert(metadata, page_metadata))
                else:
                    for node in cpd['node']['node']: # specific case of tmk, could be deeper
                        if type(node['page']) is dict: # what a shitty data structure
                            page=node['page']
                            pageptr = page['pageptr']
                            page_metadata = CdmApi.getMetadata(nick, pageptr)
                            writer.writerow(convert(metadata, page_metadata))
                        else:
                            for page in node['page']:
                                pageptr = page['pageptr']
                                page_metadata = CdmApi.getMetadata(nick, pageptr)
                                writer.writerow(convert(metadata, page_metadata))
            else:
                writer.writerow(convert(metadata, False))

    # convert needed fields

    # write to csv
