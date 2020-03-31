# georeferencer_upload
Scripts to upload metadata and images to Klokan

## Conversion notes

    id: Your own unique identifier for each map image. The IDs of images or records in your existing cataloging / publishing system. Later you can use these IDs you supply in our APIs to identify your maps to construct links, etc.
        -> ubvuid
    filename: Name of the uploaded file. It should not contain spaces, nor commas. If you have uploaded images in directories, then this column in the spreadsheet must contain also the name of the folder where the image is located. For example: M001.tiff folder "atlas" will have filename "atlas/M001.tif" - ideally case sensitive.
        -> <ubvuid>.tif zoals ze opgeslagen zijn in het archief

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

    north: Latitude of the north-most point
    south: Latitude of the south-most point
    east: Longitude of the east-most point
    west: Longitude of the west-most point
        -> uit de lokale classificatie, zie classificatie_coords.csv. Dit is dus een zeer ruwe schatting, maar mogelijk nuttig.
