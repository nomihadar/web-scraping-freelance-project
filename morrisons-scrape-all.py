#-------------------------------------------------------------------------------
# Purpose:     scraping data from Morrisons website
# Author:      Nomi Hadar
# Created:     20/07/2015
#-------------------------------------------------------------------------------

import selenium
import time
import csv
import os
import sys
import re

from lxml import html
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

############ Constants ################################

MARKET_NAME = "Morrisons "

#initial url
INITIAL_URL = 'https://groceries.morrisons.com/webshop/getCategories.do?tags'

#path to ouptput file
OUTPUT_PATH = "C:\\Users\\michal\\Documents\\akivaBerger\\Supermarkets\\Morrisons\\Data\\"

#xpathes queries
xpath_mainCategories = '//div[@id = "supernavSidebar_Grocery"]//a'
xpath_button = '//button[@value= "text" and @title= "Text view"]'
xpath_product = '(//div[@class="listProductWrap"])[position()>{}]'
xpath_title = '//h4[@class="productTitle"]/a/text()'
xpath_weight = '//h4[@class="productTitle"]/a/span/text()'
xpath_price = '//div[@class="typicalPrice"]/h5/text()'
xpath_now_price = '//div[@class="typicalPrice"]//span[@class="nowPrice"]/text()'
xpath_price_from = '//p[@class="typicalPrice"]//text()'
xpath_deal = '//p[@class="onOffer"]/a/span/text()'

#number of page scrolls in each page load
NUM_OF_SCROLLS = 20

#titels of output file
TITELS = ("Category","Product", "Weight", "Price", "Deal")

#######################################################

#   input: web driver
#   operation: scrolls page to bootom and gets all products in the page
#   return value: a list of all products, where product is a HTML element
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

#   input: producta as html element, xpath query and index
#   operation: makes a xpath query on product 
#   return value: xpath text result encoded in UTF-8 
def getDetails(product, xpath, i):
    
    try:
        detail = product.xpath(xpath)[i].strip() #strip removes spaces
    except Exception as e:
        print str(e)
        detail = "error"
    
    return u''.join(detail).encode('utf-8')#encode data to UTF-8 before

#create an output directory if directory does not exist
directory = time.strftime("%d-%m-%Y")
if not os.path.exists(OUTPUT_PATH + directory):
    os.makedirs(OUTPUT_PATH + directory)   

#open browser
print "-----> opening driver"
driver = webdriver.Firefox()
time.sleep(1)

print "-----> starts scraping\n"

#open initial page in browser
driver.get(INITIAL_URL)

#find all links for main categories
mainCategories = driver.find_elements_by_xpath(xpath_mainCategories)

#add main categories to categoriesInfo
#elements in categoriesInfo are tuples of the format:
#(category url, category name, number of products in category)
categoriesInfo = []
for category in mainCategories:
    
    try:
        #get category link
        categoryUrl = category.get_attribute('href')
        
        #get number of products in category
        numProducts = int(re.search(r'([0-9]+)', category.text).group(0))
        
        #get category name
        categoryName = re.sub(r'\([0-9]+\)','', category.text).strip()
        categoryName = u''.join(categoryName).encode('utf-8')
        
        #append category to categories
        categoriesInfo.append((categoryUrl, categoryName, numProducts))
        
    except Exceptionas as e:
        print "failed to get one of main categories", str(e)
        sys.exit(1)    
    
#create an output csv file
try:
    #file name 
    fileName = MARKET_NAME + time.strftime("%d-%m-%Y") + '.csv'
    
    #open file
    dataFile = open(OUTPUT_PATH + directory + "\\" + fileName , 'wb')
    
except IOError as e:
    print str(e)
    sys.exit(1)

#file writer
wr = csv.writer(dataFile, quoting= csv.QUOTE_ALL)

#write titles
wr.writerow(TITELS)

#for each link for main category
for categoryInfo in categoriesInfo:
    
    #open current url in the browser
    try:
        driver.get(categoryInfo[0])
        time.sleep(1)
    
        #change to text view by pressing the text view button
        #(saves the image loading time)
        textView_button = driver.find_element_by_xpath(xpath_button).click()
 
        #get a list of all products in current cateogry
        #(where product is a HTML element)
        allProducts = get_all_products_in_page(driver)
        
    except Exception as e:
        print "failed to extract data from category:", categoriesInfo[1]
        print str(e), "\n"
        continue
    
    numRows = 0 #num rows written in file
  
    #for each product in current category
    for product in allProducts:
       
        #get product name
        name = getDetails(product, xpath_title, 0)
        
        #get product weight
        weight = getDetails(product, xpath_weight, 0) 
        
        #if there is a new price (now price) get it 
        if product.xpath(xpath_now_price):
            price = getDetails(product, xpath_now_price, 0)
        
        #else if there is a regular price get it
        elif product.xpath(xpath_price):
            price = getDetails(product, xpath_price, 0)
        
        #else price is "from price"
        elif product.xpath(xpath_price_from):
            price = "From " + getDetails(product, xpath_price_from, 2)
        
        #get a deal if exists else leave deal empty
        if product.xpath(xpath_deal):
            deal = getDetails(product, xpath_deal, 0) 
        else: 
            deal = ''
            
        #creat a tuple from product's data
        row = (categoryInfo[1], name, weight, price, deal)
        
        #if one of the queries failed, print its name and continue to next product
        if "error" in row:
            print "failed to add product:", name, "\n"
            continue
        
        #write row to output file
        wr.writerow(row)
        
        #increment number of rows
        numRows +=1

    
    print   numRows, "out of ", categoryInfo[2], "products in",\
            categoryInfo[1], "category where written to file"

#close browser and file
dataFile.close()
driver.close()