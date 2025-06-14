import re
import unicodedata

def normalize_title(
        title: str,
        stopwords: list[str] = [
            "the", "a", "an", "show", "episode", #"podcast", "experience",
            "with", "and", "featuring", "versus", "by", "of", "in", "on", "for",
            "to", "at", "from", "about", "as", "that", "this", "it", "is"
        ],
        replacement: list[tuple[str, str]] = [
            ("/w", "with"), 
            ("w/", "with"), 
            ("&", "and"), 
            ("feat.", "featuring"), 
            ("ft.", "featuring"), 
            ("vs.", "versus"),
            ("vs", "versus"),
            ("ep.", "episode"), 
            ("ep", "episode")
        ]
    ) -> str:
        """
        Normalize podcast titles for better matching.
        - Lowercase the title
        - Normalize common abbreviations and symbols
        - Normalize unicode (e.g. remove accents, forms like é, ñ)
        - Encode to ASCII and decode back to string, ignoring errors
        - Remove standalone numbers
        - Remove syntax like s01e01, ep01, season 1 episode 1, season 1 ep 1
        - Remove punctuation
        - Remove common stopwords
        - Replace multiple spaces with a single space
        """

        # Normalize the title to lowercase
        title = title.lower()

        # Normalize common abbreviations and symbols
        for old, new in replacement:
            title = title.replace(old, new)

        # Normalize unicode (e.g. remove accents, forms like é, ñ)
        title = unicodedata.normalize("NFKD", title)
        
        # Encode to ASCII and decode back to string, 
        # ignoring errors to remove non-ASCII characters (e.g. emojis)
        title = title.encode("ascii", "ignore").decode()

        # remove sytax s01e01 using regex
        title = re.sub(r'\bs\d{1,2}e\d{1,2}\b', '', title)

        # Remove syntax like ep01, season 1 episode 1, season 1 ep 1 using regex
        title = re.sub(r'\b(?:ep|episode|saison|season)\s*\d{1,2}\b', '', title)

        # Remove standalone numbers using regex
        title = re.sub(r'\b\d+\b', '', title)

        # Remove punctuation using regex
        title = re.sub(r'[^\w\s]', '', title)

        # Remove common stopwords
        title = ' '.join(word for word in title.split() if word not in stopwords)

        # Replace multiple spaces with a single space
        title = re.sub(r'\s+', ' ', title) 

        return title.strip()
