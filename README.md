### DAGS

Website-Crawler -> crawler_dag.py

A web crawler that, visits HTML pages within the same domain for a given url.
Web crawler will output a file (csv|xml) and for each page a list of assets (e.g. CSS, Images, Javascripts) and links between pages.

To access the file check that a Airflow -> s3 Connection ("aws_conn") exist with format like that: 

Name: aws_conn
Type: S3
Extra: {"aws_access_key_id":"_your_aws_access_key_id_", "aws_secret_access_key": "_your_aws_secret_access_key_"}

ToDo:
Bucketname not unique: airflow-crawler-test-bucket