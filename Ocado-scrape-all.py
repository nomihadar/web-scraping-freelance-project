#-------------------------------------------------------------------------------
# Purpose:     scraping data from Ocado website
# Author:      Nomi Hadar
# Created:     20/07/2015
#-------------------------------------------------------------------------------

import time
import csv
import os
import sys


from lxml import html
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

############ Constants ################################

MARKET_NAME = "Ocado "

#root path
ROOT_URl = 'https://www.ocado.com'

#initial url
INITIAL_URL = 'https://www.ocado.com/webshop/getCategories.do?tags='

#path to ouptput file
OUTPUT_PATH = "."

#xpathes queries
xpath_mainCategories = '//div[@id = "supernavSidebar_Grocery"]'
xpath_subCategories = '//div[@id = "supernavSidebar_Mixed"]//a'
xpath_button = '//button[@value= "text" and @title= "Text view"]'
xpath_product = '(//div[@class="listProductWrap"])[position()>{}]'
xpath_title = '//h4[@class="productTitle"]/a/text()'
xpath_weight = '//h4[@class="productTitle"]/a/span/text()'
xpath_price = '//div[@class="typicalPrice"]/h5/text()'
xpath_now_price = '//div[@class="typicalPrice"]//span[@class="nowPrice"]/text()'
xpath_price2 = '//p[@class="typicalPrice"][position()=1]'
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

            htmlSource = product.get_attribute('innerHTML')
            productHtml = html.fromstring(htmlSource) #create a HTML element

            #append product to the list
            allProducts.append(productHtml)

    return allProducts


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

#extract category link, name and amount
names = mainCategoriesHTML.xpath('//a/text()')
urls = mainCategoriesHTML.xpath('//a/@href')
amounts = mainCategoriesHTML.xpath('//span/text()')

#for each link for main category - if textView does not exist,
#get the sub links instea, and union link, name and amount
categoriesInfo = []
for url, name, amount in zip(urls, names, amounts):

    try:
        url = ROOT_URl + url
        driver.get(url)
        time.sleep(1)
        
        #check if text view button exists
        driver.find_element_by_xpath(xpath_button)

        #if button exists
        categoryUrls = [url]

    except NoSuchElementException as e:
        #print "getting sub links for main category", name

        #get sub links of main category instead of just main category link
        subCategories = driver.find_elements_by_xpath(xpath_subCategories)
        categoryUrls = [subCategory.get_attribute('href')
                        for subCategory in subCategories]

    #append category to categories
    categoriesInfo.append((categoryUrls, name, amount))

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
    driver.close()
    sys.exit(1)

#file writer
wr = csv.writer(dataFile, quoting=csv.QUOTE_ALL)

#write titles
wr.writerow(TITELS)

###############################################################################
#   main code - extract products and write to file
###############################################################################

#for each link and sub links of main category
for categoryInfo in categoriesInfo:
   
    print "\nNow in", categoryInfo[1], "category"
    
    numRows = 0 #num rows written in file
    
    for url in categoryInfo[0]:
       
        try:
            driver.get(url)
            time.sleep(1)

            #change to text view by pressing the text view button
            #(saves the image loading time)
            driver.find_element_by_xpath(xpath_button).click()

        except NoSuchElementException as e:
            print categoryInfo[1], "category: there is no textView"
           
        #get a list of all products in current cateogry
        #(where product is a HTML element)
        allProducts = get_all_products_in_page(driver)
        
        #for each product in current category
        for product in allProducts:
            
            #declare product variabels
            name, weight, price, deal = '', '', '', ''
            
            try:
                
                #get product name
                titleLs = product.xpath(xpath_title)
                if titleLs:
                    name = toUTF(titleLs[0].strip())
               
                #get product weight
                weightLs = product.xpath(xpath_weight)
                if weightLs:
                    weight = toUTF(weightLs[0].strip())
                
                #get now price or regular price or "from price"
 
                #case it is a regular price
                if product.xpath(xpath_price):
                    price = toUTF(product.xpath(xpath_price)[0].strip())
                
                #case it is now price
                elif product.xpath(xpath_now_price):
                    price = toUTF(product.xpath(xpath_now_price)[0].strip())
                
                #other kinds of prices
                elif product.xpath(xpath_price2):
                 
                    priceHTML = product.xpath(xpath_price2)[0]
                    
                    if priceHTML.xpath('//span'):
                        price = toUTF(priceHTML.xpath('//text()')[0].strip())
                    else:
                        price = toUTF(priceHTML.xpath('//text()')[0].strip())             
                
                #get deal
                dealLs = product.xpath(xpath_deal)
                if dealLs:
                    deal = toUTF(dealLs[0].strip())
            
            # if not name or not price:
            except Exception as e:    
                print "failed to add product:", name
                print str(e), "\n"
                continue
            
            #creat a tuple from product's data
            row = (categoryInfo[1], name, weight, price, deal)

            #write row to output file
            wr.writerow(row)
        
            #increment number of rows
            numRows +=1

    print numRows, "out of ", categoryInfo[2], \
        "products where written to file in", categoryInfo[1], "category"
        

#close browser and file
dataFile.close()
driver.close()
