import json, sys
import sparknlp
from sparknlp.base import *
from sparknlp.annotator import *

sys.exit(1)

print("Starting Spark NLP...")

# Start Spark NLP session
spark = sparknlp.start()

# Start Spark NLP on top of your existing Spark session
sparknlp.start(spark)

def preprocess_paragraphs(
        paragraphs: list
    ) -> list:
    """
    Preprocess paragraphs by cleaning text, tokenizing, removing stopwords, and lemmatizing/stemming.
    Args:
        paragraphs (list): List of paragraphs with 'text' field.
    Returns:
        list: Cleaned paragraphs.
    """
    # Create Spark DataFrame
    df = spark.createDataFrame(paragraphs)

    # Spark NLP pipeline
    document_assembler = DocumentAssembler().setInputCol("text").setOutputCol("document")
    tokenizer = Tokenizer().setInputCols(["document"]).setOutputCol("token")
    normalizer = Normalizer().setInputCols(["token"]).setOutputCol("normalized").setLowercase(True).setCleanupPatterns(["[^\\w\\d\\s]"])
    stopwords_cleaner = StopWordsCleaner().setInputCols("normalized").setOutputCol("cleanTokens").setCaseSensitive(False)
    lemmatizer = LemmatizerModel.pretrained().setInputCols(["cleanTokens"]).setOutputCol("lemma")

    finisher = Finisher().setInputCols(["lemma"]).setOutputCols(["finished"]).setCleanAnnotations(True)

    pipeline = Pipeline(stages=[
        document_assembler,
        tokenizer,
        normalizer,
        stopwords_cleaner,
        lemmatizer,
        finisher
    ])

    # Run pipeline
    model = pipeline.fit(df)
    result = model.transform(df)

    # Collect cleaned text
    cleaned = result.select("finished").rdd.flatMap(lambda row: row).collect()

    # Save back into paragraph structure
    for i, tokens in enumerate(cleaned):
        paragraphs[i]["text"] = ' '.join(tokens)




# # Load your paragraphs (list of dicts with "text")
# with open("input/podcast_joe_segmented.json", "r") as f:
#     paragraphs = json.load(f)

# # Preprocess paragraphs
# paragraphs = preprocess_paragraphs(paragraphs)

# # Save to file
# with open("output/podcast_joe_segmented_cleaned.json", "w") as json_file:
#     json.dump(paragraphs, json_file, indent=4)
