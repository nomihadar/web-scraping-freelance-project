#-------------------------------------------------------------------------------
# Name:        module1
# Author:      Nomi Hadar
# Created:     27/08/2015
#-------------------------------------------------------------------------------

import os
import sys
import datetime
import time
import re
import csv

from lxml import html
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.support.ui import Select

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

###############################################################################
#   Constants
###############################################################################

#airline name
AIRLINE_NAME = 'WIZZ'

#initial url
INITIAL_URL = 'https://wizzair.com/en-GB/FlightSearch'

#path to ouptput file
OUTPUT_PATH = "C:\\Users\\michal\\Documents\\akivaBerger\\Airlines\\" \
              + AIRLINE_NAME

#titels of output file
TITELS = ("Airline", "Leave from", "Going To",
          "Current Date", "Departure Date", "Price (GBP)")

DELAY = 3 #seconds

DATE_FORMAT = "%d/%m/%Y" #format of date

CURRENCY = 'GBP' #currency

REGX_PRICE = '\d*\,*\d*\.\d+|\d+' #regular expression for price

#delta of days
DAYS = [7,14,30,60,90]

#flights
FLIGHTS_LIST = [['BCN','BUD'],
['BGO','GDN'],
['BGY','SOF'],
['BUD','BCN'],
['BUD','CRL'],
['BUD','DTM'],
['BUD','EIN'],
['BUD','FCO'],
['BUD','IEV'],
['BUD','LTN'],
['BUD','MAD'],
['BUD','MMX'],
['BUD','MXP'],
['BUD','NYO'],
['BUD','SAW'],
['BUD','TLV'],
['BUD','VKO'],
['CIA','OTP'],
['CLJ','LTN'],
['CRL','BUD'],
['CRL','OTP'],
['CRL','WAW'],
['DEB','LTN'],
['DTM','BUD'],
['DTM','GDN'],
['DTM','KTW'],
['DTM','OTP'],
['EIN','BUD'],
['EIN','KTW'],
['FCO','BUD'],
['FCO','WAW'],
['GDN','BGO'],
['GDN','DTM'],
['GDN','LBC'],
['GDN','LTN'],
['GDN','MMX'],
['GDN','NYO'],
['GDN','TKU'],
['GDN','TRF'],
['IEV','BUD'],
['KSC','LTN'],
['KTW','DTM'],
['KTW','EIN'],
['KTW','LTN'],
['KTW','TRF'],
['LBC','GDN'],
['LTN','BUD'],
['LTN','CLJ'],
['LTN','DEB'],
['LTN','GDN'],
['LTN','KSC'],
['LTN','KTW'],
['LTN','OTP'],
['LTN','POZ'],
['LTN','PRG'],
['LTN','RIX'],
['LTN','SKP'],
['LTN','SOF'],
['LTN','VNO'],
['LTN','WAW'],
['LTN','WRO'],
['MAD','BUD'],
['MAD','OTP'],
['MLH','SKP'],
['MMX','BUD'],
['MMX','GDN'],
['MXP','BUD'],
['MXP','OTP'],
['NYO','BUD'],
['NYO','GDN'],
['NYO','WAW'],
['OTP','CIA'],
['OTP','CRL'],
['OTP','DTM'],
['OTP','LTN'],
['OTP','MAD'],
['OTP','MXP'],
['OTP','TSF'],
['POZ','LTN'],
['PRG','LTN'],
['RIX','LTN'],
['SAW','BUD'],
['SKP','LTN'],
['SKP','MLH'],
['SOF','BGY'],
['SOF','LTN'],
['TKU','GDN'],
['TLV','BUD'],
['TRF','GDN'],
['TRF','KTW'],
['TSF','OTP'],
['VKO','BUD'],
['VNO','LTN'],
['WAW','CRL'],
['WAW','FCO'],
['WAW','LTN'],
['WAW','NYO'],
['WRO','LTN']]


#xpath of the search button
XPATH_SEARCH_BUTTON = '//*[@class= "buttonN button primary search preloader "]'

#xpath of no flights found
XPATH_NO_FLIGHTS = "//*[text()[contains(.,'No flight found')]]"

#xpath for the radio button of a basic flight
XPATH_BASIC_FLIGHTS_RADIOS = '//*[contains(@class,"selectFlightTooltip")]\
                             /label[contains(@class,"flight-fare-type--basic")]\
                             /span[contains(@class,"input-nowizzclub")]'

#xpath for price in GBP 
XPATH_GBP_PRICE = '//*[@class="paymentcurrencyselector"]/option[contains(.,"GBP")]'

#xpath of payment selector
XPATH_PAYMENT_SELECTOR = '//*[contains(@id,"PaymentCurrencySelector-button")]'

#xpath for price
XPATH_PRICE = '//*[@id = "priceDisplayBodyTotal"]//\
              *[contains(@style,"display: inline")]'

#java script for displaying hidden fields such as date pickers
JAVA_SCRIPT_DISPLAY_FIELDS = 'document.getElementsByClassName\
                             ("search-date")[0].style.display = "block";'

#java script for changing the permission of the datepicker 
JAVA_SCRIPT_CHANGE_PERMISSION = 'document.getElementsByClassName\
                                ("datepicker")[0].readOnly = false;'

###############################################################################
#   Functions
###############################################################################

###############################################################################
#   FUNCTION toUTF
#   input: string
#   return value: input string encoded in UTF-8
###############################################################################
def toUTF(string):
    return u''.join(string).encode('utf-8')

###############################################################################
#   FUNCTION fillPlaces
#   function: fill "leave from" and "going to" places
#   input: browser, leaving from place and destination
#   return value: none
###############################################################################
def fillPlaces(driver, leaveFrom, destination):
    
    #open initial page in browser
    driver.get(INITIAL_URL)
    
    #fill the "Leaving From" filed 
    from_textfield = driver.find_element_by_class_name('city-from')
    from_textfield.clear()
    from_textfield.send_keys(leaveFrom)
    from_textfield.send_keys(Keys.RETURN)
    
    #fill the "Going To" filed 
    to_textfield = driver.find_element_by_class_name('city-to')
    to_textfield.clear()
    to_textfield.send_keys(destination)
    to_textfield.send_keys(Keys.RETURN)
 
    
###############################################################################
#   FUNCTION fillDate
#   function: fill the departure date of the flight 
#   input: browser, departureDate
#   return value: none
###############################################################################    
def fillDate(driver, departureDate):

    #display hidden fields - the search-date
    driver.execute_script(JAVA_SCRIPT_DISPLAY_FIELDS)
    
    #fill the "departure date" filed 
    datepickers = driver.find_elements_by_class_name('datepicker')
    departureDate_picker = datepickers[0]
    
    #change the permission of the departure date picker to write mode
    driver.execute_script(JAVA_SCRIPT_CHANGE_PERMISSION)

    departureDate_picker.clear() #clear date in picker

    #fill picker
    departureDate_picker.send_keys(departureDate)  
    
 
    
###############################################################################
#   create a directeory and output file 
###############################################################################

#create an output directory if directory does not exist
if not os.path.exists(OUTPUT_PATH):
    os.makedirs(OUTPUT_PATH)

#create an output csv file
try:
    #file name
    fileName =  AIRLINE_NAME + " " + time.strftime("%d-%m-%Y") + '.csv'
    
    #open file
    dataFile = open(OUTPUT_PATH + "\\" + fileName, 'wb')

except IOError as e:
    print str(e)
    sys.exit(1)

#file writer
fileWriter = csv.writer(dataFile, quoting=csv.QUOTE_ALL)

#write titles
fileWriter.writerow(TITELS)
    
###############################################################################
#   Main Code
###############################################################################

#open browser
print "-----> opening driver"
driver = webdriver.Firefox()

#get current date
currentDate = datetime.datetime.now()

#for each flight 
for leaveFrom, destination in FLIGHTS_LIST:
    
    print "\n", leaveFrom, "-->", destination
    
    fillPlaces(driver, leaveFrom, destination)
    
    for deltaDays in DAYS:
        
        #get the departure date
        departureDate = (currentDate + datetime.timedelta(days= deltaDays))\
                        .strftime(DATE_FORMAT)
       
        #fill flight's departure date                
        fillDate(driver, departureDate)
        
        #press main search button 
        driver.find_element_by_xpath(XPATH_SEARCH_BUTTON).click()
        
        #if no flights were found
        if driver.find_elements_by_xpath(XPATH_NO_FLIGHTS):
            print departureDate, ": no flights"
            continue #continue to next departure date
       
        #get the radio buttons of basic flights only
        basicRadioButtons = WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH, XPATH_BASIC_FLIGHTS_RADIOS))
        )
        
        #for each radio button of basic flight 
        for i in range(len(basicRadioButtons)):
           
            #get current radio button (can not iterate directly on buttons
            #since the following click de-attaches the second button and the rest
            #from the driver)
            radio = driver.find_elements_by_xpath\
                             (XPATH_BASIC_FLIGHTS_RADIOS)[i]
           
            #click on the radio button of flight's price to get summary 
            radio.click()
            time.sleep(3) #sleep after clicking
            
            # #convert to favorite currency
            # if i == 0:
            #     selector = WebDriverWait(driver, 10).until(
            #         EC.presence_of_element_located((By.XPATH, XPATH_PAYMENT_SELECTOR))
            #     )
            #     # selector = driver.find_element_by_xpath(XPATH_PAYMENT_SELECTOR)
            #     selector.click()
            #     
            #     time.sleep(2)
            #     driver.find_elements_by_link_text(CURRENCY)[0].click()
            
            #get price 
            price = driver.find_element_by_xpath(XPATH_PRICE).text
            match = re.search(REGX_PRICE, price)
            price = toUTF(match.group())
        
            #create row for output file
            row = [AIRLINE_NAME, leaveFrom, destination,
                   currentDate.strftime(DATE_FORMAT), departureDate, price]
            
            print row
            
            fileWriter.writerow(row)
            
            price = ""
            
       # break   
     
    # break
    

driver.close()
