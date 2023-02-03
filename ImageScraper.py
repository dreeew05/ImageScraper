import Signature
import time
import pathlib
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

class BasePath():
    def getBasePath(self):
        return pathlib.Path().resolve()

class ProgressBar():
    def __init__(self, TOTAL, PREFIX):
        self.TOTAL    = TOTAL
        self.PREFIX   = PREFIX
        self.SUFFIX   = 'Complete'
        self.DECIMALS = 1
        self.FILL     = '#'
        self.LENGTH   = 50

    def progressBar(self, ITERATION):
        try:
            percent      = ('{0:.' + str(self.DECIMALS) + 'f}').format(100 * (ITERATION / float(self.TOTAL)))
            filledLength = int(self.LENGTH * ITERATION // self.TOTAL)
            bar          = self.FILL * filledLength + '-' * (self.LENGTH - filledLength)
            print(f'\r{self.PREFIX} |{bar}| {percent}% {self.SUFFIX}', end='\r')
            if ITERATION == self.TOTAL:
                print()
        except ZeroDivisionError:
            pass

    def initializeProgressBar(self):
        print('\n')
        self.progressBar(0)

class DownloadImage(BasePath):
    def __init__(self, FOLDER_NAME):
        self.FOLDER_NAME    = FOLDER_NAME
        self.failedDownload = 0
    
    def getFailedDownload(self):
        return self.failedDownload
    
    def addFailedDownload(self):
        self.failedDownload += 1

    def getFolderPath(self):
        return f"{super().getBasePath()}\{self.FOLDER_NAME}"

    def createFolder(self):
        try:
            FOLDER_PATH = self.getFolderPath()
            if not os.path.isdir(FOLDER_PATH):
                os.makedirs(FOLDER_PATH)

        except OSError as e:
            print("Error: CANNOT CREATE FOLDER!")
    
    def downloadImage(self, FILE_PATH, picURL):
        try:
            response = requests.get(picURL, timeout=5)
            if response.status_code:
                fileMaker = open(FILE_PATH, 'wb')
                fileMaker.write(response.content)
                fileMaker.close()
        except requests.exceptions.Timeout:
            self.addFailedDownload()
            pass
        except Exception:
            self.addFailedDownload()
    
    def downloadByBatch(self, BUCKETS, EXTENSION, TOPIC):
        progressBar = ProgressBar(len(BUCKETS), "Downloading")
        self.createFolder()

        progressBar.initializeProgressBar()

        for ctr, picURL in enumerate(BUCKETS):
            filePath = f"{self.getFolderPath()}\{ctr}.{EXTENSION}"
            self.downloadImage(filePath, picURL)
            progressBar.progressBar(ctr + 1)
        
        self.getDownloadReport(BUCKETS, TOPIC)

    def getDownloadReport(self, BUCKETS, TOPIC):
        print(f"\n--------------- DOWNLOAD REPORT [{TOPIC}] ---------------\n")
        print(f"Failed Download: {self.getFailedDownload()}/{len(BUCKETS)}")

class ScrapeImagesFromNet():
    def __init__(self, ITEMS):
        self.ITEMS           = ITEMS
        self.DRIVER          = None
        self.bucket          = set()
        self.skips           = 0
        self.maxImages       = ITEMS
        self.failedSearch    = 0
        self.imageDownloader = None
        self.progressBar     = ProgressBar(ITEMS, "Scraping")

    def getItems(self):
        return self.ITEMS

    def getSkips(self):
        return self.skips
    
    def addSkip(self):
        self.skips += 1

    def getBucket(self):
        return self.bucket
    
    def clearBucket(self):
        self.bucket.clear()
    
    def addItemToBucket(self, ITEM):
        self.bucket.add(ITEM)

    def getMaxImages(self):
        return self.maxImages
    
    def addMaxImage(self):
        self.maxImages += 1
    
    def getFailedSearches(self):
        return self.failedSearch
    
    def setFailedSearches(self, FAILED_SEARCHES):
        self.failedSearch = FAILED_SEARCHES

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
    
    def scrollDown(self):
        self.DRIVER.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)

    def imageScraper(self, RAW_QUERY, IS_OPEN):
        if not IS_OPEN:
            self.initializeWebDriver()

        self.DRIVER.get(self.getLink(self.getCleanQuery(RAW_QUERY)))

        self.progressBar.initializeProgressBar()

        while len(self.getBucket()) + self.getSkips() < self.getMaxImages():
            # self.progressBar.progressBar(len(self.getBucket()))
            self.scrollDown()

            THUMBNAIL_CLASS_CODE = "Q4LuWd"
            thumbnails = self.DRIVER.find_elements(By.CLASS_NAME, THUMBNAIL_CLASS_CODE)

            if self.getCurrentHeight() > self.getEndHeight():
                self.progressBar.progressBar(self.getItems())
                self.setFailedSearches(self.getItems() - len(self.getBucket()))
                break

            for image in thumbnails[len(self.getBucket()) + self.getSkips() : self.getMaxImages()]:
                try:
                    image.click()
                    time.sleep(0.5)
                    self.getImageDetails()
                except:
                    continue
        
        self.imageDownloader = DownloadImage(RAW_QUERY)
        self.getSearchReport(RAW_QUERY)
        self.imageDownloader.downloadByBatch(self.getBucket(), "jpg", RAW_QUERY)
        self.clearBucket()

    def getImageDetails(self):
        IMAGE_CLASS_CODE = "n3VNCb"
        images           = self.DRIVER.find_elements(By.CLASS_NAME, IMAGE_CLASS_CODE)

        for image in images:
            ATTRIBUTE = image.get_attribute('src')
            if ATTRIBUTE:
                #and ('jpg' in ATTRIBUTE or 'jpeg' in ATTRIBUTE)
                if 'http' in ATTRIBUTE and 'encrypted' not in ATTRIBUTE:
                    self.addItemToBucket(ATTRIBUTE)
                    self.progressBar.progressBar(len(self.getBucket()))
                if ATTRIBUTE in self.getBucket():
                    self.addMaxImage()
                    self.addSkip()
                    break
    
    def getEndHeight(self):
        return self.DRIVER.execute_script("return document.documentElement.scrollHeight")
    
    def getCurrentHeight(self):
        return self.DRIVER.execute_script("return window.pageYOffset + window.innerHeight")

    def getSearchReport(self, TOPIC):
        print(f"\n--------------- SEARCH REPORT [{TOPIC}] ---------------\n")
        print(f"Failed Search: {self.getFailedSearches()}/{self.getItems()}")
                
    def closeDriver(self):
        self.DRIVER.quit()

class ApplicationDriver(BasePath):
    def __init__(self, TYPE):
        self.TYPE         = TYPE
        self.TOPIC        = None
        self.folderName   = None
        self.imageScraper = None

        self.start()
    
    def getFolderName(self):
        return self.folderName
    
    def setFolderName(self, folderName):
        self.folderName = folderName

    def start(self):
        ITEMS = self.askForNumberOfItems(int(input("Enter Number of Items: ")))
        self.setTopic(input("Enter topic: "))
        self.imageScraper = ScrapeImagesFromNet(ITEMS)

        if self.TYPE == "single":
            self.imageScraper.imageScraper(self.getTopic(), False)
        elif self.TYPE == "multiple":
            self.multipleItems()

        self.imageScraper.closeDriver()
        print("--------------- Application Closed ---------------")
    
    def askForNumberOfItems(self, ITEMS):
        if ITEMS < 0:
            print("Error: INVALID INPUT!")
            return self.askForNumberOfItems(int(input("Enter Number of Items: ")))
        elif ITEMS > 200:
            print("Error: INPUT MUST BE EQUAL OR LOWER THAN 200!")
            return self.askForNumberOfItems(int(input("Enter Number of Items: ")))
        else:
            return ITEMS

    def getTextFilePath(self, FILENAME):
        return f"{super().getBasePath()}\{FILENAME}.txt"

    def setTopic(self, TOPIC):
        self.TOPIC = TOPIC

    def getTopic(self):
        return self.TOPIC

    def askForFileName(self, FILENAME):
        FILE_PATH = self.getTextFilePath(FILENAME)
        if not os.path.isfile(FILE_PATH):
            print("Error: FILE DOES NOT EXIST!")
            return self.askForFileName(input("Enter filename: "))
        else:
            return FILE_PATH
    
    def multipleItems(self):
        FILE_PATH = self.askForFileName(input("Enter filename: "))
        with open(FILE_PATH, 'r') as textFile:

            isOpen = False
            for line in textFile:
                line = line.split("\n")[0]
                self.imageScraper.imageScraper(f"{self.getTopic()} {line}", isOpen)
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

