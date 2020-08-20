import asyncio
import os
from datetime import datetime
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from asyncio_crawler.crawler import Crawler
from asyncio_crawler.report.file_type import FileType
from asyncio_crawler.report.export import Export
from asyncio_crawler.logger import Logger

AWS_CONNECTION_ID = 'aws_conn'
AWS_BUCKET_NAME = "airflow-crawler-test-bucket"
# ToDo: Fix Unique BucketName with aws_caller_identity.current.account_id
# letters = string.ascii_lowercase
# AWS_BUCKET_NAME = "{}-{}".format("airflow-crawler-test-bucket", ''.join(random.choice(letters) for i in range(10)))


def start_crawler():
    url = "https://www.datadrivers.de"
    logger = Logger()
    crawler = Crawler(url, logger)
    task = asyncio.Task(crawler.crawl())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(task)
    loop.close()
    result = task.result()
    Export().print("csv", result, "urls.csv")


def create_bucket(**context):
    s3_hook = S3Hook(AWS_CONNECTION_ID)
    if not s3_hook.check_for_bucket(bucket_name=AWS_BUCKET_NAME):
        s3_hook.create_bucket(bucket_name=AWS_BUCKET_NAME, region_name='eu-west-1')
        # ToDo: Fix Unspecified Location Constraint for Region eu-west-1
        # - https://dev.to/abhishekamralkar/unspecified-location-constraint-ie2
        # - https://github.com/molei20021/airflow-1-10-9-mod/blob/0888472c8fc9e7c67ea25616d875685ff460a0f0/tests/hooks/test_s3_hook.py

    return s3_hook.check_for_bucket(bucket_name=AWS_BUCKET_NAME)


def upload_object(**context):
    s3_hook = S3Hook(AWS_CONNECTION_ID)
    path = './urls.csv'
    if os.path.isfile(path):
        s3_hook.load_file(
            path,
            key="urls.csv",
            bucket_name=AWS_BUCKET_NAME,
            replace=True,
        )

    return s3_hook.check_for_key(key='urls.csv', bucket_name=AWS_BUCKET_NAME)


dag = DAG(
    "Website-Crawler",
    description="Simple Website Crawler with asyncio",
    schedule_interval="0 12 * * *",
    start_date=datetime(2020, 8, 20),
    catchup=False,
)


crawler_operator = PythonOperator(
    task_id="crawler_task",
    python_callable=start_crawler,
    dag=dag
)

create_bucket = PythonOperator(
    task_id='create_bucket',
    python_callable=create_bucket,
    provide_context=True,
    dag=dag
)

upload_object = PythonOperator(
    task_id='upload_object',
    python_callable=upload_object,
    provide_context=True,
    dag=dag
)

finish = DummyOperator(
    task_id='finish',
    dag=dag
)

crawler_operator >> create_bucket >> upload_object >> finish
