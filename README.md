# WebApp

> **This is a showcase project! Its not meant to be used in any way except for trying it out and looking.** 

This project is a simple blogging website written in Python3. It covers account management, database management, the framework Flask as well as back-end and front-end development in general, file handling and a bit of Docker.

# Usage

In order to use the web application, make sure you completed the setup steps and navigated into the App directory.

    python3 run.py --help
    usage: python3 run.py [options]

    options:
    -h, --help  show this help message and exit
    --run       run application
    --cleanup   clean up everything for a clean and fresh new setup
    --setup     setup db and configs
    --sql       start interactive interface for db
    --debug     activate debugging

    Further configurations can be done by editing the config.json file.

To run the application, you first have to set it up.

    python3 run.py --setup

Then you will be able to run the application or start an interactive session with the database.

    python3 run.py --run

The debug option can always be used and the cleanup option for clearing all of the configs, the database and all of the data, so you will have the repository in it's original state.

# Setup

- ## Locally

    1. Clone the repository on your computer.
    
            git clone https://github.com/Avo-Catto/WebApp.git
    
    2. Navigate into the directory and create a virtual environment.
        
            cd WebApp
            python3 -m venv .venv
            
            source .venv/bin/activate   - Linux
            .\venv\Scripts\activate     - Windows
    
    3. Install the dependencies.

            pip install -r requirements.txt

- ## Docker 

    > **Please Note:** 
    > - Docker containers **don't save** any changes if shut down, **all of the data will be lost**.
    > - **Before** setting up the application in a container, make sure you made a [clean up](#usage).

    1. Make sure you are in the **WebApp** directory.
    
    2. Build the container.
    
            sudo docker build . -t webapp_image

    3. Start the container.

            sudo docker run --name webapp -dp 127.0.0.1:8080:8080 webapp_image

# Features

> **Tip:** Searchbar on /explore: searches for title, except the word starts with #, then it's searching for tags

- Create Accounts

- Login / Logout

- View Accounts

- Update Accounts *(like profile image, username, password, ...)*

- Write / Edit / Delete Blogs

- a Search Bar *(search for titles, but can also search for tags by putting a # at the beginning of a word)*

# Credits

- [Profile Image](https://www.flaticon.com/de/kostenlose-icons/katze)