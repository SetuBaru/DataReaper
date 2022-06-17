"""
Developed by: https://github.com/SetuBaru
Based On: "https://github.com/Ladvien/deep_arcane/blob/main/1_get_images/scrap.py"

"""
##############
# Dependencies
##############
RuntimeErrorLog = []
try:
    import os
    import time
    import requests
    import io
    import hashlib
    from PIL import Image
    from selenium import webdriver
    import signal
    import datetime
    import chromedriver_autoinstaller
    chromedriver_autoinstaller.install(False, "../../_cache_")  # chromedriver compatibility autoinstaller.
    print('Dependencies Successfully Loaded!')
# Runtime Error Handling
except Exception as _ImportError_:
    print(f'Encountered an _ImportError_:\t {_ImportError_}')
    RuntimeErrorLog.append(f"'{str(datetime.datetime.now())}' | ImportError Encountered: {_ImportError_};\n")


##############
# Parameters
##############
try:
    # Runtime Variables
    number_of_images = 100
    GET_IMAGE_TIMEOUT = 2
    SLEEP_BETWEEN_INTERACTIONS = 0.1
    SLEEP_BEFORE_MORE = 5
    IMAGE_QUALITY = 85
    current_state = -1
    # BaseFileSystem Setup.
    cache = "_cache_"
    img_path = "../../Data/Images"
    state_file = cache + "/state.log"
    RequestsModule = cache + "/requests.io"
    ErrorLog = cache + "/error.log"
    tasks = 0
    # Runtime Error Handling
except Exception as RuntimeSetupError:
    print(f'Encountered an _ImportError_:\t {RuntimeSetupError}')
    RuntimeErrorLog.append(f"'{str(datetime.datetime.now())}' | RuntimeSetupError Encountered: {RuntimeSetupError};\n")

##############
# File System Setup
##############
# FileSys Integrity Control
# _Cache_ Path Check :1/5
if os.path.exists(cache) is False:
    os.mkdir(cache)
    tasks = tasks + 1
# Error.log Check :2/5
if os.path.isfile(ErrorLog) is False:
    with open(ErrorLog) as f:
        f.write(f"'{str(datetime.datetime.now())}' |\tERRORLOG CREATED: IN PATH {ErrorLog} ;\n")
    f.close()
    current_state = 0
    tasks = tasks + 1
# State.log File Check :3/5
if os.path.isfile(state_file) is False:
    with open(state_file) as f:
        f.write(f"'{str(datetime.datetime.now())}' |\tSTATELOG CREATED: IN PATH {state_file} ;\n")
    f.close()
    current_state = 0
    tasks = tasks + 1
# Img_Path Check :4/5
if os.path.exists(img_path) is False:
    os.makedirs(img_path)
    with open(state_file) as f:
        f.write(f"'{str(datetime.datetime.now())}' |\tDIR CREATED: {img_path};\n")
    f.close()
    tasks = tasks + 1
# request.io Check :5/5
if os.path.isfile(RequestsModule) is False:
    search_items = []
    with open(RequestsModule) as f:
        f.write(f" ------'{RequestsModule}': Last Modified:\t'{str(datetime.datetime.now())}'------\n")
    f.close()
    with open(state_file) as f:
        f.write(f"'{str(datetime.datetime.now())}' |\tDIR CREATED: '{RequestsModule}';\n")
    f.close()
    tasks = tasks + 1

##############
# Search Pre-processing
##############
# Request I/O first time creation
if os.path.isfile(RequestsModule) is True:
    with open(RequestsModule) as f:
        search_items = f.readlines()
    f.close()
# Search Query List Formatting
search_items = list(map(lambda s: s.strip(), search_items))
# Query Extraction
_query = search_items[1]
del search_items[0]  # remove header
del search_items[0]  # remove query body
del search_items[0]  # remove {
del search_items[-1]  # remove }
# Topic Extraction
if "BOTONICA" in _query.split(',')[-1].upper():
    domain = "Botanica"
elif "GEODEXX" in _query.split(',')[-1].upper():
    domain = "GeoDexX"
elif _query.split(',')[-1].upper() == "AGIVS":
    domain = "GEODEX"
else:
    domain = _query.split(',')[-1]
# Topic Dir Creation
if os.path.isfile(img_path + "/" + domain) is False:
    os.makedirs(img_path + "/" + domain)
# Verifying Current_States Existence
if not current_state:
    current_state = []
# Creating StateLog and updating state.log
if current_state is 0 or -1 or []:
    current_state = search_items
    StateLog = [f"{domain}: {','.join(current_state)};"]
    with open(state_file) as f:
        try:
            f.write('\n'.join(StateLog))
        except Exception as Error:
            RuntimeErrorLog.append(Error)
            f.write(f"{StateLog[0]}\n")
    f.close()
# loading StateLog
elif os.path.isfile(state_file) is True and (current_state is not -1) and (current_state is not 0):
    with open(state_file) as f:
        StateLog = f.read().strip().split(";")
    f.close()
    # Removing query requests already within the DataSet
    pos = -1
    for line in StateLog:
        pos = pos + 1
        if domain in line.split(":")[0]:
            current_state = line.split(":")[1].split(',')
            search_items = [item for item in search_items if item not in current_state]
            StateLog[pos] = f"{domain}: {current_state + search_items};"
        else:
            StateLog.append(f"{domain}: {search_items};")
        with open(state_file) as f:
            f.write('\n'.join(StateLog))
        f.close()

##########
# Chrome Instance
##########
# Optional argument, if not specified will look in current working dir
wd = webdriver.Chrome("../../_cache_")


##########
# Web timeout Handler
##########
# Credit: https://stackoverflow.com/a/22348885
class timeout:
    def __init__(self, seconds=1, error_message="Timeout"):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)


##########
# Url fetching
##########
def fetch_image_urls(
        query: str,
        max_links_to_fetch: int,
        wd: webdriver,
        sleep_between_interactions: float = 1.0,
):
    def scroll_to_end(wd):
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)

    # Build the Google Query.
    search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"
    # load the page
    wd.get(search_url.format(q=query))
    # Declared as a set, to prevent duplicates.
    image_urls = set()
    image_count = 0
    results_start = 0
    while image_count < max_links_to_fetch:
        scroll_to_end(wd)
        # Get all ImgReaper thumbnail results
        thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")
        number_results = len(thumbnail_results)
        print(
            f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}"
        )
        # Loop through ImgReaper thumbnail identified
        for img in thumbnail_results[results_start:number_results]:
            # Try to click every thumbnail such that we can get the real ImgReaper behind it.
            try:
                img.click()
                time.sleep(sleep_between_interactions)
            except Exception as Error:
                print(Error)
                continue
            # Extract ImgReaper urls
            actual_images = wd.find_elements_by_css_selector("img.n3VNCb")
            for actual_image in actual_images:
                if actual_image.get_attribute(
                        "src"
                ) and "http" in actual_image.get_attribute("src"):
                    image_urls.add(actual_image.get_attribute("src"))
            image_count = len(image_urls)
            # If the number images found exceeds our `num_of_images`, end the search.
            if len(image_urls) >= max_links_to_fetch:
                print(f"Found: {len(image_urls)} ImgReaper links, done!")
                break
        else:
            # If we haven't found all the images we want, let's look for more.
            print("Found:", len(image_urls), "ImgReaper links, looking for more ...")
            time.sleep(SLEEP_BEFORE_MORE)
            # Check for button signifying no more images.
            not_what_you_want_button = ""
            try:
                not_what_you_want_button = wd.find_element_by_css_selector(".r0zKGf")
            except Exception as Error:
                print(Error)
                pass
            # If there are no more images return.
            if not_what_you_want_button:
                print("No more images available.")
                return image_urls
            # If there is a "Load More" button, click it.
            load_more_button = wd.find_element_by_css_selector(".mye4qd")
            if load_more_button and not not_what_you_want_button:
                wd.execute_script("document.querySelector('.mye4qd').click();")
        # Move the result startpoint further down.
        results_start = len(thumbnail_results)
    return image_urls


##########
# Image Saving and retention
##########
def persist_image(folder_path: str, url: str):
    try:
        print("Getting ImgReaper")
        # Download the ImgReaper.  If timeout is exceeded, throw an error.
        with timeout(GET_IMAGE_TIMEOUT):
            image_content = requests.get(url).content

    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")

    try:
        # Convert the ImgReaper into a bit stream, then save it.
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert("RGB")
        # Create a unique filepath from the contents of the ImgReaper.
        file_path = os.path.join(
            folder_path, hashlib.sha1(image_content).hexdigest()[:10] + ".jpg"
        )
        with open(file_path, "wb") as f:
            image.save(f, "JPEG", quality=IMAGE_QUALITY)
        print(f"SUCCESS - saved {url} - as {file_path}")
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")


##########
# Search and Download Algo
##########
def search_and_download(search_term: str, target_path="Data", number_images=5):
    # Default Domain Path
    dir1 = 'Botanica'
    # Create target_path
    if not os.path.isdir(target_path):
        os.makedirs(target_path)
    if domain:
        dir1 = domain
    # Create the Domain Folder
    dir1 = os.path.join(target_path, dir1)
    if not os.path.exists(dir1):
        os.makedirs(dir1)
    target_folder = os.path.join(dir1, '_'.join(search_term.title().split(' ')))
    if not os.path.exists(target_folder):
        # Create the img dir
        os.makedirs(target_folder)
    # Initializing Chrome Driver
    with webdriver.Chrome() as wd:
        # Search for images URLs.
        res = fetch_image_urls(
            search_term,
            number_images,
            wd=wd,
            sleep_between_interactions=SLEEP_BETWEEN_INTERACTIONS,
        )
        # Download the images.
        if res is not None:
            for elem in res:
                persist_image(dir1, elem)
        else:
            print(f"Failed to return links for term: {search_term}")


##########
# LOOP INITIALIZATION
##########
# Loop through all the search terms.
for term in search_items:
    search_and_download(term, domain, number_of_images)
