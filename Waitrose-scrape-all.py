#-------------------------------------------------------------------------------
# Purpose:     scraping data from Waitrose website
# Author:      Nomi Hadar
# Created:     08/11/2015
#-------------------------------------------------------------------------------

import time
import csv
import os
import sys
import re

from lxml import html
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

###############################################################################
#   constants 
###############################################################################

MARKET_NAME = "Waitrose "

#initial url
INITIAL_URL = 'http://www.waitrose.com'

#path to ouptput file
OUTPUT_PATH = "."

#xpathes queries
xpath_mainCategories = '//div[@class = "mega-menu "]'
xpath_amountInCategory = '//h4[@class="current"]'
#xpath_subCategories = '//div[@id = "supernavSidebar_Mixed"]//a'
xpath_product = '(//div[@class="m-product-cell"])[position()>{}]'
xpath_title = '//a[@class="m-product-open-details"]/text()'
xpath_weight = '//div[@class="m-product-volume"]/text()'
xpath_price = '//span[@class="price trolley-price"]/text()'
xpath_deal = '//a[@class="offer"]//text()'

#number of page scrolls in each page load
NUM_OF_SCROLLS = 20

#titels of output file
TITELS = ("Category","Product", "Weight", "Price", "Deal")

###############################################################################

###############################################################################
#   FUNCTION get_all_products_in_page
#   input: web driver
#   operation: scrolls page to bootom and gets all products in the page
#   return value: a list of all products, where product is a HTML element
###############################################################################
def get_all_products_in_page(driver):

    #for scrolling down
    elem = driver.find_element_by_tag_name("body")
    
    allProducts = []#output

    #while we have not got to bottom of page
    while True:
       
        #scroll page down in order to load it with more products
        for i in range(NUM_OF_SCROLLS):
            elem.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.2) #wait for loading

        #find any products beyond the ones we already have
        xpath = xpath_product.format(len(allProducts))
        products = driver.find_elements_by_xpath(xpath)

        #if there are no more products, stop
        if not products:
            break

        #get product's html source and add it to all products list
        for product in products:

            try:
                htmlSource = product.get_attribute('innerHTML')
                productHtml = html.fromstring(htmlSource) #create a HTML element
            except Exception as e:
                print str(e)

            #append product to the list
            allProducts.append(productHtml)

    return allProducts

###############################################################################
#   FUNCTION getDetails
#   input: producta as html element, xpath query and index
#   operation: makes a xpath query on product
#   return value: xpath text result encoded in UTF-8
###############################################################################
def getDetails(product, xpath, i):

    try:
        detail = product.xpath(xpath)[i].strip() #strip removes spaces
    except Exception as e:
        print "in get details", str(e)
        detail = "error"

    return u''.join(detail).encode('utf-8')#encode data to UTF-8 before


###############################################################################
#   FUNCTION toUTF
#   input: string
#   return value: input string encoded in UTF-8
###############################################################################
def toUTF(string):
    return u''.join(string).encode('utf-8')


#open browser
print "-----> opening driver"
driver = webdriver.Firefox()
time.sleep(1)

#open initial page in browser
driver.get(INITIAL_URL)
print "-----> starts scraping", MARKET_NAME, "website\n"

###############################################################################
#   get main categories links
###############################################################################

#find all links for main categories
mainCategoriesBar = driver.find_element_by_xpath(xpath_mainCategories)

#convert main categories to HTML
htmlSource = mainCategoriesBar.get_attribute('innerHTML')
mainCategoriesHTML = html.fromstring(htmlSource)

#extract main categories links
urls = mainCategoriesHTML.xpath('//a/@href')
mainCategUrls = [INITIAL_URL + url.strip() for url in urls]

#extract main categories names
names = mainCategoriesHTML.xpath('//a/text()')
mainCategNames = [name.strip() for name in names]

#remoce 2 first categories (offers and favourites)
mainCategUrls = mainCategUrls[2:]
mainCategNames = mainCategNames[2:]

###############################################################################
#   create a directeory and output file 
###############################################################################

#create an output directory if directory does not exist
directory = time.strftime("%d-%m-%Y")
if not os.path.exists(OUTPUT_PATH + directory):
    os.makedirs(OUTPUT_PATH + directory)

#create an output csv file
try:
    #file name
    fileName = MARKET_NAME + time.strftime("%d-%m-%Y") + '.csv'

    #open file
    dataFile = open(OUTPUT_PATH + directory + "\\" + fileName, 'wb')

except IOError as e:
    print str(e)
    sys.exit(1)

#file writer
wr = csv.writer(dataFile, quoting=csv.QUOTE_ALL)

#write titles
wr.writerow(TITELS)

###############################################################################
#   main code - extract products and write to file
###############################################################################

#for each link for main category
for categoryUrl, categoryName in zip(mainCategUrls, mainCategNames):
    
    print "\nNow in", categoryName, "category"
    
    #open current url
    driver.get(categoryUrl)
    time.sleep(1)
    
    #get total number of products in page
    str = driver.find_element_by_xpath(xpath_amountInCategory).text
    amount = int(re.search(r'\d+', str).group())

    #get a list of all products in current cateogry
    #(where product is a HTML element)
    allProducts = get_all_products_in_page(driver)
   
    numRows = 0 #num rows written in file
   
    #for each product in current category
    for product in allProducts:
        
        #declare variabels
        title, weight, price, deal = '', '', '', ''
        
        try:
            #get product name
            titleLs = product.xpath(xpath_title)
            if titleLs:
                 title = toUTF(titleLs[0].strip())
            
            #get product weight
            weightLs = product.xpath(xpath_weight)
            if weightLs:
                weight = toUTF(weightLs[0].strip())
            
            #try all kind of prices 
            priceLs = product.xpath(xpath_price)
           
            #case it is a regular price
            if priceLs:
                price = toUTF(priceLs[0].strip())
        
            #get deal
            dealLs = product.xpath(xpath_deal)
            if dealLs:
                deal = toUTF(dealLs[0].strip())
            
        except Exception as e:    
            print "failed to add product:", name
            print str(e), "\n"
            continue
            
        #creat a tuple from product's data
        row = (categoryName, title, weight, price, deal)
        
        #write row to output file
        wr.writerow(row)
    
        #increment number of rows
        numRows +=1

    print categoryName, "category:", numRows, "out of ", amount, \
            "products where written to file"
    

###############################################################################
#   clean sources 
###############################################################################

#close browser and file
dataFile.close()
driver.close()


