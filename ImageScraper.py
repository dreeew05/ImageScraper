import Signature
import time
import pathlib
import os
import requests
import io
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

class BasePath():
    def getBasePath(self):
        return pathlib.Path().resolve()

class DownloadImage(BasePath):
    def __init__(self, FOLDER_NAME):
        self.FOLDER_NAME = FOLDER_NAME
    
    def getFolderPath(self):
        return f"{super().getBasePath()}\{self.FOLDER_NAME}"

    def createFolder(self):
        try:
            FOLDER_PATH = self.getFolderPath()
            if not os.path.isdir(FOLDER_PATH):
                os.makedirs(FOLDER_PATH)

        except OSError as e:
            print("Error: CANNOT CREATE FOLDER!")
    
    def downloadImage(self, filename, extension, picURL):
        success = False
        try:
            self.createFolder()

            imageContent = requests.get(picURL).content
            imageFile    = io.BytesIO(imageContent)
            image        = Image.open(imageFile)
            FILE_PATH    = f"{self.getFolderPath()}\{filename}.{extension}"
            print(FILE_PATH)

            with open(FILE_PATH, 'wb') as file:
                image.save(file, "PNG")
            success = True

        except Exception as e:
            print(f"Error downloading {filename}")

        return success

class ScrapeImagesFromNet():
    def __init__(self, ITEMS):
        self.ITEMS           = ITEMS
        self.DRIVER          = None
        self.imageDownloader = DownloadImage("sample")

    def initializeWebDriver(self):
        PATH        = Service("C:\Program Files (x86)\chromedriver\msedgedriver.exe")
        OPTIONS     = self.driverOptions()
        self.DRIVER = webdriver.Edge(service = PATH, options = OPTIONS)

    def driverOptions(self):
        options = Options()
        options.use_chromium = True
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        return options

    def getCleanQuery(self, RAW_QUERY):
        cleanQuery = RAW_QUERY.split(' ')
        if len(cleanQuery) == 1:
            return RAW_QUERY
        else:
            return "%20".join(f"{word}" for word in cleanQuery)

    def getLink(self, QUERY):
        LINK = f"https://www.google.com/search?q=+{QUERY}+&sxsrf=AJOqlzVmmNsdmEI6pBIIPDxl4Hb_IiGpRw:1675135394870&source=lnms&tbm=isch&sa=X&ved=2ahUKEwimw6XR7fD8AhXmt2MGHXUVCesQ_AUoAnoECAEQBA&cshid=1675135401347283&biw=1920&bih=965"
        return LINK

    def imageScraper(self, RAW_QUERY, IS_OPEN):
        if not IS_OPEN:
            self.initializeWebDriver()

        self.DRIVER.get(self.getLink(self.getCleanQuery(RAW_QUERY)))

        THUMBNAIL_CLASS_CODE = "Q4LuWd"
        thumbnails = self.DRIVER.find_elements(By.CLASS_NAME, THUMBNAIL_CLASS_CODE)

        ctr = 0
        for image in thumbnails:
            image.click()
            time.sleep(1)

            if(ctr >= self.ITEMS):
                break
            
            if self.getImageDetails(ctr):
                ctr += 1
    
    def getImageDetails(self, CTR):
        IMAGE_CLASS_CODE = "n3VNCb"
        images           = self.DRIVER.find_elements(By.CLASS_NAME, IMAGE_CLASS_CODE)
        isValid          = False

        for image in images:
            ATTRIBUTE = image.get_attribute('src')
            if ATTRIBUTE:
                if 'http' in ATTRIBUTE and 'png' in ATTRIBUTE:
                    if self.imageDownloader.downloadImage(f"something_{CTR}", "png", ATTRIBUTE):
                        isValid = True
                        break
        return isValid
                
    
    def closeDriver(self):
        self.DRIVER.quit()

class ApplicationDriver(BasePath):
    def __init__(self, TYPE):
        self.TYPE         = TYPE
        self.folderName   = None
        self.imageScraper = None

        self.start()
        # print(self.askForFileName(input()))
    
    def getFolderName(self):
        return self.folderName
    
    def setFolderName(self, folderName):
        self.folderName = folderName

    def start(self):
        ITEMS = self.askForNumberOfItems(int(input("Enter Number of Items: ")))
        self.imageScraper = ScrapeImagesFromNet(ITEMS)

        if self.TYPE == "single":
            self.imageScraper.imageScraper("Actress that won Oscars in 2015 png", False)
        elif self.TYPE == "multiple":
            self.multipleItems()

        self.imageScraper.closeDriver()
        print("----- Application Closed -----")
    
    def askForNumberOfItems(self, ITEMS):
        if ITEMS < 0:
            print("Error: INVALID INPUT!")
            return self.askForNumberOfItems(int(input("Enter Number of Items:")))
        else:
            return ITEMS

    def getTextFilePath(self, FILENAME):
        return f"{super().getBasePath()}\{FILENAME}.txt"

    def askForFileName(self, FILENAME):
        FILE_PATH = self.getTextFilePath()
        if not os.path.isfile(FILE_PATH):
            print("Error: FILE DOES NOT EXIST!")
            return self.askForFileName(input("Enter Filename: "))
        else:
            return FILE_PATH
    
    def multipleItems(self):
        FILE_PATH = self.askForFileName(input("Enter Filename: "))
        with open(FILE_PATH, 'r') as textFile:
            imageURLS = set()

            isOpen = False
            for line in textFile:
                self.imageScraper.imageScraper(f"famous person from {line}", isOpen)
                isOpen = True

### Code Execution       
if __name__ == "__main__":

    def askForType(response):
        if response.lower() not in ["single", "multiple"]:
            print("Error: INVALID INPUT!")
            return askForType(input("Enter input: "))
        else:
            ApplicationDriver(response.lower())
    
    askForType(input("Enter input: "))

