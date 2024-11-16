import random
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import time
import pyautogui





class LinkedinScraperScript:

    def __init__(self):
        print("Initializing driver...")

        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--disable-extensions')
        self.chrome_options.add_argument("start-maximized")


        self.driver = webdriver.Chrome(options=self.chrome_options)
        stealth(self.driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        print("Driver launched")

        # Randomize the window size and position
        window_width = random.randint(1024, 1920)
        window_height = random.randint(768, 1080)
        window_position_x = random.randint(0, 100)
        window_position_y = random.randint(0, 100)

        self.driver.set_window_size(window_width, window_height)
        self.driver.set_window_position(window_position_x, window_position_y)

    def human_type(self,element, text, prefix=""):

            # Attempt to type using the Selenium send_keys method
            
            
            if prefix:
                element.send_keys(prefix)
                time.sleep(random.uniform(0.05, 0.3))  # Random delay to mimic typing the prefix

            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.3)) 

    def random_scroll(self):
        for _ in range(random.randint(1, 3)):
            scroll_amount = random.randint(200, 800)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.5))

    def scroll_down(self, pause_time=2):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)


    def simulate_mouse_movement(self,element):
        action = ActionChains(self.driver)
        action.move_to_element(element).perform()
        # Randomized small movements
        x_offset = random.randint(-10, 10)
        y_offset = random.randint(-10, 10)
        pyautogui.moveRel(x_offset, y_offset, duration=random.uniform(0.1, 0.5))




    def login_to_linkedin(self):

        account= "matthieu@fribl.co"
        password= "Patapon77"
    
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(3)


      
    


        #fill in email field

        try:
            email_field = self.driver.find_element(By.ID, 'username')
            self.simulate_mouse_movement(email_field)
            self.human_type(email_field,account)
        except NoSuchElementException:
    
            print("Email field not found. Please check the XPath.")
        
        time.sleep(2)

        #fill in password field
        try:
            password_field = self.driver.find_element(By.ID,'password')
            self.simulate_mouse_movement(password_field)
            self.human_type(password_field,password)
        except NoSuchElementException:
            print("Password field not found. Please check the XPath.")

        time.sleep(3)

        self.random_scroll()
        # Click login button
        try:
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            self.simulate_mouse_movement(login_button)
            login_button.click()
        except NoSuchElementException:
            print("Login button not found. Please check the XPath.")
        
        time.sleep(3)

        
        

        # Captcha manual countermesure
        while True:
            try:
                # Wait for the presence of an element indicating successful login
                WebDriverWait(self.driver,5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="global-nav-typeahead"]/input')))
                print(f"succesfully logged in {account}")
                return self.driver
            except TimeoutException:
                print('Difficulty to login, please check if captcha verification is needed')
        





    ##Section 2: Scraping functions##

    """
    Here we will define the scraping variables:

    -Indexscrap: scrap the index, to help user select they want to scrap, after what they will be able to Deepscrap, or Fastscrap
    -Scraping: it goes deep into each profile, goes trough all the details pages


    """


    def scrap_profile_info(self):
                
                """Scrape general profile information like name, job, and location."""
                page_source = BeautifulSoup(self.driver.page_source, 'html.parser')
                info_div = page_source.find('div', class_='mt2 relative')

                if info_div:
                    name = page_source.find('h1').get_text().strip()
                    job = page_source.find('div', class_="text-body-medium break-words").get_text().strip()
                    location = info_div.find('span', class_="text-body-small inline t-black--light break-words").get_text().strip()

                    return {
                        "name": name,
                        "job": job,
                        "location": location
                    }
                return None
    


    def scrap_skills(self):
        """Scrape skills from the skills section using Selenium and BeautifulSoup."""
        
        skills_with_endorsements = []
        unique_skills = set()  # Using a set to ensure uniqueness

        try:
            # Wait for the skills container to be present
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'scaffold-finite-scroll__content'))
            )
            print("Skills section loaded successfully.")

            # Scroll down a few times to ensure everything is loaded
            for _ in range(3):
                self.scroll_down(pause_time=1)

            # Use BeautifulSoup after waiting for the page to load
            skillpage_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find all possible containers that hold skills
            skills_containers = skillpage_soup.find_all('div', class_="scaffold-finite-scroll__content")

            current_skill = None

            for skill_div in skills_containers:
                # Locate all skills under each skill container
                captured_span = skill_div.find_all('span', attrs={'class': 'visually-hidden'})
                print(f"Found {len(captured_span)} skill elements in current container.")

                # Extract the skills and endorsement counts
                for element in captured_span:
                    text = element.get_text().strip()

                    # If the text looks like an endorsement count, associate it with the current skill
                    if "endorsement" in text.lower():
                        if current_skill and current_skill not in unique_skills:
                            skills_with_endorsements.append({
                                "skill": current_skill,
                                "endorsement_count": text
                            })
                            unique_skills.add(current_skill)
                            current_skill = None
                    else:
                        # If it's a skill name, keep it as the current skill
                        current_skill = text

            # Print captured skills and endorsements after the loop finishes
            if skills_with_endorsements:
                for item in skills_with_endorsements:
                    print(f"Skill: {item['skill']}, Endorsement Count: {item['endorsement_count']}")
            else:
                print("No skills found with endorsements for this profile.")

        except TimeoutException:
            print("Timeout while waiting for the skills section to load. The content might be slow to load or blocked.")
        except NoSuchElementException:
            print("Skills section not found on this profile. Check the locator or the page structure.")
        except Exception as e:
            print(f"An error occurred while scraping skills: {e}")

        return skills_with_endorsements if skills_with_endorsements else "No skills found"

    def scrap_education(self):
        """Scrape education details from the education section using Selenium and BeautifulSoup."""
        
        education_details = []
        unique_education = set()  # Using a set to ensure uniqueness

        try:
            # Wait for the education container to be present
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'scaffold-finite-scroll__content'))
            )
            print("Education section loaded successfully.")

            # Scroll down a few times to ensure everything is loaded
            for _ in range(3):
                self.scroll_down(pause_time=1)

            # Use BeautifulSoup after waiting for the page to load
            educationpage_soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Find all possible containers that hold education details
            education_containers = educationpage_soup.find_all('div', class_="scaffold-finite-scroll__content")

            current_education = {}

            for edu_div in education_containers:
                # Locate all education entries under each container
                captured_spans = edu_div.find_all('span', attrs={'class': 'visually-hidden'})
                print(f"Found {len(captured_spans)} education elements in current container.")

                # Extract education details
                for element in captured_spans:
                    text = element.get_text().strip()

                    # Fill in the education fields step by step
                    if not current_education.get("school"):
                        current_education["school"] = text
                    elif not current_education.get("degree"):
                        current_education["degree"] = text
                    elif not current_education.get("field_of_study"):
                        current_education["field_of_study"] = text
                    elif not current_education.get("years_attended"):
                        current_education["years_attended"] = text
                    else:
                        # Append completed education entry and reset for the next one
                        education_details.append(current_education)
                        unique_education.add(current_education["school"])
                        current_education = {
                            "school": text
                        }

                # Append the last education entry if it's complete
                if current_education and current_education.get("school") not in unique_education:
                    education_details.append(current_education)

            # Print captured education details
            if education_details:
                for edu in education_details:
                    print(f"School: {edu.get('school')}, Degree: {edu.get('degree')}, Field of Study: {edu.get('field_of_study')}, Years: {edu.get('years_attended')}")
            else:
                print("No education details found for this profile.")

        except TimeoutException:
            print("Timeout while waiting for the education section to load.")
        except NoSuchElementException:
            print("Education section not found on this profile. Check the locator or the page structure.")
        except Exception as e:
            print(f"An error occurred while scraping education: {e}")

        return education_details if education_details else "No education found"


    def scrap_experience(self):
        """Scrape experience from the experience section by combining Selenium and BeautifulSoup."""
        experiences = []

        try:
            # Wait for the experience section container to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'scaffold-finite-scroll__content'))
            )

            # Scroll down to ensure all experiences are loaded
            self.scroll_down(pause_time=3)

            # Create a BeautifulSoup object after waiting for the experience section to load
            experience_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            experience_div = experience_soup.find('div', class_='scaffold-finite-scroll__content')

            if experience_div:
                captured_spans = experience_div.find_all('span', class_='visually-hidden')

                current_experience = {}
                for element in captured_spans:
                    text = element.get_text().strip()

                    # Extract information based on the order of fields typically present in experience sections
                    if not current_experience.get("job_title"):
                        current_experience["job_title"] = text
                    elif not current_experience.get("company"):
                        current_experience["company"] = text
                    elif not current_experience.get("duration"):
                        current_experience["duration"] = text
                    else:
                        # If all fields are filled, append the experience to the list and reset for the next one
                        experiences.append(current_experience)
                        current_experience = {
                            "job_title": text
                        }

                # Append the last experience if it exists and is complete
                if current_experience:
                    experiences.append(current_experience)

        except NoSuchElementException:
            print("Experience section not found. Please check the XPath or class name.")
        except Exception as e:
            print(f"An error occurred while scraping experience: {e}")

        return experiences if experiences else "No experience found"
    def scrap_certifications(self):
        """Scrape certifications from the certifications section by combining Selenium and BeautifulSoup."""
        certifications = []

        try:
            # Wait for the certifications section container to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'scaffold-finite-scroll__content'))
            )

            # Scroll down to ensure all certifications are loaded
            self.scroll_down(pause_time=3)

            # Create a BeautifulSoup object after waiting for the certifications section to load
            certification_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            certification_div = certification_soup.find('div', class_='scaffold-finite-scroll__content')

            if certification_div:
                captured_spans = certification_div.find_all('span', class_='visually-hidden')

                current_certification = {}
                for element in captured_spans:
                    text = element.get_text().strip()

                    # Extract information in a similar order as the certification section fields typically appear
                    if not current_certification.get("certification_name"):
                        current_certification["certification_name"] = text
                    elif not current_certification.get("issuing_organization"):
                        current_certification["issuing_organization"] = text
                    elif not current_certification.get("issued_date"):
                        current_certification["issued_date"] = text
                    else:
                        # If all fields are filled, append the certification to the list and reset for the next one
                        certifications.append(current_certification)
                        current_certification = {
                            "certification_name": text
                        }

                # Append the last certification if it exists and is complete
                if current_certification:
                    certifications.append(current_certification)

        except NoSuchElementException:
            print("Certifications section not found. Please check the XPath or class name.")
        except Exception as e:
            print(f"An error occurred while scraping certifications: {e}")

        return certifications if certifications else "No certifications found"
    

    def scrap_languages(self):
        """Scrape languages from the languages section by combining Selenium and BeautifulSoup."""
        languages = []

        try:
            # Wait for the languages section container to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'scaffold-finite-scroll__content'))
            )

            # Scroll down to ensure all languages are loaded
            self.scroll_down(pause_time=3)

            # Create a BeautifulSoup object after waiting for the languages section to load
            languages_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            languages_div = languages_soup.find('div', class_='scaffold-finite-scroll__content')

            if languages_div:
                captured_spans = languages_div.find_all('span', class_='visually-hidden')
                for element in captured_spans:
                    text = element.get_text().strip()
                    languages.append(text)

        except NoSuchElementException:
            print("Languages section not found. Please check the XPath or class name.")
        except Exception as e:
            print(f"An error occurred while scraping languages: {e}")

        return languages if languages else "No languages found"


    def scrap_recommendations(self):
        """Scrape recommendations from the recommendations section by combining Selenium and BeautifulSoup."""
        recommendations = []

        try:
            # Wait for the recommendations section container to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'scaffold-finite-scroll__content'))
            )

            # Scroll down to ensure all recommendations are loaded
            self.scroll_down(pause_time=3)

            # Create a BeautifulSoup object after waiting for the recommendations section to load
            recommendation_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            recommendation_div = recommendation_soup.find('div', class_='scaffold-finite-scroll__content')

            if recommendation_div:
                captured_spans = recommendation_div.find_all('span', class_='visually-hidden')
                for element in captured_spans:
                    text = element.get_text().strip()
                    recommendations.append(text)

        except NoSuchElementException:
            print("Recommendations section not found. Please check the XPath or class name.")
        except Exception as e:
            print(f"An error occurred while scraping recommendations: {e}")

        return recommendations if recommendations else "No recommendations found"


    def scrap_courses(self):
        """Scrape courses from the courses section by combining Selenium and BeautifulSoup."""
        courses = []

        try:
            # Wait for the courses section container to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'scaffold-finite-scroll__content'))
            )

            # Scroll down to ensure all courses are loaded
            self.scroll_down(pause_time=3)

            # Create a BeautifulSoup object after waiting for the courses section to load
            course_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            course_div = course_soup.find('div', class_='scaffold-finite-scroll__content')

            if course_div:
                captured_spans = course_div.find_all('span', class_='visually-hidden')
                for element in captured_spans:
                    text = element.get_text().strip()
                    courses.append(text)

        except NoSuchElementException:
            print("Courses section not found. Please check the XPath or class name.")
        except Exception as e:
            print(f"An error occurred while scraping courses: {e}")

        return courses if courses else "No courses found"


        
    def scrap_organizations(self):
        """Scrape organizations from the organizations section by combining Selenium and BeautifulSoup."""
        organizations = []

        try:
            # Wait for the organizations section container to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'scaffold-finite-scroll__content'))
            )

            # Scroll down to ensure all organizations are loaded
            self.scroll_down(pause_time=3)

            # Create a BeautifulSoup object after waiting for the organizations section to load
            organization_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            organization_div = organization_soup.find('div', class_='scaffold-finite-scroll__content')

            if organization_div:
                captured_spans = organization_div.find_all('span', class_='visually-hidden')
                for element in captured_spans:
                    text = element.get_text().strip()
                    organizations.append(text)

        except NoSuchElementException:
            print("Organizations section not found. Please check the XPath or class name.")
        except Exception as e:
            print(f"An error occurred while scraping organizations: {e}")

        return organizations if organizations else "No organizations found"



    def scrap_interests(self):
        """Scrape interests from the interests section by combining Selenium and BeautifulSoup."""
        interests = []

        try:
            # Wait for the interests section container to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'scaffold-finite-scroll__content'))
            )

            # Scroll down to ensure all interests are loaded
            self.scroll_down(pause_time=3)

            # Create a BeautifulSoup object after waiting for the interests section to load
            interests_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            interests_div = interests_soup.find('div', class_='scaffold-finite-scroll__content')

            if interests_div:
                captured_spans = interests_div.find_all('span', class_='visually-hidden')

                for element in captured_spans:
                    text = element.get_text().strip()
                    interests.append(text)

        except NoSuchElementException:
            print("Interests section not found. Please check the XPath or class name.")
        except Exception as e:
            print(f"An error occurred while scraping interests: {e}")

        return interests if interests else "No interests found"



    def scrap_volunteering(self):
        """Scrape volunteering experiences from the volunteering section by combining Selenium and BeautifulSoup."""
        volunteering = []

        try:
            # Wait for the volunteering section container to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'scaffold-finite-scroll__content'))
            )

            # Scroll down to ensure all volunteering experiences are loaded
            self.scroll_down(pause_time=3)

            # Create a BeautifulSoup object after waiting for the volunteering section to load
            volunteering_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            volunteering_div = volunteering_soup.find('div', class_='scaffold-finite-scroll__content')

            if volunteering_div:
                captured_spans = volunteering_div.find_all('span', class_='visually-hidden')
                for element in captured_spans:
                    text = element.get_text().strip()
                    volunteering.append(text)

        except NoSuchElementException:
            print("Volunteering section not found. Please check the XPath or class name.")
        except Exception as e:
            print(f"An error occurred while scraping volunteering experiences: {e}")

        return volunteering if volunteering else "No volunteering experiences found"
    



    def scrap_activity(self):
        """Scrape recent activity from the activity section by combining Selenium and BeautifulSoup."""
        activity = []

        try:
            # Wait for the activity section container to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'scaffold-finite-scroll__content'))
            )

            # Scroll down to ensure all activity is loaded
            self.scroll_down(pause_time=3)

            # Create a BeautifulSoup object after waiting for the activity section to load
            activity_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            activity_div = activity_soup.find('div', class_='scaffold-finite-scroll__content')


            if activity_div:
                activity_span = activity_div.find_all('span', dir='ltr')
                activity = [span.get_text().strip() for span in activity_span[:100]]

        except NoSuchElementException:
            print("Activity section not found. Please check the XPath or class name.")
        except Exception as e:
            print(f"An error occurred while scraping activity: {e}")

        return activity if activity else "No recent activity found"



    def scrap_profile(
        self,
        url,
        scrap_skills=False,
        scrap_profile_info=False,
        scrap_experience=False,
        scrap_certifications=False,
        scrap_education=False,
        scrap_recommendations=False,
        scrap_interests=False,
        scrap_languages=False,
        scrap_courses=False,
        scrap_organizations=False,
        scrap_volunteering=False,
        scrap_activity=False,
      
    ):
        """Scrape specific information from a profile based on flags."""
        
        # Load the main profile page
        self.driver.get(url)

        profile_data = {}

        # Scrape general profile information
        if scrap_profile_info:
            profile_data.update(self.scrape_profile_info())

        # Scrape skills
        if scrap_skills:
            self.random_scroll()
            time.sleep(random.uniform(1, 3))
            skillpage_url = (url.split('?')[0]) + '/details/skills'
            self.driver.get(skillpage_url)
            profile_data['skills'] = self.scrap_skills()

        # Scrape education

        if scrap_education:
            self.random_scroll()
            time.sleep(random.uniform(1,3)) 
            edupage_url = (url.split('?')[0]) + '/details/education'
            self.driver.get(edupage_url)
            profile_data['education'] = self.scrap_education()


        # Scrape certifications
        if scrap_certifications:
            self.random_scroll()
            time.sleep(random.uniform(1, 3))
            certpage_url = (url.split('?')[0]) + '/details/certifications'
            self.driver.get(certpage_url)
            profile_data['certifications'] = self.scrap_certifications()

        # Scrape experience
        if scrap_experience:
            self.random_scroll()
            time.sleep(random.uniform(1, 3))
            exppage_url = (url.split('?')[0]) + '/details/experience'
            self.driver.get(exppage_url)
            profile_data['Experience'] = self.scrap_experience()

        # Scrape languages

        if scrap_interests:
            self.random_scroll()
            time.sleep(random.uniform(1, 3))
            interestpage_url = (url.split('?')[0]) + '/details/interests'
            self.driver.get(interestpage_url)
            profile_data['interests'] = self.scrap_interests()

        
        if scrap_languages:
            self.random_scroll()
            time.sleep(random.uniform(1, 3))
            languagepage_url = (url.split('?')[0]) + '/details/languages'
            self.driver.get(languagepage_url)
            profile_data['languages'] = self.scrap_languages()

        # Scrape recommendations
        if scrap_recommendations:
            self.random_scroll()
            time.sleep(random.uniform(1, 3))
            recommendationpage_url = (url.split('?')[0]) + '/details/recommendations'
            self.driver.get(recommendationpage_url)
            profile_data['recommendations'] = self.scrap_recommendations()

        # Scrape courses
        if scrap_courses:
            self.random_scroll()
            time.sleep(random.uniform(1, 3))
            coursepage_url = (url.split('?')[0]) + '/details/courses'
            self.driver.get(coursepage_url)
            profile_data['courses'] = self.scrap_courses()

        # Scrape organizations
        if scrap_organizations:
            self.random_scroll()
            time.sleep(random.uniform(1, 3))
            organizationpage_url = (url.split('?')[0]) + '/details/organizations'
            self.driver.get(organizationpage_url)
            profile_data['organizations'] = self.scrape_organizations()

        # Scrape volunteering experiences
        if scrap_volunteering:
            self.random_scroll()
            time.sleep(random.uniform(1, 3))
            volunteeringpage_url = (url.split('?')[0]) + '/details/volunteering-experiences'
            self.driver.get(volunteeringpage_url)
            profile_data['volunteering'] = self.scrap_volunteering()

        # Scrape recent activity
        if scrap_activity:
            self.random_scroll()
            time.sleep(random.uniform(1, 3))
            activitypage_url = (url.split('?')[0]) + '/recent-activity/all'
            self.driver.get(activitypage_url)
            profile_data['activity'] = self.scrap_activity()

        return profile_data

    def scrap_latest_company_post(self):
            """Scrape the latest post from a profile's company post section."""
            latest_post = {}

            try:
                # Wait for the company posts section to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'feed-shared-update-v2__description-wrapper'))
                )
                print("Company posts section loaded successfully.")
                
                # Create a BeautifulSoup object after waiting for the company posts section to load
                post_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                post_div = post_soup.find('div', class_='feed-shared-update-v2__description-wrapper')

                if post_div:
                    print("Post div found.")
                    
                    # Find all <span> and <a> tags within the post div to gather the complete text
                    post_text_parts = post_div.find_all(['span', 'a'], recursive=True)

                    # Clean up and concatenate the text from each part while avoiding duplicates
                    seen_text = set()  # To keep track of unique text parts
                    complete_post_text = ' '.join([part.get_text().strip() for part in post_text_parts 
                                                if part.get_text().strip() and part.get_text().strip() not in seen_text 
                                                and not seen_text.add(part.get_text().strip())])
                    
                    # Store the cleaned-up post in the dictionary
                    latest_post['latest_post'] = complete_post_text
                else:
                    print("No post div found.")

            except NoSuchElementException:
                print("Company posts section not found. Please check the XPath or class name.")
            except Exception as e:
                print(f"An error occurred while scraping the latest post: {e}")

            return latest_post if latest_post else "No latest post found."

    def scrap_job_openings(self):
        """Scrape the amount of job openings from a company's LinkedIn page."""
        
        job_openings_data = {}
        
        try:
            # Wait for the job openings section to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'org-jobs-job-search-form-module__job-search-container'))
            )
            print("Job openings section loaded successfully.")

            # Parse the page source using BeautifulSoup
            job_openings_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Locate the div with the job openings info
            job_openings_div = job_openings_soup.find('div', class_='org-jobs-job-search-form-module__job-search-container')

            if job_openings_div:
                # Find the <h4> element containing the job openings text
                job_openings_text = job_openings_div.find('h4', class_='org-jobs-job-search-form-module__headline')

                if job_openings_text:
                    # Extract the number of job openings from the text using regex or splitting
                    job_openings = job_openings_text.get_text().strip()

                    # Optionally, extract the number of job openings using regex
                    import re
                    job_openings_count = re.search(r'\d[\d,]*', job_openings)
                    if job_openings_count:
                        job_openings_data['job_openings'] = job_openings_count.group().replace(',', '')
                    else:
                        job_openings_data['job_openings'] = "Job openings information not found."

            else:
                print("Job openings div not found.")
        
        except NoSuchElementException:
            print("Job openings section not found. Please check the class name.")
        
        return job_openings_data


    def scrap_company_about(self):
       
        """Scrape the about section of a company's LinkedIn page."""
        about_data = {}

        try:
            # Wait for the about section to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'org-grid__content-height-enforcer'))
            )
            print("About section loaded successfully.")

            # Create a BeautifulSoup object after waiting for the about section to load
            about_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            about_div = about_soup.find('div', class_='org-grid__content-height-enforcer')

            if about_div:
                # Find all <p> tags within the about div to gather the complete text
                about_paragraphs = about_div.find_all('p', recursive=True)
                
                # Clean up and concatenate the text from each paragraph
                complete_about_text = ' '.join([p.get_text().strip() for p in about_paragraphs if p.get_text().strip()])
                
                # Store the cleaned-up about text in the dictionary
                about_data['about'] = complete_about_text
            else:
                print("No about div found.")

        except NoSuchElementException:
            print("About section not found. Please check the XPath or class name.")
        except Exception as e:
            print(f"An error occurred while scraping the about section: {e}")

        return about_data if about_data else "No about section found."



    def scrap_company(self, url, latest_post=False, about=False, job_openings=False):
        """Navigate to a profile URL and click on the company link in the first experience."""
        company_data = {}

        try:
            # Navigate to the profile URL
            self.driver.get(url)
            
            # Wait for the experience container to be present
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'scaffold-finite-scroll__content'))
            )
            print("Experience section loaded successfully.")

            # Find the first experience container
            experience_div = self.driver.find_element(By.CLASS_NAME, 'scaffold-finite-scroll__content')

            if experience_div:
                self.random_scroll()
                # Find the <a> tag with the company link (we're using 'experience_company_logo' as a data field indicator)
                company_link_element = experience_div.find_element(By.XPATH, "//a[@data-field='experience_company_logo']")
                self.driver.execute_script("arguments[0].click();", company_link_element)
                
                print("Clicked on the company link and navigated to the company's LinkedIn page.")
                time.sleep(random.uniform(1, 3))
                
                # Get the current company URL
                company_url = self.driver.current_url
                print(f"Company URL: {company_url}")
                
                # Check if '/posts/?feedView=all' is already in the URL before appending it
                if latest_post:
                    time.sleep(random.uniform(1, 3))
                    if '/posts/?feedView=all' not in company_url:
                        latestpost_url = company_url.split('?')[0] + '/posts/?feedView=all'
                        self.driver.get(latestpost_url)
                        print(f"Navigated to the company's posts page: {latestpost_url}")
                    else:
                        print("Already on the posts page.")

                    # Scrape the latest post
                    company_data['Company Latest Post'] = self.scrap_latest_company_post()

                if about:
                    time.sleep(random.uniform(1, 3))
                    self.random_scroll()
                    # Clean up the URL by removing any unwanted segments like '/posts' or others
                    company_url = company_url.split('/posts')[0]  # Remove '/posts' and anything after it

                    # Check if '/about/' is already in the URL before appending it
                    if '/about/' not in company_url:
                        about_url = company_url + '/about/'
                        self.driver.get(about_url)
                        print(f"Navigated to the company's about page: {about_url}")
                    else:
                        print("Already on the about page.")

                    # Scrape the about section
                    company_data['Company About'] = self.scrap_company_about()

                if job_openings:
                    self.random_scroll()
                    time.sleep(random.uniform(1, 3))
                    company_url = company_url.split('/posts')[0]  # Remove '/about' and anything after it
                    # Check if '/jobs/' is already in the URL before appending it
                    if '/jobs/' not in company_url:
                        jobs_url = company_url.split('?')[0] + '/jobs/'
                        self.driver.get(jobs_url)
                        print(f"Navigated to the company's jobs page: {jobs_url}")
                    else:
                        print("Already on the jobs page.")

                    # Scrape the jobs section
                    company_data['Job Openings'] = self.scrap_job_openings()



            
            else:
                print("Experience section not found on this profile, unable to click on the company link.")

        except TimeoutException:
            print("Timeout while waiting for the experience section to load.")
        except NoSuchElementException:
            print("Company link not found.")
        except Exception as e:
            print(f"An error occurred while clicking the company link: {e}")

        return company_data if company_data else "No company data found."


    def quit_driver(self):
            """Quit the driver when all scraping is done."""
            self.driver.quit()







