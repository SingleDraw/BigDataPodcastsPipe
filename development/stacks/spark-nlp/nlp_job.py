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
# args.output = "abfs://whisper@devstoreaccount1.dfs.core.windows.net/output" # Use Azure Blob Storage (ABFS) for output

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
