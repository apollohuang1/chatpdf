# Use an official Python runtime as a parent image
FROM python:3.8-buster

# Set the working directory in the container to /app/src
WORKDIR /app/src

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r /app/requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 3000

# Run gunicorn when the container launches
CMD ["gunicorn", "-w", "4", "--timeout", "180", "app:app", "-b", "0.0.0.0:3000"]

