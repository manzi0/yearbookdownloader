# yearbookscraper
<<<<<<< HEAD
Simple tool to help download Chinese provincial yearbook data from government websites. Supports downloading data presented in excel workbook, HTML table, PDF, or image formats.
=======
Simple tool to help download Chinese provincial yearbook data from government websites. Supports downloading data presented in excel workbook, HTML table, PDF, or graphical formats.

Run the get_tjnj_interative.py file to start program.


USAGE INSTRUCTIONS
- Download URLs are pre-loaded for tested yearbooks. URLs for additional yearbooks may be provided by the user but download may or may not work depending on the format of the yearbook.
- Files are downloaded in whatever format is available. This may include excel, image, or pdf files depending on the yearbook. Yearbooks provided in the form of HTML tables are scraped as csv. Some provinces provide yearbooks in zip file format. Zip file downloads are not supported for security reasons and as these are easily downloaded manually.
- The number of files found for each yearbook will be displayed and must be confirmed by the user before download. A file check will be performed after each yearbook download completes. Pages where no relevant table or file was found can be listed. If all necessary files have been downloaded, enter 'n' to finish current yearbook download. If any relevant files are missing, select 'y' to re-attempt download.
- If a download is interrupted or incomplete, the download can be restarted with the same parameters. The program will identify missing files and offer to download them.
- Depending on your IP address, a proxy may be necessary to download files. Some websites are only accessible from Chinese IPs. Please provide a proxy if necessary.

>>>>>>> 0f2b756 (Updated to interactive version)
