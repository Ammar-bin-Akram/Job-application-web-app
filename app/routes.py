from selenium.webdriver.chrome.options import Options
from werkzeug.utils import secure_filename

from app import app
from flask import render_template, request
import time
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService, Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import os

ignored_jobs = 0
saved_jobs = 0


@app.route("/")
def home():
    return render_template("home.html", title="JobBot")


@app.route("/get-details")
def get_details():
    return render_template("get-details.html", title="Details")


@app.route("/run-bot", methods=['POST'])
def run_bot():
    email = request.form['account-email']
    password = request.form['account-password']
    keyword = request.form['search-keyword']
    country = request.form['search-country']
    file = request.files['file']
    file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
    uploaded_filename = file.filename
    main_driver = setup_driver()
    login_to_linkedin(main_driver, email, password)
    print('Login was completed')
    time.sleep(30)
    filter_application(main_driver, keyword, country)
    print('Filters have been applied')
    file_path = f"./static/uploaded_files/{uploaded_filename}"
    time.sleep(10)
    job_finding(main_driver, file_path)
    time.sleep(10)
    goto_next_page(main_driver, file_path)
    return f"Your bot has started running with {email}, {keyword}, {country}"


def setup_driver():
    options = Options()
    options.add_experimental_option('detach', True)
    # setting up the driver
    driver = webdriver.Chrome(options=options, service=Service(ChromeDriverManager().install()))
    # reaching the required site
    driver.get("https://www.linkedin.com/login")
    driver.maximize_window()
    return driver


# function to log in to linkedin account
def login_to_linkedin(driver, login_username, login_password):
    username_input = driver.find_element(By.NAME, 'session_key')
    password_input = driver.find_element(By.NAME, 'session_password')
    username_input.send_keys(login_username)
    password_input.send_keys(login_password)

    signin_button = driver.find_element(By.CSS_SELECTOR, "[aria-label='Sign in']")
    signin_button.click()


# function to apply filters on the job search
def filter_application(driver, word, country):
    keyword_input = driver.find_element(By.CSS_SELECTOR, "[aria-label='Search']")
    word = word + ' jobs'
    keyword_input.send_keys(word)
    keyword_input.send_keys(Keys.ENTER)
    time.sleep(4)
    # selecting only remote jobs
    remote_button = driver.find_element(By.XPATH, "//a[contains(@href, 'WT=2')]")
    remote_button.click()
    time.sleep(3)
    # selecting the country in which we want to look for jobs
    country_input = driver.find_element(By.CSS_SELECTOR, "[aria-label='City, state, or zip code']")
    country_input.click()
    country_input.clear()
    country_input.send_keys(country)
    country_input.send_keys(Keys.ENTER)
    time.sleep(5)
    # only selecting jobs that are easy to apply
    easy_apply = driver.find_elements(By.CSS_SELECTOR, "[aria-label='Easy Apply filter.']")
    if len(easy_apply) == 0:
        return
    else:
        easy_apply_button = easy_apply[0]
        easy_apply_button.click()
    time.sleep(5)
    # getting the jobs that are only 1 day old
    date_posted_button = driver.find_element(By.CSS_SELECTOR,
                                             "[aria-label='Date posted filter. Clicking this button displays all Date posted filter options.']")
    date_posted_button.click()
    past_day_button = driver.find_element(By.CSS_SELECTOR, "[for='timePostedRange-r86400']")
    past_day_button.click()
    time.sleep(10)
    show_results_button = driver.find_element(By.XPATH,
                                              "/html/body/div[5]/div[3]/div[4]/section/div/section/div/div/div/ul/li[5]/div/div/div/div[1]/div/form/fieldset/div[2]/button[2]")
    # show_results_button = driver.find_element(By.XPATH, "//*[contains(@aria-label, 'Apply current filter to show')]")
    show_results_button.click()
    time.sleep(3)


def job_finding(driver, path):
    job_ads = driver.find_elements(By.CSS_SELECTOR, '.ember-view.jobs-search-results__list-item.occludable-update.p0.relative.scaffold-layout__list-item')
    for job_ad in job_ads:
        # hovering over each job and then applying to it
        hover = ActionChains(driver).move_to_element(job_ad)
        hover.perform()
        job_ad.click()
        # print(job_ad.get_attribute('innerHTML'))
        job_application(driver, path)


def job_application(driver, path):
    global saved_jobs
    global ignored_jobs
    job_easy_apply = driver.find_elements(By.CSS_SELECTOR,
                                          ".jobs-apply-button.artdeco-button.artdeco-button--3.artdeco-button--primary.ember-view")
    if len(job_easy_apply) == 0:
        return
    else:
        job_easy_apply_button = job_easy_apply[0]
        job_easy_apply_button.click()
    time.sleep(3)
    # checking if the job application does not require more than cv and required information
    # on the first page of the application
    next_button = driver.find_element(By.CSS_SELECTOR,
                                      ".artdeco-button.artdeco-button--2.artdeco-button--primary.ember-view")
    next_button.click()
    time.sleep(3)
    next_review_span = driver.find_element(By.CSS_SELECTOR, ".artdeco-button__text")
    next_text = next_review_span.get_attribute('innerHTML')
    next_text = next_text.strip()
    # if the application is all set to go then submit the application
    if next_text == 'Submit application':
        next_button.click()
        time.sleep(3)
        close_popup_button = driver.find_element(By.CSS_SELECTOR, "[aria-label='Dismiss']")
        close_popup_button.click()
        print('Application was submitted after the first page')
        saved_jobs += 1
        time.sleep(10)
        return
    time.sleep(4)
    # on the next page of application
    # checking if the next page requires to upload resume or asks some different questions
    questions_heading = driver.find_element(By.CSS_SELECTOR, ".t-16.t-bold")
    required_information = questions_heading.get_attribute('innerHTML')
    required_information = required_information.strip()
    if required_information == 'Resume' or required_information == 'Currículum':
        uploaded_resumes = driver.find_elements(By.CSS_SELECTOR, "[aria-label='Select this resume']")
        uploaded_selected_resume = driver.find_elements(By.CSS_SELECTOR, "[aria-label='Selected']")
        if len(uploaded_resumes) == 0 or len(uploaded_selected_resume) == 0:
            upload_resume_button = driver.find_element(By.NAME, "file")
            resume_path = "C:\\Users\\HP\\Documents\\My-CV.pdf"
            upload_resume_button.send_keys(resume_path)
            time.sleep(10)
            print('Resume was uploaded')
        next_review_button = driver.find_element(By.CSS_SELECTOR,
                                                 ".artdeco-button.artdeco-button--2.artdeco-button--primary.ember-view")
        next_review_span = next_review_button.find_element(By.CSS_SELECTOR, ".artdeco-button__text")
        next_review_text = next_review_span.get_attribute('innerHTML')
        next_review_text = next_review_text.strip()
        print(next_review_text)
        if next_review_text == "Next":
            print('the text is review')
            close_popup_button = driver.find_element(By.CSS_SELECTOR, "[aria-label='Dismiss']")
            close_popup_button.click()
            time.sleep(2)
            discard_button = driver.find_element(By.CSS_SELECTOR,
                                                 ".artdeco-button.artdeco-button--2.artdeco-button--secondary.ember-view.artdeco-modal__confirm-dialog-btn")
            discard_button.click()
            ignored_jobs += 1
        elif next_review_text == 'Review':
            print('the text is review')
            next_review_button.click()
            submit_button = driver.find_element(By.CSS_SELECTOR, "[aria-label='Submit application']")
            submit_button.click()
            time.sleep(4)
            print('Application was not submitted after the first page.')
            # closing the popup that appeared after applying to the job
            close_popup_button = driver.find_element(By.CSS_SELECTOR, "[aria-label='Dismiss']")
            close_popup_button.click()
            saved_jobs += 1
    # if the next page of application does not require you to submit your resume then, close the application
    elif required_information != 'Resume' or required_information != 'Currículum':
        close_popup_button = driver.find_element(By.CSS_SELECTOR, "[aria-label='Dismiss']")
        close_popup_button.click()
        time.sleep(2)
        discard_button = driver.find_element(By.CSS_SELECTOR,
                                             ".artdeco-button.artdeco-button--2.artdeco-button--secondary.ember-view.artdeco-modal__confirm-dialog-btn")
        discard_button.click()


def goto_next_page(driver, path):
    try:
        # finding pagination and then going to the next page if next page exists
        pagination = driver.find_elements(By.CSS_SELECTOR, ".artdeco-pagination__pages.artdeco-pagination__pages--number")
        if len(pagination) == 0:
            print('Jobs only exist on the first page.')
        else:
            pagination = pagination[0]
            pages = pagination.find_elements(By.CSS_SELECTOR, ".artdeco-pagination__indicator.artdeco-pagination__indicator--number.ember-view")
            number_of_pages = len(pages)
            print(number_of_pages)
            for number in range(1, number_of_pages):
                # finding the pagination element again because the error of state element reference can occur
                pagination = driver.find_elements(By.CSS_SELECTOR, ".artdeco-pagination__pages.artdeco-pagination__pages--number")
                pagination = pagination[0]
                pages = pagination.find_elements(By.CSS_SELECTOR,
                                                 ".artdeco-pagination__indicator.artdeco-pagination__indicator--number.ember-view")
                print('On page number ', number)
                next_page = pages[number]
                next_page.click()
                job_finding(driver, path)

    except Exception as ex:
        print(ex)


def save_job_link_to_file(job_link, job_status):
    with open('job_links.csv', 'a') as file:
        file.write(f"{job_link}{job_status}\n")
