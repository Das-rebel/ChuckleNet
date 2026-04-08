# Reddit Jokes Processing Report

## Validation

- Input file: `/Users/Subho/datasets/manual_acquisition/reddit-jokes/download.json`
- Input exists: `True`
- Input size (MB): `65.48`
- Parser mode: `json_array_stream`
- Total parsed rows: `194553`
- Malformed rows skipped: `0`

## Filters

- Length range: `20` to `500` characters
- Minimum Reddit score: `1`
- Quality threshold: `87.0`
- English-only heuristic: `ascii/function-word/alpha-ratio composite`
- Offensive filter: `hate-slur + explicit-harm + explicit-sexual term blocklist`
- Duplicate filter: `punctuation-insensitive canonical text hash`

## Output Counts

- Accepted jokes: `101609`
- Label 1 rows: `101609`
- Unique canonical jokes kept: `101609`
- Mean quality score: `99.65`
- Mean character length: `121.52`
- Mean word count: `22.72`

## Rejection Counts

- content: `23528`
- duplicate: `8834`
- empty_canonical_text: `2`
- empty_text: `3`
- language: `144`
- length: `23827`
- offensive_or_inappropriate: `6437`
- quality_threshold: `50`
- reddit_score: `57352`

## Success Criteria

- Minimum 50,000 high-quality jokes: `True`
- Mean quality score >= 90: `True`
- CSV created: `True`
- JSON report created: `True`
- Markdown report created: `False`

## Files

- cleaned_csv: `data/training/reddit_jokes/reddit_jokes_humor.csv`
- report_json: `data/training/reddit_jokes/reddit_jokes_processing_report.json`
- report_markdown: `data/training/reddit_jokes/reddit_jokes_processing_report.md`
- latest_checkpoint: `data/training/reddit_jokes/checkpoints/latest_checkpoint.json`

## Sample Accepted Jokes

- `5tz52q`: I hate how you cant even say black paint anymore Now I have to say "Leroy can you please paint the fence?"
- `5tz04j`: I walked into a PETA adoption center and the receptionist asked me what kind of dog I wanted Apparently "Whatever's low in cholesterol" was not the right answer.
- `5tyzxh`: Remember when you were a kid and when you cried your parents said, "I'll give you a reason to cry"? I always thought they were gunna hit me, not that they were going to destroy ...
- `5tyytx`: My boss said to me, "you're the worst train driver ever. How many have you derailed this year?" I said, "I'm not sure; it's hard to keep track."
- `5tyyo2`: If I get a bird I'm naming it Trump cuz all they do is Tweet

## Sample Rejections

- content: `5tz2wj`: Brian raises his hand and says, "He's in Heaven." A Sunday school teacher is concerned that his students might be a little confused about Jesus, so he asks his class, "Where is ...
- content: `5tyx6v`: A mother went into a coma after giving birth to twins When she woke up after 6 months and 3 days, the doctor told the mother: "While you were in a coma, we had your brother name...
- content: `5tyqag`: I've translated a popular Russian joke to English , wanna hear you reaction )) A young boy says to his father "Dad, our math teacher is asking to see you." "What happened?" The ...
- duplicate: `5tsp5j`: It all The title says it all
- duplicate: `5t8z6d`: What happens when you take a joke too far? The 45th President of the United States.
- duplicate: `5t7n4b`: What's red and bad for your teeth? A brick
- empty_canonical_text: `3576hu`: -.. .. -.. + -.-- --- ..- + ... . . + - .... . + .. -. - . .-. -. . - + .--- --- -.- . + .. -. + -- --- .-. ... . + -.-. --- -.. . .. - + .-- .- ... + -.. --- - + -.-. --- -- . ...
- empty_canonical_text: `2wipmt`: ­
- empty_text: `3d78nl`: 
- empty_text: `3c08b2`: 
- empty_text: `2v316r`: 
- language: `5tuxa3`: Old McDonald had a farm... 2.71828 √(-1) 2.71828 √(-1) (5-5)
- language: `5r5ywj`: "Hold my beer." -2017
- language: `52rjmt`: Joke mind blown allahu=6 Akbar=5 6-5=1 9/11 1+11=12. 12-9=3 Illuminati did 9/11
- length: `5tz2wj`: Brian raises his hand and says, "He's in Heaven." A Sunday school teacher is concerned that his students might be a little confused about Jesus, so he asks his class, "Where is ...
- length: `5tyx6v`: A mother went into a coma after giving birth to twins When she woke up after 6 months and 3 days, the doctor told the mother: "While you were in a coma, we had your brother name...
- length: `5tyqag`: I've translated a popular Russian joke to English , wanna hear you reaction )) A young boy says to his father "Dad, our math teacher is asking to see you." "What happened?" The ...
- offensive_or_inappropriate: `5txxq7`: Why is the camel called the ship of the desert? Because its full of Arab semen.
- offensive_or_inappropriate: `5txomv`: What's long and hard and full of semen? A Submarine.
- offensive_or_inappropriate: `5txlkj`: Did you hear the outrage over the rapist getting four years? And he gets to live in the White House to boot!
- quality_threshold: `5sq8qo`: "No" means "NO"!..... Unless she's dyslexic, then **it's ON!**
- quality_threshold: `5s5ysc`: Nerdy pickup line Hey baby, are you a compressed file format, because rar. ^^^^^now ^^^^^where ^^^^^did ^^^^^I ^^^^^put ^^^^^the ^^^^^bleach...
- quality_threshold: `5s03or`: Wanna hear a joke about sodium? Na
- reddit_score: `5tz4dd`: What's the difference between a Jew in Nazi Germany and pizza ? Pizza doesn't scream when you put it in the oven . I'm so sorry.
- reddit_score: `5tz319`: I recently went to America.... ...and being there really helped me learn about American culture. So I visited a shop and as I was leaving, the Shopkeeper said "Have a nice day!"...
- reddit_score: `5tz1pc`: You hear about the University book store worker who was charged for stealing $20,000 worth of books? He got caught trying to sell the two books to a freshman.
