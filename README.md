# Proof — LLM Evaluation Platform

## Dataset CSV Format

To evaluate your model with rule-based scorers and expected outputs, structure your dataset CSV file with the following columns:

```csv
input,expected,regex,min_words,max_words,required_keywords,forbidden_keywords,requires_json
"What is the capital of France?","Paris","Paris",1,10,"Paris","London",false
"How many seconds are in 3.5 hours?","12600","\\d+",1,5,"12600","error",false
```

### Column Descriptions
- `input`: The prompt/question sent to the LLM.
- `expected`: The expected target answer for the LLM judge.
- `regex`: (Optional) Regular expression pattern the response must match.
- `min_words`: (Optional) Minimum word count required.
- `max_words`: (Optional) Maximum word count allowed.
- `required_keywords`: (Optional) Comma-separated words that must be present in the response.
- `forbidden_keywords`: (Optional) Comma-separated words that must NOT be present in the response.
- `requires_json`: (Optional) True/false indicating if the response must be valid JSON.

