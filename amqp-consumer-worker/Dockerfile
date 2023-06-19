FROM python:slim
ADD worker.py .
RUN pip install pika
CMD ["python", "-u", "worker.py"] 