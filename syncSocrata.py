import arcpy, arcrest, json, urllib2, unicodedata, os, cStringIO, time
import logging
from arcrest.ags import MapService
from datetime import datetime

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

#koopBase = "http://geodata.wa.gov/koop/socrata/wa/"
koopBase = "http://koop.dc.esri.com/socrata/wastate/"
socrataURL = "http://data.wa.gov/data.json"
username = "<Your ArcGIS Online Username>"
password = "<Your ArcGIS Online Password>"
sh = None
agol = None
usercontent = None
folderId = "9b6d06bc333e479783b712fb08893eab" #folderId in username's content to place all of the item registrations
folderName = "data.wa.gov"
#you can get the folderId from here: http://<your-org>.maps.arcgis.com/sharing/rest/content/users/<Username>?f=pjson&token=<your token>
proxy_port = None
proxy_url = None
baseURL = None
defaultExtentForTables = "-124.775,45.413,-116.952,49.051" #default extent for non-spatial items
itemsToIgnore = {}
groupIds = "cdd16d5a3ba54b8193834aea8634053e" #groups to share to
sharingEveryone = True
sharingOrg = True
standardTags = ["data.wa.gov"]

### The following config variables are for creating thumbnails to be used for the item registrations
thumbnailImage = r"C:\Users\scot5141\Documents\GitHub\OpenData-SocrataRegistrar\thumbnail\waopendatabridge.png" #thumbnail you are going to place text on
fontsPath = r'C:\Users\scot5141\Documents\GitHub\OpenData-SocrataRegistrar\fonts' #path to your fonts for the thumbnail text
tnFont = "ARIALUNI.TTF" #font to be used to render item title on thumbnail - make sure font is in the %fontsPath% location.
tnULX = 0 #bounding box upper left x coordinate to place text within on image
tnULY = 100 #bounding box upper left y coordinate to place text within on image
tnLLX = 200 #bounding box lower left x coordinate to place text within on image
tnLLY = 133 #bounding box lower left y coordinate to place text within on image
tnAlign = "Center" #justification of text within the box
tnColor = "#404966" #color of text
tnSize = 18 #Max font size of text.  It will be shrunk until it fits with the box

def createThumbnail(itemText, fontSize, fontColor, textAlign, fontFace, ulx, uly, lrx, lry, bgImage):
  
  outputPath = arcpy.env.scratchFolder
  CHARS_PER_LINE = 0
  numLines = 0
  PIXELS_BETWEEN_LINES = 3

  astr = itemText
  FONT_SIZE = fontSize
  TEXT_COLOR = fontColor
  ALIGN = textAlign
  selectedFont = fontFace
  ULX = ulx
  ULY = uly
  LRX = lrx
  LRY = lry
  bgiItem = bgImage

  background = Image.open(bgiItem)
  arcpy.AddMessage("Using user uploaded background...")

  mergedImageName = "fgandbg.png"
  background = background.resize((200,133), Image.ANTIALIAS)
  background.save(os.path.join(outputPath, mergedImageName))

  fits = False #assume the text doesn't fit to start
  finalSize = FONT_SIZE #start with user specified fontsize and test for fit.  Shrink as necessary

  while not fits:
      words = astr.split()
      img = Image.open(os.path.join(outputPath, mergedImageName))
      MAX_W, MAX_H = img.size
      MAX_W = LRX - ULX
      MAX_H = LRY - ULY
      draw1 = ImageDraw.Draw(img)
      font1 = ImageFont.truetype(os.path.join(fontsPath,selectedFont), finalSize)
      w,h=draw1.textsize(astr, font=font1)
      arcpy.AddMessage("Width of whole line: " + str(w) + ".  Width of box: " + str(MAX_W))
      arcpy.AddMessage("Line height: " + str(h))
      
      MAX_LINES = MAX_H // (h+PIXELS_BETWEEN_LINES)
      arcpy.AddMessage("Based on this font and fontsize " + str(finalSize) + ", there can be " + str(MAX_LINES) + " lines in the box specified.")
      
      sentence = []
      lines = []
      sentenceStr = ""
      sentenceTest = ""
      for idx,word in enumerate(words):
          w,h=draw1.textsize(astr, font=font1)
          sentenceTest = " ".join(sentence)
          sentence.append(word)
          sentenceStr = " ".join(sentence)
          w,h=draw1.textsize(sentenceStr, font=font1)
          arcpy.AddMessage("Width of text: '" + sentenceStr + "' is "  + str(w) + " pixels.  Width of box: " + str(MAX_W))
          if (w > MAX_W):
              lines.append(sentenceTest)
              sentence = []
              sentence.append(word)
              arcpy.AddMessage("LINE CALCULATED: '" + sentenceTest + "' and new line started")
              arcpy.AddMessage("idx: '" + str(idx) + ", " + str(len(words)-1))
              if (idx == (len(words)-1)):
                  sentenceStr = " ".join(sentence)
                  lines.append(sentenceStr)
                  arcpy.AddMessage("FINAL LINE CALCULATED: '" + sentenceStr + "'")
          elif (idx == (len(words)-1)):
              lines.append(sentenceStr)
              arcpy.AddMessage("FINAL LINE CALCULATED: '" + sentenceStr + "'")

      if (MAX_LINES >= len(lines)):
          fits = True
      else:
          fits = False
          finalSize-=1
          FONT_SIZE=finalSize

  totalHeight = (len(lines) * (h+PIXELS_BETWEEN_LINES))-PIXELS_BETWEEN_LINES

  img = Image.open(os.path.join(outputPath, mergedImageName))
  MAX_W, MAX_H = img.size
  MAX_W = LRX - ULX
  draw = ImageDraw.Draw(img)
  font = ImageFont.truetype(os.path.join(fontsPath,selectedFont), FONT_SIZE)

  numLines = len(lines)

  current_h = ((LRY - ULY) - totalHeight)/2 + ULY
  arcpy.AddMessage("current_h: " + str(current_h))

  if (ALIGN == "Right"):
      for line in lines:
          w,h=draw.textsize(line, font=font)
          draw.text((ULX + (MAX_W - w), current_h), line, font=font, fill=TEXT_COLOR)
          arcpy.AddMessage("WRITING LINE TO IMAGE: '" + line + "' at insertion x location: " + str(current_h))
          current_h+=h+PIXELS_BETWEEN_LINES
  elif (ALIGN == "Center"):
      for line in lines:
          w,h=draw.textsize(line, font=font)
          draw.text((((LRX-ULX-w)/2), current_h), line, font=font, fill=TEXT_COLOR)
          arcpy.AddMessage("WRITING LINE TO IMAGE: '" + line + "' at insertion x location: " + str(current_h))
          current_h+=h+PIXELS_BETWEEN_LINES
  else:
      for line in lines:
          w,h=draw.textsize(line, font=font)
          draw.text((ULX, current_h), line, font=font, fill=TEXT_COLOR)
          arcpy.AddMessage("WRITING LINE TO IMAGE: '" + line + "' at insertion x location: " + str(current_h))
          current_h+=h+PIXELS_BETWEEN_LINES  
  img.save(os.path.join(outputPath, "outputimage" + ".png"))
  return os.path.join(outputPath, "outputimage" + ".png")
  #timestr = time.strftime("%Y%m%d-%H%M%S")
  #img.save(os.path.join(outputPath, "outputimage" + "-" + timestr + ".png"))
  #return os.path.join(outputPath, "outputimage" + "-" + timestr + ".png")


if __name__ == "__main__":
    try:
        logger = logging.getLogger('syncSocrata')
        timestr = time.strftime("%Y%m%d-%H%M%S")
        hdlr = logging.FileHandler('syncSocrata-' + timestr + '.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr) 
        logger.setLevel(logging.DEBUG)
        logger.info("STARTING PROCESS")
        data = json.load(urllib2.urlopen(socrataURL))

        if baseURL is None or baseURL == "":
          baseURL = "https://www.arcgis.com/sharing/rest"
          
        sh = arcrest.AGOLTokenSecurityHandler(username=username, password=password)
        admin = arcrest.manageorg.Administration(url=baseURL, securityHandler=sh)
        content = admin.content
        user = content.users.user()
        user.currentFolder = folderName #title
        agolContent = user.items
        itemsDictAGOL = {}
        for userItem in agolContent:
          if userItem.type == "Feature Service":
            if koopBase in userItem.url:
              itemsDictAGOL[userItem.url.split('/')[-3]] = { "id": userItem.id, "url": userItem.url }
            else:
              logger.info("Item: -" + userItem.title + "- does not appear to be an open data registration. You may want to remove it from the folder.")
          else: 
            logger.info("Item: -" + userItem.title + "- is not a Feature Service or an open data registration. You may want to remove it from the folder.")
        logger.info(str(len(itemsDictAGOL)) + " items found in ArcGIS Online")
        
        #for socrataId, AGOLItem in itemsDictAGOL.iteritems():
        #  print socrataId + ": " + AGOLItem["id"]

        allSocrataData = {}
        for dataset in data["dataset"]:
          allSocrataData[dataset['identifier'].split('/')[-1]] = koopBase + dataset['identifier'].split('/')[-1] + "/FeatureServer/0"

        logger.info(str(len(allSocrataData)) + " items found in data.wa.gov")
        diff = set(itemsDictAGOL.keys())-set(allSocrataData.keys()) #sets

        theIDs = []
        for n in diff:
          theIDs.append(itemsDictAGOL[n]["id"])
        if len(theIDs) > 0:
          logger.info("Deleting: " + ",".join(theIDs))
          user.deleteItems(",".join(theIDs))
        
        #For testing if you would like to pause after deleting files
        #raw_input("Press Enter to continue...")
        
        for dataset in data["dataset"]:
            usercontent = agolContent
            itemParams = None
            itemParams = arcrest.manageorg.ItemParameter()
            itemParams.title = dataset["title"]
            itemParams.description = str(unicodedata.normalize('NFKD', dataset['description']).encode('ascii','ignore')) + '<br/><a href="' + dataset['landingPage'] + '">' + dataset['landingPage'] + '</a>' + '<br/>Created: ' + dataset['issued'] + '<br/>Modified : ' + dataset['modified'] + '<br/>Update by syncSocrata script at: ' + str(datetime.now())
            itemParams.snippet = dataset["title"]
            itemParams.accessInformation = "Creative Commons Attribution License"
            itemParams.type = "Feature Service"
            allTags = []
            if dataset.has_key("keywords"):
              allTags = standardTags + dataset["keywords"]
            else:
              allTags = standardTags
            if dataset.has_key("theme"):
              allTags =  allTags + dataset["theme"]

            itemParams.tags = ",".join(allTags)

            itemParams.url = koopBase + dataset['identifier'].split('/')[-1] + "/FeatureServer/0"
            
            try:
              logger.info(itemParams.url)
              data2 = json.load(urllib2.urlopen(itemParams.url))

              if not "type" in data2:
                retryAttempts = 0
                # drop the index and retry
                idxdropresponse = urllib2.urlopen(koopBase + dataset['identifier'].split('/')[-1] + "/drop")
                htmlresponse = idxdropresponse.read()
                logger.info("Index Drop Response: " + htmlresponse)
                while retryAttempts < 10:
                  data2 = json.load(urllib2.urlopen(itemParams.url))
                  if not "type" in data2:
                    logger.debug("trying again (" + str(retryAttempts) + ")")
                    #data2 = json.load(urllib2.urlopen(itemParams.url))
                  else:
                    logger.debug("retry successful")
                    retryAttempts = 10
                  retryAttempts += 1
                
              if "type" in data2:
                logger.info("Service appears to be valid...")
                itemParams.typeKeywords = ["Data", "Service", "Feature Service", "ArcGIS Server", "Feature Access"]
                if data2["type"] == "Feature Layer":
                    itemParams.extent = str(data2["extent"]["xmin"]) + "," + str(data2["extent"]["ymin"]) + "," + str(data2["extent"]["xmax"]) + "," + str(data2["extent"]["ymax"])
                else:
                    itemParams.extent = defaultExtentForTables
                    itemParams.title += " (Non-Spatial)"
                path = createThumbnail(dataset["title"], tnSize, tnColor, tnAlign, tnFont, tnULX, tnULY, tnLLX, tnLLY, thumbnailImage)
                itemParams.thumbnail = path
                itemExists = False
                existId = None
                for itemId, url in itemsDictAGOL.iteritems():
                  if url["url"] == itemParams.url:
                    existId = url["id"]
                    
                if existId:
                  item = content.getItem(existId)
                  item.shareItem(groups=groupIds, everyone=sharingEveryone, org=sharingOrg)
                  res = item.userItem.updateItem(itemParameters=itemParams)
                  logger.info("UPDATING FEATURE SERVICE: " + itemParams.title + " - " + itemParams.url)
                else:
                  res = user.addItem(itemParameters=itemParams, overwrite=True, folder=folderId)
                  user.shareItems(items=res.id,groups=groupIds,everyone=sharingEveryone,org=sharingOrg)
                  logger.info("ADDING FEATURE SERVICE: " + itemParams.title + " - " + itemParams.url)
              elif "errors" in data2[0]:
                logger.error("Error in registering item with Koop")
              else:
                logger.error("Error in registering item with Koop - logging")
            except Exception as inst:
              logger.error("SKIPPING DATASET: " + dataset['identifier'].split('/')[-1])
        logger.info("PROCESS COMPLETE")    
    except ValueError, e:
        print str(e)

