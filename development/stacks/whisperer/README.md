
### Speech transcription using Whisperer

# Build Whisperer images using [./development.sh] bash script menu in this monorepo root.

# Docker example samlpe command to run batch transcription job:
there must be:
- [sample2.mp3] file present in [s3://whisper/sample1.mp3] location of local s3 seaweedfs 
  > use this link to download audio and rename it to [sample2.mp3]:
  [https://d38nvwmjovqyq6.cloudfront.net/va90web25003/companions/ws_smith/17%20French%20Nasal%20Vowels.mp3]
  > use http://localhost:8899 web ui for quick upload

- [batch.json] file present in [s3://whisper/batch.json] location with a content:

```json
[
    {
        "input": "https://d38nvwmjovqyq6.cloudfront.net/va90web25003/companions/ws_smith/1%20Comparison%20Of%20Vernacular%20And%20Refined%20Speech.mp3",
        "output": "default+az://whisperer/transcribed_raw/output_speech_sample_transcription.txt"
    },
    {
        "input": "seaweedfs+s3://whisperer/sample2.mp3",
        "output": "default+az://whisperer/transcribed_raw/french_nasal_vowels_sample_transcription.txt"
    }
]
```
- [default+az] will resolveas default azure configuration for the sink, based on environment variables provided in compose yml file.
  > NOTE: [seaweedfs] is Whisperer baked in configuration for local seaweed s3 storage


### Run this example from development.sh menu or like this:
```bash
# Batch submit command:
docker exec whisperer-submitter whisperer-submit --batch seaweedfs+s3://whisperer/batch.json
```

### Additional baked in configurations:
- should be mounted as files with *.properties extension in /app/config directory on Whisperer workers
- Whisperer accepts two types of storages: Azure Blob and S3 storage.
