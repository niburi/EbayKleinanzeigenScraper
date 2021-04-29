from bs4 import BeautifulSoup
import numpy as np
import requests 
import time 
import re 


class bcolors:
    """
    Background colors for tha cmdLine
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class StringParser:
    """
    Class to search an abstraction of a string in baseString
    """
    def __init__(self, stringValue):
        self.__stringValue = stringValue
        self.__stringValueLow = stringValue.lower()

    def chkString(self, searchword):
        """
        Searches a string or abstraction of the string in baseString
        """
        check = self.__clearString(self.__stringValueLow)
        check = check.split(' ')
        for word in check:
            if self.__levenshteinDistance(searchword, word) <= 2:
                return True

    def __clearString(self, string):
        """
        Clears a string from unneeded symbols
        """
        rep = {
                '!': ' ', 
                '?': ' ', 
                ',': ' ', 
                '.': ' ', 
                '(': ' ', 
                ')': ' '
            }
        pattern = re.compile("|".join(map(re.escape,rep.keys()))) 
        new_string = pattern.sub(lambda match: rep[match.group(0)], string)
        return new_string

    def __levenshteinDistance(self, seq1, seq2):
        """
        Implementation of the Levenshtein-Distance algorithm,
        return number equals needed operations of changes to make string 1 to string 2
        """
        size_x = len(seq1) + 1
        size_y = len(seq2) + 1
        matrix = np.zeros ((size_x, size_y))
        for x in range(size_x):
            matrix [x, 0] = x
        for y in range(size_y):
            matrix [0, y] = y

        for x in range(1, size_x):
            for y in range(1, size_y):
                if seq1[x-1] == seq2[y-1]:
                    matrix [x,y] = min(
                        matrix[x-1, y] + 1,
                        matrix[x-1, y-1],
                        matrix[x, y-1] + 1
                    )
                else:
                    matrix [x,y] = min(
                        matrix[x-1,y] + 1,
                        matrix[x-1,y-1] + 1,
                        matrix[x,y-1] + 1
                    )
        return (matrix[size_x - 1, size_y - 1])


class ArticleListScraper:
    """
    Search for an item in EbayKleinanzeigen
    """
    def __init__(self, requestword, header, timeWait = 30):
        self.__header = header 
        self.__timeWait = timeWait
        self.__requestword = requestword 
        self.__sideCounter = 1
        self.__nullLoad = False  
 
    def loadData(self):
        """
        Loading of all items from searchlist into cache
        """
        arrlist = []     
        while True:         
            url = f"https://www.ebay-kleinanzeigen.de/s-musikinstrumente/seite:{self.__sideCounter}/{self.__requestword}/k0c74"
            page = requests.get(url, headers=self.__header, allow_redirects=False)    
            page.close()
            soup = BeautifulSoup(page.text, 'html.parser')                    

            if soup.find("div", {"class": "pagination-pages"}) !=  None:
                itemlist = soup.find_all("article", {"class": "aditem"})
                for item in itemlist:    
                    try:
                        price_reg = self.__redefinePrice(item.find("p", {"class": "aditem-main--middle--price"}).text.strip())
                        arrlist.append( { 
                                            "main": str(item.find("a", {"class": "ellipsis"}).text.strip()),  
                                            "link": str(item.find("a", {"class": "ellipsis"}).attrs['href']),                                                                     
                                            "price": price_reg,
                                            "pushdate": str(item.find("div", {"class": "aditem-main--top--right"}).text.strip()),
                                            "text": str(item.find("p", {"class": "aditem-main--middle--description"}).text.strip())                           
                                        })
                    except Exception as e:
                        print(bcolors.FAIL + 'ArrayFail ' + url)                  
                self.__sideCounter += 1
                self.__nullLoad = False
            else: 
                if self.__nullLoad == True:
                    break 
                while True:                    
                    if self.__ipBanCheck(self.__sideCounter) == False:
                        self.__sideCounter += 1                                                       
                        break
                    else:
                        print(f'von Site gebannt, warte {self.__timeWait} sec...')
                        time.sleep(self.__timeWait)
                self.__nullLoad = True      
        return arrlist

    def __ipBanCheck(self, counter):
        """
        Check if you are banned by host
        """
        ipBan = False
        url = f"https://www.ebay-kleinanzeigen.de/s-musikinstrumente/seite:1/{self.__requestword}/k0c74"
        page = requests.get(url, headers=self.__header, allow_redirects=False)    
        page.close()
        soup = BeautifulSoup(page.text, 'html.parser')    
        if soup.find("div", {"class": "pagination-pages"}) ==  None:
            ipBan = True
        return ipBan

    def __redefinePrice(self, rawPrice):
        """
        Search for relevant nubmer in string
        """
        reg = re.findall("([0-9]*)", str(rawPrice))
        if not reg:
            price_reg = None
        else:
            price_reg = "".join([x for x in reg])
        return price_reg


class ArticleScraper():
    """
    Class scrapes article website an searches for keyword. 
    """
    def __init__(self, link, header, timeWait = 30):
        self.__header = header
        self.__link = link    
        self.__timeWait = timeWait

    def loadPage(self):
        """
        Loading page into cache, if response is emtpy the process will redo in 30 sec again. 
        """    
        url = f"https://www.ebay-kleinanzeigen.de/{self.__link}"    
        searchWordFound = False       
        while True:
            page = requests.get(url, headers=self.__header, allow_redirects=False)    
            page.close()
            soup = BeautifulSoup(page.text, 'html.parser') 
            try:             
                testX = str(soup.find("p", {"id": {"viewad-description-text"}}).text.strip()).lower()                                  
                if StringParser(testX).chkString('tausch') == True:
                    searchWordFound = True
                    print(bcolors.OKGREEN + 'URL: ' + url)
                    print(bcolors.OKGREEN + 'Tausch gefunden: ' + testX)                
                break
            except Exception as e:
                print(bcolors.FAIL + f'{self.__timeWait}sec wait, Error: ' + url)
                time.sleep(self.__timeWait)
        return searchWordFound





"""
Datadefinition
"""
timer = 30
header = {"User-Agent": 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}


"""
Scrapting logic
"""
cl_ebayArtikel = ArticleListScraper('jackson', header)
ebayArtikel = cl_ebayArtikel.loadData()
print(len(ebayArtikel))
for item in ebayArtikel:            
    if item['price'] != '' and float(item['price']) > 1000:
        print(bcolors.WARNING + 'Preis: ' + item['price'] + ', ' + item['main'] + ' Link: ' + item['link'])
        testclass = ArticleScraper(item['link'], header)   
        ergebnis = testclass.loadPage()
        print(ergebnis)         

#"test"
#abcXXXXXXXXXX