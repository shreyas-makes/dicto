# Vocabulary Management Guide

## Overview

The **Vocabulary Management** tab in Dicto's preferences provides a comprehensive interface for managing custom words and proper nouns to improve transcription accuracy. This feature helps Dicto better recognize domain-specific terms, company names, technical jargon, and other specialized vocabulary.

## Accessing Vocabulary Management

1. **Open Dicto Preferences** (Cmd+, or menu bar)
2. **Click the "Vocabulary" tab**

## Features

### 📝 Add Individual Words

**Single Word Entry:**
- Enter a word in the "Add Word" field
- Choose between "Regular Word" or "Proper Noun"
- Press Enter or click "Add Word"

**Proper Nouns vs Regular Words:**
- **Regular Words**: Technical terms, common words (e.g., "kubernetes", "microservices")
- **Proper Nouns**: Names, companies, places (e.g., "Docker", "AWS", "Microsoft")

### 📄 Add Multiple Words

1. Use the "Add Multiple" text area
2. Enter one word per line
3. Select word type (Regular Word/Proper Noun)
4. Click "Add Multiple Words"

### 📁 File Operations

**Load from File:**
Supports multiple formats:

**JSON Format** (`vocabulary.json`):
```json
{
  "words": ["kubernetes", "docker", "microservices"],
  "proper_nouns": ["Amazon", "Microsoft", "OpenAI"],
  "domains": {
    "medical": ["stethoscope", "diagnosis", "prescription"],
    "legal": ["litigation", "defendant", "jurisdiction"]
  }
}
```

**Plain Text Format** (`words.txt`):
```
kubernetes
microservices
containerization
```

**CSV Format** (`vocab.csv`):
```
kubernetes,word
Docker,proper_noun
microservices,word
```

**Export Vocabulary:**
- Export current vocabulary to JSON or text files
- Useful for backup and sharing between systems

### 🗂️ Vocabulary Lists

**Custom Words Tab:**
- View all regular words
- Select multiple words to remove
- Clear all words

**Proper Nouns Tab:**
- View all proper nouns
- Select multiple nouns to remove  
- Clear all proper nouns

### 🏷️ Domain Categories

**Predefined Domains:**
- General
- Medical
- Legal
- Technical
- Business

**Create Custom Domains:**
- Click "Create New Domain"
- Enter domain name
- Organize vocabulary by context

### 📊 Statistics

Real-time display of:
- Total custom words
- Total proper nouns
- Number of domains

## Usage Examples

### Medical Transcription Setup

1. **Create medical vocabulary file** (`medical_terms.json`):
```json
{
  "words": [
    "stethoscope", "diagnosis", "prescription", "symptoms",
    "hypertension", "diabetes", "medication", "treatment"
  ],
  "proper_nouns": [
    "Mayo Clinic", "Johns Hopkins", "Cleveland Clinic",
    "Pfizer", "Johnson & Johnson"
  ]
}
```

2. **Load in Dicto:**
   - Vocabulary tab → "Load from File..." → Select `medical_terms.json`

### Technical Documentation

1. **Add programming terms:**
```
kubernetes
microservices
containerization
API
database
```

2. **Add company names:**
```
Docker
AWS
Microsoft
Google
GitHub
```

### Legal Documents

1. **Add legal terminology:**
```
litigation
defendant
jurisdiction
precedent
```

## Best Practices

### 🎯 Word Selection
- **Focus on domain-specific terms** that standard dictionaries miss
- **Include technical jargon** relevant to your work
- **Add proper nouns** for people, companies, products you frequently mention

### 📋 Organization
- **Use domains** to categorize vocabulary by context
- **Export regularly** for backup purposes
- **Remove unused words** to keep lists manageable

### 🔄 Maintenance
- **Review accuracy** - Remove words that cause more errors
- **Update regularly** - Add new terms as your vocabulary evolves
- **Share vocabularies** - Export and import across team members

## Integration with Transcription

**Automatic Application:**
- Words are automatically used during transcription
- Must enable "Custom vocabulary" in Transcription tab
- Higher confidence scores for recognized custom words

**Context-Aware Suggestions:**
- System provides intelligent suggestions based on transcription context
- Domain-specific words prioritized when context matches

## Storage Location

Vocabulary is stored in:
```
~/.dicto/vocabulary/custom_vocabulary.json
```

**Backup Location:**
Configuration backups include vocabulary data for recovery.

## Troubleshooting

### Words Not Being Recognized
1. Check "Enable custom vocabulary" in Transcription tab
2. Verify words are added correctly (check spelling)
3. Restart transcription engine if needed

### File Loading Issues
1. Check file format (JSON/CSV/TXT)
2. Verify JSON syntax if using JSON format
3. Ensure file encoding is UTF-8

### Performance Considerations
- Large vocabularies (>10,000 words) may slightly impact performance
- Consider domain-specific vocabularies rather than massive general lists
- Remove outdated or rarely used terms

## Advanced Features

### Programmatic Access

For developers, vocabulary can be managed programmatically:

```python
from vocabulary_manager import VocabularyManager

vocab = VocabularyManager()
vocab.add_custom_words(["kubernetes", "docker"])
vocab.add_proper_nouns(["AWS", "Microsoft"])
vocab.save_vocabulary_preferences()
```

### Batch Operations

For large vocabulary lists, use file import:
1. Prepare vocabulary file
2. Use "Load from File" feature
3. Review imported words in lists
4. Export for backup

---

## Quick Reference

| Action | Location | Shortcut |
|--------|----------|----------|
| Open Preferences | Menu Bar | Cmd+, |
| Add Single Word | Vocabulary Tab → Add Word field | Enter |
| Add Multiple | Vocabulary Tab → Multi-line text | - |
| Load File | Vocabulary Tab → File Operations | - |
| Export | Vocabulary Tab → File Operations | - |
| Remove Words | Select in list → Remove Selected | - |
| Clear All | Word list → Clear All | - |

**The vocabulary management system is now fully integrated into the Dicto preferences interface!** 🎉 