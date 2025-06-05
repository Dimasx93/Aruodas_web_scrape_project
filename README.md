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

1. Clone the repo:

git clone https://github.com/Dimasx93/Aruodas_web_scrape_project.git
cd Aruodas_web_scrape_project

2. (Optional) Create a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

3. Install all dependencies:

pip install -r requirements.txt

4. Run the app:

python app/main.py

