# Data Directory README

This directory contains data files for the multilingual risk evaluation project.

## Structure

- `prompts/`: Directory for storing generated and custom evaluation prompts
- `sample_data/`: Sample datasets and examples
- `results/`: Evaluation results and analysis files (created during runtime)

## Prompt Files

Evaluation prompts are generated automatically by the system but can also be manually created and stored as JSON files in the `prompts/` directory.

### Format

Prompt files should follow this JSON structure:

```json
[
  {
    "id": "unique_prompt_id",
    "prompt": "The actual prompt text",
    "language": "en",
    "domain": "healthcare",
    "base_prompt": "Original prompt without template formatting",
    "risk_level": "high"
  }
]
```

### Supported Languages

- `en`: English
- `zh`: Chinese (Simplified)
- `es`: Spanish
- `fr`: French

### Supported Domains

- `healthcare`: Medical and health-related scenarios
- `legal`: Legal advice and representation scenarios
- `education`: Educational assessment and guidance scenarios

## Custom Prompts

You can add custom prompts by creating JSON files in the `prompts/` directory. The system will automatically load and include them in evaluations when specified in the configuration.

## Notes

- All prompt files should use UTF-8 encoding to support multilingual content
- Prompts are designed to test model responses in high-risk scenarios
- Results are automatically saved to timestamped files to prevent overwrites