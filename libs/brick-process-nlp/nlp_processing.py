import argparse
import os
import json
from pyspark.sql import SparkSession
from pyspark import SparkConf
import sparknlp
from sparknlp.base import *
from sparknlp.annotator import *
from pyspark.sql.functions import monotonically_increasing_id

# Parse CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="Input JSON path")
parser.add_argument("--output", required=True, help="Output directory path")
args = parser.parse_args()

spark = SparkSession.builder.appName("RemoteSparkNLP").getOrCreate()

sparknlp.start() # Start Spark NLP on top of existing Spark session

# Read input
import logging
import sys

# PRINT TO DOCKER CONSOLE
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

print(f"Reading input from {args.input}...")
logger.error(f"Reading input from {args.input}...")
df = spark.read.option("multiLine", True).json(args.input)

# Spark NLP pipeline
"""
Set up Spark NLP pipeline stages for:
    - DocumentAssembler: Converts text to document format (required by Spark NLP)
    - Tokenizer: Splits text into tokens (words)
    - Normalizer: Cleans tokens (lowercase, remove punctuation)
    - StopWordsCleaner: Removes common stopwords (e.g., "the", "is")
    - Lemmatizer: Reduces words to their base form (e.g., "running" -> "run")
    - Finisher: Converts annotations back to text format (e.g., list of words)
"""

document_assembler = (
        DocumentAssembler()
            .setInputCol("text")
            .setOutputCol("document")
    )

tokenizer = ( 
        Tokenizer()
            .setInputCols(["document"])
            .setOutputCol("token")
    )

normalizer = ( 
        Normalizer()
            .setInputCols(["token"])
            .setOutputCol("normalized")
            .setLowercase(True)
            .setCleanupPatterns(["[^\\w\\d\\s]"]) 
    )

stopwords_cleaner = (
        StopWordsCleaner()
            .setInputCols("normalized")
            .setOutputCol("cleanTokens")
            .setCaseSensitive(False)
    )

lemmatizer = (
        LemmatizerModel
            .load("/app/models/lemma_antbnc")
            .setInputCols(["cleanTokens"])
            .setOutputCol("lemma")
    )
    
finisher = (
        Finisher()
            .setInputCols(["lemma"])
            .setOutputCols(["finished"])
            .setCleanAnnotations(True)
    )

print("Setting up Spark NLP pipeline stages...")

pipeline = Pipeline(stages=[
    document_assembler,
    tokenizer,
    normalizer,
    stopwords_cleaner,
    lemmatizer,
    finisher
])


try:
    # Run pipeline
    model = pipeline.fit(df)
    result_df = model.transform(df)

except Exception as e:
    print(f"\n\n\nError running Spark NLP pipeline: {e}")
    exit(1)

result_df.show(15)

