import arcpy, arcrest, json, urllib2, unicodedata
from arcrest.ags import MapService
from datetime import datetime

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import os
import json
import urllib, cStringIO

koopBase = "http://geodata.wa.gov/koop/socrata/wa/"
socrataURL = "http://data.wa.gov/data.json"
username = "<Your ArcGIS Online Username"
password = "<Your ArcGIS Online Password"
sh = None
agol = None
usercontent = None
folderId = "4eaf10c38338433cb29048e748eeb23b" #folderId to place all of the registration
proxy_port = None
proxy_url = None
baseURL = None
defaultExtentForTables = "-124.775,45.413,-116.952,49.051" #default extent for non-spatial items
itemsToIgnore = {}
groupIds = "9fcc2802b3d2423795f37c384213301e" #groups to share to
sharingEveryone = True
sharingOrg = True
fontsPath = r'C:\Users\scot5141\Documents\GitHub\OpenData-SocrataRegistrar\fonts' #path to your fonts for the thumbnail text
standardTags = ["data.wa.gov"]
thumbnailImage = r"C:\Users\scot5141\Documents\GitHub\OpenData-SocrataRegistrar\waopendatabridge.png" #thumbnail you are going to place text on
tnFont = "ARIALUNI.TTF" #font to be used to render item title on thumbnail
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


if __name__ == "__main__":
    try:
        data = json.load(urllib2.urlopen(socrataURL))
        print data["dataset"][0]["identifier"]

        if baseURL is None or baseURL == "":
          baseURL = "https://www.arcgis.com/sharing/rest"
          
        sh = arcrest.AGOLTokenSecurityHandler(username=username, password=password)
        agol = arcrest.manageorg.Administration(url=baseURL, securityHandler=sh)
        agolContent = agol.content.getUserContent(username=username,folderId=folderId)

        itemsDictAGOL = {}
        for userItem in agolContent['items']:          
          itemsDictAGOL[userItem["url"].split('/')[-3]] = { "id": userItem["id"], "url": userItem["url"] }
        print str(len(itemsDictAGOL)) + " items found in ArcGIS Online"
        
        for socrataId, AGOLItem in itemsDictAGOL.iteritems():
          print socrataId + ": " + AGOLItem["id"]

        allSocrataData = {}
        for dataset in data["dataset"]:
          allSocrataData[dataset['identifier'].split('/')[-1]] = koopBase + dataset['identifier'].split('/')[-1] + "/FeatureServer/0"

        print str(len(allSocrataData)) + " items found in data.wa.gov"
        diff = set(itemsDictAGOL.keys())-set(allSocrataData.keys()) #sets
        
        for n in diff:
          usercontent = content.usercontent(username=username)
          if folderId is None or folderId == "":
              res = agolContent.deleteItem(item_id=userItem[n])
          else:
              res =  agolContent.deleteItem(item_id=userItem[n], folder=folderId)
          print n
        
        for dataset in data["dataset"]:
            usercontent = agol.content.usercontent(username)
            if isinstance(usercontent, arcrest.manageorg.administration._content.UserContent):
                pass
            itemParams = arcrest.manageorg.ItemParameter()
            itemParams.title = dataset["title"]
            itemParams.description = str(unicodedata.normalize('NFKD', dataset["description"]).encode('ascii','ignore')) + '<br/><a href="' + dataset["landingPage"] + '">' + dataset["landingPage"] + '</a>' + '<br/>Created: ' + dataset["issued"] + '<br/>Modified : ' + dataset["modified"] + '<br/>Update by registerSocrata script at: ' + str(datetime.now())
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
              data2 = json.load(urllib2.urlopen(itemParams.url))
              itemParams.typeKeywords = ["Data", "Service", "Feature Service", "ArcGIS Server", "Feature Access"]
              if data2["type"] == "Feature Layer":
                  itemParams.extent = str(data2["extent"]["xmin"]) + "," + str(data2["extent"]["ymin"]) + "," + str(data2["extent"]["xmax"]) + "," + str(data2["extent"]["ymax"])
              else:
                  itemParams.extent = defaultExtentForTables
                  itemParams.title = itemParams.title + " (Non-Spatial)"
              path = createThumbnail(dataset["title"], tnSize, tnColor, tnAlign, tnFont,tnULX,tnULY,tnLLX,tnLLY, thumbnailImage)
              itemParams.thumbnail = path
              itemExists = False
              existId = None
              for itemId, url in itemsDictAGOL.iteritems():
                if url["url"] == itemParams.url:
                  existId = url["id"]
                  
              if existId:
                content = agol.content
                adminusercontent = content.usercontent()
                item = content.item(existId)
                res = adminusercontent.updateItem(itemId=existId, updateItemParameters=itemParams, folderId=item.ownerFolder)
                item.shareItem(groups=groupIds, everyone=sharingEveryone, org=sharingOrg)
                print "UPDATING FEATURE SERVICE: " + itemParams.url
              else:
                res = usercontent.addItem(itemParameters=itemParams, overwrite=True, folder=folderId)
                itemToUpdate = agol.content.item(res["id"])
                itemToUpdate.shareItem(groups=groupIds,everyone=sharingEveryone,org=sharingOrg)
                print "ADDING FEATURE SERVICE: " + itemParams.url
            except Exception as inst:
              print "SKIPPING DATASET: " + dataset['identifier'].split('/')[-1]

    except ValueError, e:
        print str(e)

