import argparse
import os
import json
from pyspark.sql import SparkSession
from pyspark import SparkConf
import sparknlp
from sparknlp.base import *
from sparknlp.annotator import *
from pyspark.sql.functions import monotonically_increasing_id

"""
pip install --no-cache-dir setuptools pyspark==3.5.0 spark-nlp==5.1.4 numpy
"""


spark = SparkSession.builder.appName("RemoteSparkNLP").getOrCreate()

sparknlp.start() # Start Spark NLP on top of your existing Spark session


# df = spark.read.option("multiLine", True).json(args.input)



spark.stop()