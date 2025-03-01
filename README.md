## iMenuManager - Web Application for Restaurant Management 🍽️

iMenuManager is a **web application designed to centralize menu management** for organizations operating multiple canteens within industrial facilities across the country. 🇮🇹

### Table of Contents 📑

*   [Introduction](#introduction)
*   [Technologies](#technologies)
*   [Features](#features)
*   [Future Development](#future-development)
*   [Author](#author)

### Introduction ℹ️

The goal of iMenuManager is to **automate and optimize routine tasks** within the organization, reducing administrative costs and time. Before this application, menu management was done through manual and decentralized processes, such as Excel sheets and email exchanges. iMenuManager offers a centralized infrastructure accessible from various devices (computer, phone, tablet), improving efficiency and reducing errors.

The main idea is to **ensure the ability to manage weekly menus for all facilities** in different areas of Italy.

### Technologies 💻

The project is developed using the following main technologies:

*   **Backend**: **Django**, an open-source web framework written in Python, following the Model-View-Template (MVT) pattern. Django was chosen for its completeness, versatility, and security.
*   **Frontend**: **Bootstrap**, a frontend component library for creating responsive and mobile-first web interfaces. Bootstrap was selected for its ease of use and support for responsive design.
*   **Database**: **SQLite**, a lightweight and serverless database, ideal for applications requiring simple configuration and portability.
*   **Web Server**: **Nginx** and **Gunicorn** for application deployment. Nginx acts as a reverse proxy, manages requests asynchronously, and offers caching and load balancing features . Gunicorn is a WSGI server that translates Nginx requests into a format manageable by Django.

### Features ✨

iMenuManager offers the following main features:

*   **User Management**: Authentication, authorization, and role management (chef, chef manager, area managers, directional users, plant managers).
*   **Facility Management**: Creation, modification, and visualization of facilities, with information on geographic area and classification.
*   **Recipe Management**: Creation, modification, approval, and visualization of recipes, with the ability to associate ingredients, tags, courses, and images.
*   **Menu Management**: Creation, modification, approval, and visualization of weekly menus for each facility, with cost analysis, allergen information, and modification history features.
*   **Order Generation**: Creation of weekly ingredient orders based on menus.
*   **Analysis**: Analysis of ingredients and dishes used in previous weeks' menus.
*   **Reporting**: Download reports in PDF format, including menus and recipe books.

### Future Development 🔭

During the testing phase, several ideas emerged to **improve and expand the system's features**:

*   Graphical improvements to the user interface.
*   Display of the total number of calories for each dish on the menu.
*   Express quantities in kg instead of grams in the PDF generated when placing an order.
*   Ability to change the individual quantities of the various ingredients present when modifying a recipe.
*   Implementation of an inventory area for each facility.
*   Option to add only dishes created by the facility itself when creating a menu.

### Author 👨‍💻

*   Alberto Cotumaccio