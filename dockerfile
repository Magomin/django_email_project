# Use an official Python image as the base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*


# Set working directory
WORKDIR /app

# Clone the GitHub repository
RUN git clone https://github.com/Magomin/django_email_project.git

# Copy requirements.txt and install dependencies
COPY django_email_tracking/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt


# Copy the Django project code into the container
#COPY . /app/

# Expose the port that the Django app runs on
EXPOSE 8000

CMD ["python", "django_email_project/manage.py", "runserver", "0.0.0.0:8000"]