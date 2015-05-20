# ArcGIS Open Data - Socrata Synchronization Script (Python)

Script to synchronize a Socrata data site with ArcGIS Online.  It reads the Socrata data.json and creates registrations within ArcGIS Online and shares them to a group (most likely an Open Data group).

BONUS: This script will create a great looking thumbnail for your Socrata items as well!

The script also syncronizes the catalogs so if items are removed from the Socrata site, they are removed from ArcGIS Online.  Also, if updates/changes occur in the Socrata items, it will synchronize them.  Therefore, it is a good idea to run this as a scheduled task, perhaps, nightly.



## Basic Usage

  Create a folder in your content to store the registrations.  It is recommended to not put the registrations in an existing folder with other content in it.  You will need your folderId in the python script. You can get the folderId from here: http://<your-org>.maps.arcgis.com/sharing/rest/content/users/<Username>?f=pjson&token=<your token>
  Create a group that you will share your items to.  Make sure it is enabled for Open Data.  You will need your group id in the python script.

  To find your group ID, use this tool:
  https://developers.arcgis.com/javascript/jssamples/portal_getgroupamd.html

  You will want a stock thumbnail that you will want to use for your items.  This script will add the item title to the thumbnail.
  ![Thumbnail](https://raw.githubusercontent.com/sirws/OpenData-SocrataRegistrar/master/thumbnail/waopendatabridge.png)
  
  You will need to define a box using upper left and lower right coordinates (pixels) on the thumbnail.  This will define where to constrain the text on the image.
  You will need a font that you want to use to render the text on the image as well as the color and size.
  
## Instructions

  Fill out the config parameters at the top of the script and run it.

## Requirements

  This script requires ArcREST: https://github.com/Esri/ArcREST.
  The thumbnail generation requires the Python pillow library.  You can download it from here: https://pypi.python.org/pypi/Pillow/2.8.1
  
  This has been tested with the Python 2.7 release that comes with ArcGIS Desktop (32-bit).

## Resources

  ArcREST: https://github.com/Esri/ArcREST
  ArcPy: https://desktop.arcgis.com/en/desktop/latest/analyze/arcpy/a-quick-tour-of-arcpy.htm
  Python: https://www.python.org/about/gettingstarted/

## Issues

Find a bug or want to request a new feature?  Please let us know by submitting an issue.

## Contributing

Esri welcomes contributions from anyone and everyone. Please see our [guidelines for contributing](https://github.com/esri/contributing).

## Licensing
Copyright 2015 Esri

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the license is available in the repository's [license.txt]( https://raw.githubusercontent.com/sirws/ThumbnailBuilderUI/master/License.txt) file.

[](Esri Tags: ArcGIS Online Thumbnail Builder)
[](Esri Language: JavaScript)​