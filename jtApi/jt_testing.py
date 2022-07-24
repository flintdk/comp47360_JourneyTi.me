# jt_testing; Selenium Testing module for Journeyti.me Application

# This module requires the installation of selenium libraries:
#   -> pip install selenium

import glob, os, sys
# This might seem unusual... but to make sure we can import modules from the
# folder where jt_gtfs_loader is installed (e.g. if called as an installed
# endpoint) - we always add the module directory to the python path. Endpoints
# can be called from any 'working directory' - but modules can only be imported
# from the python path etc..
jt_testing_module_dir = os.path.dirname(__file__)
sys.path.insert(0, jt_testing_module_dir)

from datetime import datetime
from jt_utils import load_credentials
import logging
import traceback

# For python testing without specifying chrome driver location:
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.ie.service import Service as IEService
from selenium.webdriver.support import expected_conditions as EC
# Expected Conditions
# There are some common conditions that are frequently of use when automating web
# browsers. Listed below are the names of each. Selenium Python binding provides
# some convenience methods so you don’t have to code an expected_condition class
# yourself or create your own utility package for them.
#   -> title_is
#   -> title_contains
#   -> presence_of_element_located
#   -> visibility_of_element_located
#   -> visibility_of
#   -> presence_of_all_elements_located
#   -> text_to_be_present_in_element
#   -> text_to_be_present_in_element_value
#   -> frame_to_be_available_and_switch_to_it
#   -> invisibility_of_element_located
#   -> element_to_be_clickable
#   -> staleness_of
#   -> element_to_be_selected
#   -> element_located_to_be_selected
#   -> element_selection_state_to_be
#   -> element_located_selection_state_to_be
#   -> alert_is_present
from selenium.webdriver.support.ui import WebDriverWait
import time
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.microsoft import IEDriverManager

log = logging.getLogger(__name__)  # Standard naming...

# Load the paramaterised urls for testing from journeytime.json
credentials = load_credentials()
TEST_JTAPI_URL = credentials['SELENIUM_TESTING']['JTAPI_SRVR']
if credentials['SELENIUM_TESTING']['JTAPI_PORT']:
    TEST_JTAPI_URL += ":" + credentials['SELENIUM_TESTING']['JTAPI_PORT']
TEST_JTUI_URL = credentials['SELENIUM_TESTING']['JTUI_SRVR']
if credentials['SELENIUM_TESTING']['JTUI_PORT']:
    TEST_JTUI_URL += ":" + credentials['SELENIUM_TESTING']['JTUI_PORT']

CONST_SML_FILENAMES = ['agency', 'calendar', 'calendardates', 'routes', 'stops', 'transfers']
CONST_LRG_FILENAMES = ['shapes', 'stoptimes', 'trips']

CONST_DOWNLOAD_DIR = 'testing_downloads'

TEST_MODE      = 'test_mode'
TEST_MODE_FULL = 'Full'

#===============================================================================
#===============================================================================
#===============================================================================


def test_static_pages(driver):
    """Test the static pages on the API site are available

    We don't expect these to ever break - but we test them nonetheless
    """
    print('JT_Testing: Validating Static pages')
    home_url = TEST_JTAPI_URL + '/index.html'
    driver.get(home_url)
    try:
        home_message = driver.find_element(By.ID, 'home_heading1').text
        assert 'Journeyti.me - A Free Public Dublin Bus Journeytime Prediction API' in home_message
    except:
        print('\tERROR Expected text on Home page missing.')
    else:
        print('\tHome Page is Valid')

    docs_url = TEST_JTAPI_URL + '/documentation.html'
    driver.get(docs_url)
    try:
        docs_message = driver.find_element(By.ID, 'documentation_heading1').text
        assert 'Journeyti.me API Reference' in docs_message
    except:
        print('\tERROR Expected text on Documentation page missing.')
    else:
        print('\tDocumentation Page is Valid')

    about_url = TEST_JTAPI_URL + '/about.html'
    driver.get(about_url)
    try:
        about_message = driver.find_element(By.ID, 'about_message').text
        assert 'Journeyti.me is the result of a collaborative push' in about_message
    except:
        print('\tERROR Expected text on About page missing.')
    else:
        print('\tAbout Page is Valid')

    return


def test_file_download_links(driver, **kwargs):
    
    docs_url = TEST_JTAPI_URL + '/documentation.html'

    # Set a default wait of 10 seconds... this means we wait a 'maximum' of
    # ten seconds before throwing an exception...
    wait = WebDriverWait(driver, 10)

    # Beforee we download anything, we empty the download directory. 
    empty_download_dir()

    # Some files are huge - we only include those files when running a full
    # integration test - to avoid wasting both time and bandwidth.
    filenames = CONST_SML_FILENAMES
    if TEST_MODE in kwargs:
        if kwargs[TEST_MODE] == TEST_MODE_FULL:
            filenames.append(CONST_LRG_FILENAMES)

    for filename in filenames:
        try:
            driver.get(docs_url)

            # Some ways to find links on a page!...
            #  = driver.find_element_by_css_selector('.icon-csv')
            #  = driver.find_element_by_link_text("Agency")
            #  = driver.find_element_by_id('accept-cookie-notification')
            #onclick="setDownloadTargetValueAndOpenModal('/agency')"
            
            # NOTE presence_of_element_located is waiting for element to be present
            # in the DOM - it's not really checking whether the element is clickable
            # json_element = wait.until(
            #     EC.presence_of_element_located((By.ID, "agency_json"))
            # )
            # NOTE ElementToBeClickable is waiting for element to be 'enabled,' it's
            # not really checking whether the element is clickable
            # json_element = wait.until(
            #     EC.element_to_be_clickable((By.ID, "agency_json"))
            # )

            # The link *must be visible on the screen* if you want to click it! Duh...
            json_element = center_element_on_screen_by_id(filename + '_json', driver)
            json_element.click()

            modal_continue_element = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located((By.ID, "downloadModalContinueButton"))
            )
            modal_continue_element.click()

            # Following may seem pointless... but we catch internal server errors with it...
            if str(driver.title) != 'Journeyti.me GTFS Based Prediction Engine - Public API':
                raise Exception('JSON link of ' + filename + ' is invalid :-(')
            else:
                print('JSON link for ' + filename + ' is valid!')

            driver.get(docs_url)

            # No need to scroll here as we've already centered the title on the page
            driver.find_element(By.ID, filename + '_dljson').click()
            modal_continue_element = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located((By.ID, "downloadModalContinueButton"))
            )
            modal_continue_element.click()
            time.sleep(0.12)  # The modal has a hard-coded 100ms delay... we wait past that...

            # Following may seem pointless... but we catch internal server errors with it...
            if str(driver.title) != 'Journeyti.me GTFS Based Prediction Engine - Public API':
                raise Exception('JSON link of ' + filename + ' is invalid :-(')
            else:
                print('\tDLJSON link for ' + filename + ' is valid!')

            # No need to scroll here as we've already centered the title on the page
            driver.find_element(By.ID, filename + '_dlcsv').click()
            modal_continue_element = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located((By.ID, "downloadModalContinueButton"))
            )
            modal_continue_element.click()
            time.sleep(0.12)  # The modal has a hard-coded 100ms delay... we wait past that...

            # Following may seem pointless... but we catch internal server errors with it...
            if str(driver.title) != 'Journeyti.me GTFS Based Prediction Engine - Public API':
                raise Exception('JSON link of ' + filename + ' is invalid :-(')
            else:
                print('\tDLCSV link for ' + filename + ' is valid!')

        except Exception as e:
            print("Well... dang...", e.__class__, "occurred.")
            print(traceback.format_exc())

    time.sleep(10)  # We do a hard wait here to let ?most' file downloads finish...
    driver.close()  # Close the browser window that the driver has focus of

    return


def test_restful_services(driver, **kwargs):
    
    docs_url = TEST_JTAPI_URL + '/documentation.html'

    # Set a default wait of 10 seconds... this means we wait a 'maximum' of
    # ten seconds before throwing an exception...
    wait = WebDriverWait(driver, 10)

    # Some files are huge - we only include those files when running a full
    # integration test - to avoid wasting both time and bandwidth.
    filenames = CONST_SML_FILENAMES
    if TEST_MODE in kwargs:
        if kwargs[TEST_MODE] == TEST_MODE_FULL:
            filenames.append(CONST_LRG_FILENAMES)

    # Simple endpoint to submission of json and return it to the user...
    # '/update_model_list.do', methods=['GET'])
    # '/get_journey_time.do', methods=['POST'])

    # "/check_username_available.do", methods=['POST'])
    # "/register.do", methods=['POST'])
    # "/login.do", methods=['POST'])
    # "/update_user.do", methods=['POST'])
    # "/get_profile_picture.do", methods=['GET'])

    time.sleep(10)  # We do a hard wait here to let ?most' file downloads finish...
    driver.close()  # Close the browser window that the driver has focus of

    return

#===============================================================================
#===============================================================================
#===============================================================================

def center_element_on_screen_by_id(element_id, driver):
    """
    """
    wait = WebDriverWait(driver, 10)
    element = wait.until(
        EC.presence_of_element_located((By.ID, element_id))
    )

    #driver.execute_script('arguments[0].scrollIntoView(true);', json_element)
    #ActionChains(driver).scroll_to_element(json_element).perform()
    desired_y = (element.size['height'] / 2) + element.location['y']
    current_y = (driver.execute_script('return window.innerHeight') / 2) + driver.execute_script('return window.pageYOffset')
    scroll_y_by = desired_y - current_y
    driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)
    log.debug('scroll complete, scrolled by: ', scroll_y_by)
    time.sleep(1)

    element = wait.until(
        EC.visibility_of_element_located((By.ID, element_id))
    )

    return element

def empty_download_dir():
    """Empty (delete all files in) the Download Directory
    
    This means all files in the download directory at the end of a test run are
    releated to this test run. Makes checking files etc. easier.
    """
    jt_testing_dl_dir = os.path.join(jt_testing_module_dir, CONST_DOWNLOAD_DIR)
    print('Clearing down files in', jt_testing_dl_dir)
    file_extensions = ['*.csv.gz', '*.json']
    files_removed = 0
    for extension in file_extensions:
        # Get a list of all the file paths that ends with .txt from in specified directory
        fileList = glob.glob(os.path.join(jt_testing_dl_dir, extension))
        # Iterate over the list of filepaths & remove each file.
        for filePath in fileList:
            try:
                os.remove(filePath)
                files_removed += 1
            except:
                print("Error deleting file ->", filePath)
    print('\t' + str(files_removed) + ' files removed.')
    
    return

#===============================================================================
#===============================================================================
#===============================================================================

def test_jtapi(driver, **kwargs):
    """Test all the endpoints on the API server

    """
    # Simplest case - we test the static pages load.
    test_static_pages(driver)

    # Test all the download links for the support files...
    test_file_download_links(driver, **kwargs)

    # Most complex case - test the restful services.
    #test_restful_services(driver, **kwargs)

def test_jtui(driver, **kwargs):
    """Test all the endpoints on the UI server

    """

    pass

def test_using_chrome(download_dir, **kwargs):
    # (ALTERNATIVE TO BELOW: Add driver location to path - always only one driver at a time!)
    # Use install() to get the location used by the manager and pass it into service class
    # SYNTAX FOM SELENIUM SITE:  DELETE IF NOTE NEEDED....  service=Service(executable_path=ChromeDriverManager().install()))
    service = ChromeService(executable_path=ChromeDriverManager().install())

    options = webdriver.ChromeOptions()
    prefs = {"media.autoplay.enabled" : False, "download.default_directory" : download_dir}
    options.add_experimental_option("prefs", prefs)
    # Prevent the chrome window from appearing on the screen
    #options.headless = True

    driver = webdriver.Chrome(service=service, options=options)
    # An implicit wait tells WebDriver to poll the DOM for a certain amount
    # of time when trying to find any element (or elements) not immediately available
    driver.implicitly_wait(10) # seconds

    # Synchronizing the code with the current state of the browser is one of the
    # biggest challenges with Selenium, and doing it well is an advanced topic.
    # -
    # Essentially you want to make sure that the element is on the page before you
    # attempt to locate it and the element is in an interactable state before you
    # attempt to interact with it.
    # -
    # An implicit wait is rarely the best solution, but it’s the easiest to
    # demonstrate here, so we’ll use it as a placeholder.

    # Find an element 
    # These are the various ways the attributes are used to locate elements on a page:
    # find_element(By.ID, "id")
    # find_element(By.NAME, "name")
    # find_element(By.XPATH, "xpath")
    # find_element(By.LINK_TEXT, "link text")
    # find_element(By.PARTIAL_LINK_TEXT, "partial link text")
    # find_element(By.TAG_NAME, "tag name")
    # find_element(By.CLASS_NAME, "class name")
    # find_element(By.CSS_SELECTOR, "css selector")

    # Take action on element
    # search_box.send_keys("Selenium")
    # search_button.click()

    # Request element information
    # value = search_box.get_attribute("value")

    test_jtapi(driver, **kwargs)

    test_jtui(driver, **kwargs)

    driver.quit()  # Closes all browser windows and safely ends the session


def test_using_firefox(download_dir, **kwargs):
    service = FirefoxService(executable_path=GeckoDriverManager().install())

    options = webdriver.FirefoxOptions()
    # Set following preference to tell Selenium Webdriver to not use the default
    # directory for downloading the file.
    options.set_preference("browser.download.folderList", 2)
    # Set following preference to turn off the showing of download progress.
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", download_dir)
    # Tells Firefox to automatically download the files of the selected mime-types.
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/json")
    # Prevent the firefox window from appearing on the screen
    #options.headless = True

    driver = webdriver.Firefox(service=service)
    # An implicit wait tells WebDriver to poll the DOM for a certain amount
    # of time when trying to find any element (or elements) not immediately available
    driver.implicitly_wait(10) # seconds

    test_jtapi(driver, **kwargs)

    test_jtui(driver, **kwargs)

    driver.quit()  # Closes all browser windows and safely ends the session


# def test_using_edge(prefs):
#     service = EdgeService(executable_path=EdgeChromiumDriverManager().install())

#     options = webdriver.EdgeOptions()
#     options.add_experimental_option("prefs",prefs)

#     driver = webdriver.Edge(service=service, options=options)

#     driver.quit()

# @pytest.mark.skip(reason="only runs on Windows")
# def test_ie_session():
#     service = IEService(executable_path=IEDriverManager().install())

#     driver = webdriver.Ie(service=service)

#     driver.quit()

#===============================================================================
#===============================================================================
#===============================================================================

def main(**kwargs):
    """Run Selenium tests for the Journeyti.me application


    """
    start_time = datetime.now()

    print('JT_Testing: Start of test set (' + start_time.strftime('%Y-%m-%d %H:%M:%S') + ')')
    print('            Use \'test_mode=Full\' to conduct a more time-consuming, fuller test.')
    if TEST_MODE in kwargs:
        if kwargs[TEST_MODE] == TEST_MODE_FULL:
            print('            \"test_mode=Full\" engaged. Please be patient!')
    print('')

    try:
        jt_testing_dl_dir = os.path.join(jt_testing_module_dir, CONST_DOWNLOAD_DIR)
        test_using_chrome(jt_testing_dl_dir, **kwargs)

        #test_using_firefox(jt_testing_temp_dir, **kwargs)
    except:
        # if there is any problem, print the traceback
        print(traceback.format_exc())

    # (following returns a timedelta object)
    elapsedTime = datetime.now() - start_time
    
    # returns (minutes, seconds)
    #minutes = divmod(elapsedTime.seconds, 60) 
    minutes = divmod(elapsedTime.total_seconds(), 60) 
    print('Tests Complete! (Elapsed time:', minutes[0], 'minutes', minutes[1], 'seconds)\n')
    sys.exit()

if __name__ == '__main__':
    main(**dict(arg.split('=') for arg in sys.argv[1:]))  # kwargs