import time
import selenium.common.exceptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd

# Identify articles to target - Should be urls saved in a txt file
articles = 'articles.txt'

# Define an output folder
output_folder = './Processed Articles/'  # Where files should be written to

# Define the main function

def get_comments(url, name):  # Takes the target url and a name for the output file.
    driver = webdriver.Chrome(
        "chromedriver")  # This should be set to where the driver is installed
    driver.get(url)

    # Agree to cookies - Need to do this before we can flip through the pages

    WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it(
        (By.XPATH, '//*[@id="sp_message_iframe_514494"]')))  # Switch to the pop-up frame
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.XPATH, '//*[@id="notice"]/div[3]/div/div/button[1]'))).click()  # Click 'Yes I'm happy'
    driver.switch_to.default_content()  # Switch back to the other frame

    # Click to expand the comments
    time.sleep(2)

    dropdown = driver.find_element_by_xpath('// *[ @ id = "comment-filters"] / div[5] / div / div[1] / button')
    dropdown.click()
    expanded = driver.find_element_by_xpath('// *[ @ id = "dropbox-id-threads-dropdown"] / li[2] / button')
    expanded.click()

    time.sleep(3)  # Wait a few seconds for all comments to load
    comments_list = []  # Initialise an empty list to store all comments in
    pages = driver.find_elements_by_class_name('css-421l3v')  # Find the buttons to push to flip through the other pages
    page_numbers = []
    largest_number = 0

    # Remove duplicate pages

    for page in pages:
        if page.text not in page_numbers:
            page_numbers.append(page.text)
            if int(page.text) > largest_number:
                largest_number = int(page.text)
        elif page.text in page_numbers:
            pages.remove(page)
    pages = pages[:largest_number - 1]

    # Get comments from the first page

    comments = driver.find_elements_by_class_name('css-6z96rl-Comment')
    for p in range(len(comments)):
        comments_list.append(comments[p].text)

    # Iterate through the remaining pages

    for page in pages:
        try:
            page.click()
            time.sleep(3)
            comments = driver.find_elements_by_class_name('css-6z96rl-Comment')
            for p in range(len(comments)):
                comments_list.append(comments[p].text)
        except selenium.common.exceptions.StaleElementReferenceException:
            pass
    # Prepare the comments for formatting

    output = pd.DataFrame(comments_list)
    output = format_article(output)
    output.to_excel(output_folder + name + '.xlsx')  # Write the comments to an Excel file
    driver.close()  # Close the browser to clear for the next article

# Define the function to format the comments from each article (nested in 'get_comments')

def format_article(article):
    article['Split Strings'] = article[0].apply(lambda x: str.splitlines(x))

    article['Username'] = article['Split Strings'].apply(lambda x: x[0])

    article['Time'] = article['Split Strings'].apply(lambda x: x[2] if x[1][0] == ' ' else x[1])

    article['Points'] = article['Split Strings'].apply(lambda x: x[3] if x[1][0] == ' ' else x[2])

    article['Remove'] = article['Split Strings'].apply(lambda x: x[-1])

    article['Split Strings'] = article['Split Strings'].apply(lambda x: x[:-1])  # Remove 'Report' button text

    article['Comments'] = article['Split Strings'].apply(lambda x: ' '.join(x[4:]) if x[1][0] == ' ' else ' '.join(x[3:]))

    article = article[['Username', 'Time', 'Points', 'Comments']]

    return article


if __name__ == "__main__":
    urls = []  # Open the file with the list of Guardian articles to target and add them to a list
    with open(articles, 'r') as f:
        for line in f:
            urls.append(line)
        f.close()
    article_number = 1
    for url in urls:
        name = 'Article ' + str(article_number)
        get_comments(url, name)
        article_number += 1
