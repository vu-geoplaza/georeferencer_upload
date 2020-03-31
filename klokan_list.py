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
        row['dmrecord'] = pmd['dmrecord']
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

'''
    link (IMPORTANT): URL of the map page in your library website (where you want to send people). On this page can be easily placed the inteligent backlink to Georeferencer service
        -> contentdm reference URL
        
    viewer: URL to the zoomable viewer of the scan on the web (if different from the landing page "link" above).
        -> link naar de Deepzoom viewer
        
    catalog: URL to the catalog, with detailed authoritative metadata record (if different from the landing page "link" above)
        -> leeg, de contentdm reference url dient hiervoor, bevat alle informatie die in WMS staat
        
    title (IMPORTANT): Title of the map (if known).
        -> in geval van series is dit nu: <bladtitel>, uit: <serietitel>
        
    date (IMPORTANT): Date of what is depicted on the map, ie. not the publishing date;
    either in YYYY or YYYY-MM-DD format
    alternatively for a range of dates: date_from and date_to  (it is possible to fill only the "date" column or only the range of dates using the combination of "date_from" and "date_to" column!)
        -> de eerste 4 getallen in Jaar van Uitgave, indien niet aanwezig: leeg
           ranges komen maar weinig voor en lastig automatisch op te pikken.
           
    pubdate: Date of the publication (if known) - a supplement to 'date' to recognize reprints and school atlas maps from true old maps.
    alternatively for a range of dates: pubdate_from and pubdate_to
        -> Hebben wij volgens mij niet, facsimiles hebben meestal de originele datum
        
    description: Description of what is on the map as a simple text, ie. not HTML, not entity escaped
        -> TODO
         
    creator: Name of the cartographer, surveyor, etc.; NOT "anonymous"
        -> (Co)auteurs ggc006
        
    contributor: Name of the engraver; NOT "anonymous"
        --> Hebben wij dit???
    publisher: Name of the publisher; NOT "anonymous"
        -> Drukker ggc021
        
    physical_width: Physical width of the map in centimeters
    physical_height: Physical height of the map in centimeters
        -> test regex '(\d{1,3}) x (\d{1,3}) cm'. Als deze maar 1 keer voorkomt is dit <width> x <height> cm
            Staat vaak meer dan 1 vermelding vanwege verschillende formaten of gevouwen, die zijn nu dus helemaal weggelaten
        
    scale: Metric scale denominator; ie. if the scale is 1 meter : 10,000 meters, the value is 10000
        -> Mathematische gegevens, ggc020, gefilterd op string regex 1:(\d|\.)*
        
    dpi: The information about scans - for precise estimation of scale in the MapAnalyst
        -> Alles zou op 300dpi gescand moeten zijn
'''


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
