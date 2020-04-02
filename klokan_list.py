import csv
import re
import CdmApi
import requests_cache

requests_cache.install_cache('requests_cache')

# 3557: landgoedkaarten
# 6743, 2131: tmk
# Globes: 3748, 3769, 3727, 3832, 3866, 3811, 3853, 3790,3618,3794
IGNORE_LIST = [3748, 3769, 3727, 3832, 3866, 3811, 3853, 3790,
               3618, 3794]  # compound or single records that should be skipped
IGNORE_PAGE_TITLE_LIST = ['[indexkaart]']
NO_DEEPZOOM = [7244]
REF_BASE = 'http://imagebase.ubvu.vu.nl/cdm/ref/collection/krt/id/'
DZ_BASE = 'http://imagebase.ubvu.vu.nl/cdm/deepzoom/collection/krt/id/'

# Get all record ptrs
nick = 'krt'
ptrs = CdmApi.getAllPtr(nick)


def getGeoClassifications():
    classif = {}
    with open('classificatie_coords.csv', encoding='utf-8') as f:
        reader = csv.reader(f)
        for line in reader:
            names = line[0].replace('"', '').strip().split(';')
            name = names[len(names) - 1]

            bbox = line[2].replace('"', '').strip()
            code = line[4].replace('"', '').strip()

            if not code == '':
                classif[code] = {}
                classif[code]['bbox'] = bbox
                classif[code]['name'] = name
    return classif


def getBboxFromClassif(val):
    bbox = False
    if val != '':
        # http://cdm21033.contentdm.oclc.org/oai/oai.php?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:cdm21033.contentdm.oclc.org:krt/2821
        val = val.replace('81.4.210.110', '80.4.210.110')  # typo
        val = val.replace('80.273.3', '81.273.3')  # typo

        a = re.findall(r'80(?:\.\d+)+', val)
        if len(a) > 0:
            code = a[0]
            if code in classif:
                bbox = classif[code]['bbox']
    return bbox


def sanitize(val):
    # sanitizer for empty fields
    txt = ''
    if not isinstance(val, dict):
        txt = val.replace(';;', ';')
    return txt


def convert(md, pmd):
    # convert to csv row
    row = {}

    row['dpi'] = 300

    y = re.findall(r'\d{4}', md['ggc002'])
    if len(y) > 0:
        row['date'] = y[0]  # take first 4 consecutive numbers from JvU
    else:
        row['date'] = ''

    row['creator'] = sanitize(md['ggc006'])
    row['publisher'] = sanitize(md['ggc008'])
    ggc015 = sanitize(md['ggc015'])
    ggc011 = sanitize(md['ggc011'])
    ggc026 = sanitize(md['ggc026'])
    # -> Titelvariant (ggc015) + Annotatie geografische gegevens (ggc026) + Annotatie (ggc011)
    d = []
    if ggc015 != '':
        d.append('titelvariant: %s' % ggc015)
    if ggc011 != '':
        d.append('Annotatie: %s' % ggc011)
    if ggc026 != '':
        d.append('Annotatie geografische gegevens: %s' % ggc026)
    row['description'] = '; '.join(d)

    matches = re.findall(r'1:(\s{0,1}(?:\d|\.)*)', sanitize(md['ggc020']))
    if len(matches) > 0:
        row['scale'] = matches[0].replace('.', '')

    matches = re.findall(r'(\d{1,3}) x (\d{1,3}) cm', sanitize(md['ggc009']))
    if len(matches) == 1:
        row['physical_width'] = matches[0][0]
        row['physical_height'] = matches[0][1]
    else:
        row['physical_width'] = ''
        row['physical_height'] = ''

    bbox = getBboxFromClassif(sanitize(md['ggc053']))
    # "Europa;West Europa;Nederland","(O 3 - O 8 /N 54 - N 50)","8,50,3,54",445,80.4.210
    if bbox:
        c = bbox.split(',')
        row['north'] = c[3]
        row['south'] = c[1]
        row['east'] = c[0]
        row['west'] = c[2]

    ubvuid = sanitize(pmd['lok001']) if pmd else sanitize(md['lok001'])
    row['id'] = ubvuid
    row['filename'] = '%s.tif' % ubvuid

    row['title'] = '%s, uit: %s' % (pmd['title'], md['title']) if pmd else md['title']
    row['link'] = '%s%s' % (REF_BASE, pmd['dmrecord']) if pmd else '%s%s' % (REF_BASE, md['dmrecord'])

    if int(md['dmrecord']) not in NO_DEEPZOOM:
        row['viewer'] = '%s%s/show/%s' % (DZ_BASE, md['dmrecord'], pmd['dmrecord']) if pmd else '%s%s' % (
        DZ_BASE, md['dmrecord'])

    if (pmd and pmd['title'].lower() in IGNORE_PAGE_TITLE_LIST) or ubvuid == '':
        row = False

    return row


classif = getGeoClassifications()

# open csv
with open('ubvu_maps.csv', mode='w', newline='', encoding='utf-8') as csv_file:
    fieldnames = ['id', 'filename', 'link', 'viewer', 'title', 'date', 'description', 'creator', 'publisher',
                  'physical_width',
                  'physical_height', 'scale', 'dpi', 'north', 'south', 'east', 'west']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    # loop through ptrs and get metadata
    for ptr in ptrs:
        print(ptr)
        if ptr not in IGNORE_LIST:
            metadata = CdmApi.getMetadata(nick, ptr)
            if 'code' not in metadata:  # some broken items?
                print(metadata)
                if CdmApi.isCpd(nick, ptr):
                    cpd = CdmApi.getCpdPages(nick, ptr)
                    n = 0
                    if cpd['type'] != 'Monograph':
                        for page in cpd['page']:
                            pageptr = page['pageptr']
                            page_metadata = CdmApi.getMetadata(nick, pageptr)
                            row = convert(metadata, page_metadata)
                            if row:
                                writer.writerow(row)
                    else:
                        for node in cpd['node']['node']:  # specific case of tmk, could be deeper
                            if type(node['page']) is dict:  # what a shitty data structure
                                page = node['page']
                                pageptr = page['pageptr']
                                page_metadata = CdmApi.getMetadata(nick, pageptr)
                            row = convert(metadata, page_metadata)
                            if row:
                                writer.writerow(row)
                            else:
                                for page in node['page']:
                                    pageptr = page['pageptr']
                                    page_metadata = CdmApi.getMetadata(nick, pageptr)
                                    row = convert(metadata, page_metadata)
                                    if row:
                                        writer.writerow(row)
                else:
                    row = convert(metadata, False)
                    if row:
                        writer.writerow(row)
