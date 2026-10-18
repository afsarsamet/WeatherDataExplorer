**Project  — Weather Data Explorer — A Pythonic Analysis Toolkit**

**Objective:**

Build a well-structured, object-oriented Python toolkit that loads, cleans, analyses and visualizes historical weather data for several cities.

**Description:**

Students will design a small package of classes (e.g., WeatherStation, Measurement, Report) that read raw CSV/JSON data (e.g., from the Meteostat or NOAA open datasets), validate it, and compute statistics such as monthly averages, extremes, trends and anomaly days. The focus is on idiomatic Python: data structures, list and dict comprehensions, custom exceptions for malformed data, and effective use of the Standard Library. Numerical work is done with NumPy and results are presented with Matplotlib.

**Core Techniques:**

- Object-oriented design: classes, inheritance, dunder methods, dataclasses
- List/dict comprehensions, collections (Counter, defaultdict), itertools
- Exception handling with custom exception classes and logging
- Standard Library: csv, json, pathlib, datetime, argparse, statistics
- NumPy vectorized computations and Matplotlib plots (line, histogram, heatmap)
- Unit testing with unittest or pytest

**Deliverable:**

A command-line application (argparse) that generates a PDF/PNG report with statistics and plots for selected cities and periods, accompanied by unit tests and a short design document (class diagram).

**Difficulty (team of 2):**

**2 / 10 — Easy.** Uses only the Python fundamentals of the first part of the course and requires no machine learning. Data is easy to obtain. The challenge is code quality: a clean class design, proper error handling and tests. Suitable for teams who want a solid but low-risk project.