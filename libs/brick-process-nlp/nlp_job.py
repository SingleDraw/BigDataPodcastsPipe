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
Spark NLP pipeline for preprocessing paragraphs.

spark-submit \
  --master spark://<spark-master>:7077 \
  --deploy-mode cluster \
  --jars /app/jars/spark-nlp_2.12-5.1.0.jar \
  nlp_job.py \
  --input /data/transcriptions/joe.json \
  --output /data/cleaned/joe_cleaned/

  
# Option 1: Process All Files in One Spark Job
spark-submit ... nlp_job.py \
  --input "/data/transcriptions/*.json" \
  --output /data/cleaned/all_cleaned/

# Option 2: Process Each File in Its Own Job (Parallel Jobs)
for f in /data/transcriptions/*.json; do
  out="/data/cleaned/$(basename "$f" .json)_cleaned/"
  spark-submit ... nlp_job.py --input "$f" --output "$out" &
done
wait

# Option 3: Provide a List of Files
spark-submit ... nlp_job.py \
  --inputs "/data/transcriptions/1.json,/data/transcriptions/2.json" \
  --output /data/cleaned/all_cleaned/

# And parse the list:
inputs = args.inputs.split(",")
df = spark.read.json(inputs) # df = spark.read.json(["file1.json", "file2.json", "file3.json"])

## Now Spark treats it as one unified DataFrame. 
# To distinguish between the original files in the output, 
# you need to explicitly track file-level metadata, for example:

# Option 1: Add file name as a column
from pyspark.sql.functions import input_file_name
df = spark.read.json(["file1.json", "file2.json", "file3.json"])
df = df.withColumn("source_file", input_file_name())

# Option 2: Add ID inside each file (if you control file content)
# Each input JSON can contain a field like "file_id": "123", and you simply preserve that during processing.

# Option 3: Partition output by input source
# This creates folders like output/source_file=file1.json/ etc.
df.write.partitionBy("source_file").json("output/")


"""


# Parse CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="Input JSON path")
parser.add_argument("--output", required=True, help="Output directory path")
args = parser.parse_args()

spark = SparkSession.builder.appName("RemoteSparkNLP").getOrCreate()


sparknlp.start() # Start Spark NLP on top of your existing Spark session

# spark.read.option("mode", "PERMISSIVE").json("your_file.json")

# Read input
import logging
import sys

# PRINT TO DOCKER CONSOLE
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)
msg = "!!!!!!!!!!!!!!!!!! !!!!!!!!!!!!!!!!!!"
logger.error(msg)

print(f"Reading input from {args.input}...")
logger.error(f"Reading input from {args.input}...")

#df = spark.read.json(args.input).withColumn("id", monotonically_increasing_id())
df = spark.read.option("multiLine", True).json(args.input)

# # df show 5 rows
# print("Input DataFrame:")
# df.show(5, truncate=False)
# if df.isEmpty():
#     print(f"No data found in {args.input}. Exiting.")
# print(f"Read from {args.input} successfully.")

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

print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>> Setting up Spark NLP pipeline stages...")
print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>> Setting up Spark NLP pipeline stages...")
print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>> Setting up Spark NLP pipeline stages...")
print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>> Setting up Spark NLP pipeline stages...")
print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>> Setting up Spark NLP pipeline stages...")

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
    result = model.transform(df)

except Exception as e:
    print(f"\n\n\n22 >>>>>>>>>Error running Spark NLP pipeline: {e}")
    exit(1)



### Write JSON output
# result.select("finished").write.mode("overwrite").json(args.output)

## AZURTIE:
# df.write.parquet("wasb://mycontainer@devstoreaccount1.blob.core.windows.net/output")

### Write Parquet output

import os
import shutil
output_path = args.output
if os.path.exists(output_path):
    print(f"Output path {output_path} already exists. Removing it...")
    print(f"Output path {output_path} already exists. Removing it...")
    print(f"Output path {output_path} already exists. Removing it...")
    print(f"Output path {output_path} already exists. Removing it...")
    print(f"Output path {output_path} already exists. Removing it...")
    shutil.rmtree(output_path)
print(f"Writing output to {args.output}...")
print(f"Writing output to {args.output}...")
print(f"Writing output to {args.output}...")
print(f"Writing output to {args.output}...")
print(f"Writing output to {args.output}...")
# result.select("finished").write.mode("overwrite").json(args.output)
result.select("finished").write.mode("overwrite").parquet(args.output) #  output must be a directory, not a file
df = spark.read.parquet(args.output)
df.show(5)

# try:
#     # Write output
#     # result.select("id", "finished").write.mode("overwrite").json(args.output)
#     result.select("finished").write.mode("overwrite").json(args.output)

# except Exception as e:
#     print(f"\n\n\n33 >>>>>>>>>Error writing output to {args.output}: {e}")
#     exit(1)





# # Collect cleaned text
# cleaned = result.select("finished").rdd.flatMap(lambda row: row).collect()

# # Save back into paragraph structure
# for i, tokens in enumerate(cleaned):
#     paragraphs[i]["text"] = ' '.join(tokens)

# return paragraphs





# # Load your paragraphs (list of dicts with "text")
# with open("input/podcast_joe_segmented.json", "r") as f:
#     paragraphs = json.load(f)

#     print(f"Loaded {len(paragraphs)} paragraphs for preprocessing.")
#     print(f"Example paragraph: {paragraphs[0]}")

#     # Preprocess paragraphs
#     paragraphs = preprocess_paragraphs(paragraphs)

#     # Save to file
#     with open("output/podcast_joe_segmented_cleaned.json", "w") as json_file:
#         json.dump(paragraphs, json_file, indent=4)
