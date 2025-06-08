# 🏡 Aruodas Apartment Analytics Web App


A Flask-based web application that scrapes apartment listings from Aruodas.lt, stores them in a MongoDB database, and provides users with a way to search listings, view individual properties, and analyze market trends like average or median prices.
 

## 🚀 Features

🕸️ Web Scraping: Collects apartment data from aruodas.lt

🧾 MongoDB Storage: Efficient NoSQL storage of listings and user data

🔍 Search Functionality: Filter apartments by price, size, location, etc.

📊 Market Insights: View calculated median and average prices across listings

🔐 User Auth: Register, log in, and save searches securely

🧠 Form Validation: Strong backend validation of input via WTForms

🌐 Responsive UI: Easy-to-use web interface


## 🛠️ Technologies Used

## Tech	- Purpose

Flask -	Web framework

Flask-Login	- User session management

Flask-WTF	- Form handling + CSRF

Flask-Bcrypt	- Password hashing

Flask-PyMongo	- MongoDB integration

MongoDB	- Data storage

Selenium	- Web scraping

BeautifulSoup	- HTML parsing

Pytest	- Testing

WTForms	- Form validation


## 🔗 Links
Project repo: https://github.com/Dimasx93/Aruodas_web_scrape_project.git

My Portfolio: https://dimasx93.github.io/Portfolio/

GitHub: https://github.com/Dimasx93

LinkedIn: https://www.linkedin.com/in/stefano-di-mauro-132620190/

Video tutorial: https://youtu.be/XOjyN4PEl7k

📂 Project Structure

<pre>Aruodas_web_scrape_project/
│
├── app/                        # Flask web app (UI, routes, forms)
│   ├── static/
│   │   └── style.css
│   ├── templates/              # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── search.html
│   │   ├── analysis.html
│   │   └── my_searches.html
│   ├── __init__.py             # Optional if turning `app/` into a package
│   ├── main.py                 # Flask app routes and logic
│   ├── forms.py                # WTForms for registration/search
│   ├── db_init.py              # MongoDB init & user model
│   ├── extensions.py           # Flask extensions setup (bcrypt, login_manager, csrf, etc.)
│   └── tests/
│       ├── __init__.py
│       └── test_webapp.py      # Your web app-specific tests
│
├── scraper_mongodb/                    # Web scraping & DB logic
│   ├── __init__.py
│   ├── aruodas_scraper.py      # BeautifulSoup/Selenium scraper for aruodas.lt
│   ├── properties_mongo_db.py  # MongoDB functions (insert/find properties)
│   ├── schema_validation.py    # JSON schema for property validation
│   └── tests/
│       ├── __init__.py
│       └── test_scraper.py     # Scraper-specific tests
│
├── .coverage                   # Code coverage file
├── requirements.txt            # Python dependencies
└── README.md # Project overview and usage instructions </pre>
 
## 📦Installation


### 1. Clone the repo:


git clone https://github.com/Dimasx93/Aruodas_web_scrape_project.git

cd Aruodas_web_scrape_project

### 2. (Optional) Create a virtual environment:


python -m venv venv

source venv/bin/activate 

On Windows use: venv\Scripts\activate

### 3. Install all dependencies:


pip install -r requirements.txt

### 4. Run the app:


python -m app.main

## Screenshots

## Main page
![Image](https://github.com/user-attachments/assets/eb1b905b-e544-4615-9949-00557d46c81b)

## If the length of the user or password is not in the min of WTF forms you'll get an error message. (img1)
## Or if the password does not have the minimum requirements, you will also get an error message. (img2)

![Image](https://github.com/user-attachments/assets/68bbcd8b-508b-45a0-b18d-d0bb3ce88e8c)

![Image](https://github.com/user-attachments/assets/27d9f7c9-5527-4066-938f-25f565eda8f6)

## You can search using a dropdown for Region field and District.

![Image](https://github.com/user-attachments/assets/e4cbecce-cb58-4118-82a2-45ef334f7404)
![Image](https://github.com/user-attachments/assets/205d715e-61f5-410b-b97e-b03856ae82d9)

## You can also save a search for the future and or delete. 

![Image](https://github.com/user-attachments/assets/73a633d5-0594-47b7-9cdf-89128a1ae557)

## Also you can look up at median values such as Price, Size and more, for top/bottom Regions, or you can look at all of them, or at just a single one.

![Image](https://github.com/user-attachments/assets/db3a7248-55cd-48e7-b12f-5a5fb7c06337)
