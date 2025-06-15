
import os, json, pathlib

def convert_to_json_segments(
        input_file: str,
        # output_file: str
    ) -> list:
    """
    Convert a subtitle formatted file 
    to JSON format with start, end, and text fields.
    syntax:
    [00:00:00 --> 00:00:06] The Joe Rogan experience.
    results in:
    [
      {"start": 0.0, "end": 6.0, "text": "The Joe Rogan experience."}
    ]
    """
    with open(input_file, "r") as f:
        lines = f.readlines()
        segments = []
        for line in lines:
            if line.startswith("[") and "-->" in line:
                time_part, text_part = line.split("] ", 1)
                start_end = time_part[1:].split(" --> ")
                start = float(start_end[0].replace(":", "")) / 100
                end = float(start_end[1].replace(":", "")) / 100
                text = text_part.strip()
                segments.append({"start": start, "end": end, "text": text})
        # Save to JSON
        # with open(output_file, "w") as json_file:
        #     json.dump(segments, json_file, indent=4)
        # print(f"Converted {len(lines)} lines to JSON format.")
        return segments




def segment_paragraphs(
        segments: list, 
        max_pause: float =6.5, 
        max_chars: int =1400
    ) -> list:
    """
    Segment paragraphs based on pauses and character limits.
    Args:
        segments (list): List of segments with start, end, and text.
        max_pause (float): Maximum pause duration in seconds to consider a new paragraph.
        max_chars (int): Maximum number of characters in a paragraph.
    Returns:
        list: List of segmented paragraphs with start, end, and text.
    """
    paragraphs = []
    current = {
        "start": segments[0]["start"],
        "text": "",
        "end": segments[0]["end"]
    }

    for seg in segments:
        pause = seg["start"] - current["end"]
        # Start new paragraph if long pause or chunk gets too long
        if pause > max_pause or len(current["text"]) > max_chars:
            paragraphs.append(current)
            current = {
                "start": seg["start"],
                "text": seg["text"].strip(),
                "end": seg["end"]
            }
            # Tag segments with `episode_id`, `segment_id`, `timestamp`, etc., for Spark or downstream tools.
            current["episode_id"] = "episode_1"
            current["segment_id"] = len(paragraphs) + 1
        else:
            current["text"] += " " + seg["text"].strip()
            current["end"] = seg["end"]

    # Append final paragraph
    if current["text"]:
        paragraphs.append(current)

    return paragraphs


if __name__ == "__main__":
    paragraphs = segment_paragraphs(
        segments = convert_to_json_segments("input/podcast_joe.srt")
    )

    # Save to JSON
    with open("output/podcast_joe_segmented.json", "w") as json_file:
        json.dump(paragraphs, json_file, indent=4)


