#!/usr/bin/env python3
"""
Vocabulary Manager - Custom vocabulary and proper noun handling for Dicto
This module provides vocabulary management capabilities to improve transcription accuracy
for domain-specific terms, proper nouns, and custom vocabulary lists.
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Set, Optional, Any
from datetime import datetime


class VocabularyManager:
    """
    Manages custom vocabulary for improved transcription accuracy.
    
    Handles loading, storing, and applying custom vocabulary lists to improve
    transcription accuracy for domain-specific terms and proper nouns.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the VocabularyManager.
        
        Args:
            config_dir: Directory for storing vocabulary configuration. 
                       If None, uses default user config directory.
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up configuration directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Use user's home directory for config
            home_dir = Path.home()
            self.config_dir = home_dir / ".dicto" / "vocabulary"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Vocabulary storage
        self.custom_words: Set[str] = set()
        self.proper_nouns: Set[str] = set()
        self.domain_vocabulary: Dict[str, Set[str]] = {}
        self.word_frequencies: Dict[str, int] = {}
        
        # Configuration files
        self.vocab_file = self.config_dir / "custom_vocabulary.json"
        self.preferences_file = self.config_dir / "preferences.json"
        
        # Load existing vocabulary
        self._load_vocabulary()
        
        self.logger.info(f"VocabularyManager initialized with {len(self.custom_words)} custom words")
    
    def load_custom_vocabulary(self, file_path: str) -> bool:
        """
        Load custom vocabulary from a file.
        
        Supports various formats:
        - JSON: {"words": ["word1", "word2"], "proper_nouns": ["Name1", "Name2"]}
        - Plain text: One word per line
        - CSV: word,type (where type is 'word' or 'proper_noun')
        
        Args:
            file_path: Path to the vocabulary file.
            
        Returns:
            bool: True if loaded successfully, False otherwise.
        """
        try:
            vocab_path = Path(file_path)
            
            if not vocab_path.exists():
                self.logger.error(f"Vocabulary file not found: {file_path}")
                return False
            
            # Determine file format and load accordingly
            if vocab_path.suffix.lower() == '.json':
                return self._load_json_vocabulary(vocab_path)
            elif vocab_path.suffix.lower() == '.csv':
                return self._load_csv_vocabulary(vocab_path)
            else:
                # Assume plain text format
                return self._load_text_vocabulary(vocab_path)
                
        except Exception as e:
            self.logger.error(f"Failed to load vocabulary from {file_path}: {e}")
            return False
    
    def _load_json_vocabulary(self, file_path: Path) -> bool:
        """Load vocabulary from JSON format."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'words' in data:
                words_added = self.add_custom_words(data['words'])
                self.logger.info(f"Added {words_added} words from JSON file")
            
            if 'proper_nouns' in data:
                nouns_added = 0
                for noun in data['proper_nouns']:
                    if self._add_proper_noun(noun):
                        nouns_added += 1
                self.logger.info(f"Added {nouns_added} proper nouns from JSON file")
            
            if 'domains' in data:
                for domain, words in data['domains'].items():
                    self._add_domain_vocabulary(domain, words)
                    self.logger.info(f"Added {len(words)} words for domain '{domain}'")
            
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON format in {file_path}: {e}")
            return False
    
    def _load_csv_vocabulary(self, file_path: Path) -> bool:
        """Load vocabulary from CSV format."""
        try:
            words_added = 0
            nouns_added = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(',')
                    if len(parts) >= 2:
                        word = parts[0].strip()
                        word_type = parts[1].strip().lower()
                        
                        if word_type == 'proper_noun':
                            if self._add_proper_noun(word):
                                nouns_added += 1
                        else:
                            if self._add_custom_word(word):
                                words_added += 1
                    else:
                        # Assume it's just a word
                        if self._add_custom_word(parts[0].strip()):
                            words_added += 1
            
            self.logger.info(f"Added {words_added} words and {nouns_added} proper nouns from CSV file")
            return True
            
        except Exception as e:
            self.logger.error(f"Error reading CSV file {file_path}: {e}")
            return False
    
    def _load_text_vocabulary(self, file_path: Path) -> bool:
        """Load vocabulary from plain text format."""
        try:
            words_added = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith('#'):
                        if self._add_custom_word(word):
                            words_added += 1
            
            self.logger.info(f"Added {words_added} words from text file")
            return True
            
        except Exception as e:
            self.logger.error(f"Error reading text file {file_path}: {e}")
            return False
    
    def add_custom_words(self, words: List[str]) -> int:
        """
        Add multiple custom words to the vocabulary.
        
        Args:
            words: List of words to add.
            
        Returns:
            int: Number of words actually added (excluding duplicates).
        """
        added_count = 0
        for word in words:
            if self._add_custom_word(word):
                added_count += 1
        
        if added_count > 0:
            self._save_vocabulary()
            self.logger.info(f"Added {added_count} new custom words")
        
        return added_count
    
    def _add_custom_word(self, word: str) -> bool:
        """
        Add a single custom word.
        
        Args:
            word: Word to add.
            
        Returns:
            bool: True if word was added, False if it already existed.
        """
        if not word or not isinstance(word, str):
            return False
        
        # Clean and normalize the word
        clean_word = self._clean_word(word)
        if not clean_word:
            return False
        
        if clean_word not in self.custom_words:
            self.custom_words.add(clean_word)
            self.word_frequencies[clean_word] = self.word_frequencies.get(clean_word, 0) + 1
            return True
        
        return False
    
    def _add_proper_noun(self, noun: str) -> bool:
        """
        Add a proper noun to the vocabulary.
        
        Args:
            noun: Proper noun to add.
            
        Returns:
            bool: True if noun was added, False if it already existed.
        """
        if not noun or not isinstance(noun, str):
            return False
        
        # Proper nouns should preserve capitalization
        clean_noun = noun.strip()
        if not clean_noun:
            return False
        
        if clean_noun not in self.proper_nouns:
            self.proper_nouns.add(clean_noun)
            return True
        
        return False
    
    def _add_domain_vocabulary(self, domain: str, words: List[str]) -> int:
        """
        Add vocabulary for a specific domain.
        
        Args:
            domain: Domain name (e.g., "medical", "legal", "technical").
            words: List of domain-specific words.
            
        Returns:
            int: Number of words added for this domain.
        """
        if domain not in self.domain_vocabulary:
            self.domain_vocabulary[domain] = set()
        
        added_count = 0
        for word in words:
            clean_word = self._clean_word(word)
            if clean_word and clean_word not in self.domain_vocabulary[domain]:
                self.domain_vocabulary[domain].add(clean_word)
                added_count += 1
        
        return added_count
    
    def _clean_word(self, word: str) -> str:
        """
        Clean and normalize a word.
        
        Args:
            word: Raw word input.
            
        Returns:
            str: Cleaned word or empty string if invalid.
        """
        # Remove extra whitespace and convert to lowercase for regular words
        cleaned = word.strip().lower()
        
        # Remove non-alphabetic characters except hyphens and apostrophes
        cleaned = re.sub(r"[^a-z\-']", "", cleaned)
        
        # Remove if too short or too long
        if len(cleaned) < 2 or len(cleaned) > 50:
            return ""
        
        return cleaned
    
    def get_vocabulary_suggestions(self, context: str) -> List[str]:
        """
        Get vocabulary suggestions based on context.
        
        Args:
            context: Text context to analyze for relevant vocabulary.
            
        Returns:
            List[str]: Suggested vocabulary words based on context.
        """
        suggestions = []
        
        if not context:
            # Return most frequently used words
            sorted_words = sorted(self.word_frequencies.items(), 
                                key=lambda x: x[1], reverse=True)
            return [word for word, _ in sorted_words[:20]]
        
        context_lower = context.lower()
        
        # Look for domain-specific context clues
        for domain, words in self.domain_vocabulary.items():
            if domain.lower() in context_lower:
                suggestions.extend(list(words)[:10])
        
        # Add proper nouns that might be relevant
        for noun in self.proper_nouns:
            if any(word in context_lower for word in noun.lower().split()):
                suggestions.append(noun)
        
        # Add custom words that appear in context
        for word in self.custom_words:
            if word in context_lower:
                suggestions.append(word)
        
        return list(set(suggestions))[:30]  # Remove duplicates and limit
    
    def save_vocabulary_preferences(self) -> bool:
        """
        Save vocabulary preferences to persistent storage.
        
        Returns:
            bool: True if saved successfully, False otherwise.
        """
        return self._save_vocabulary() and self._save_preferences()
    
    def _save_vocabulary(self) -> bool:
        """Save vocabulary to JSON file."""
        try:
            vocab_data = {
                "custom_words": list(self.custom_words),
                "proper_nouns": list(self.proper_nouns),
                "domain_vocabulary": {k: list(v) for k, v in self.domain_vocabulary.items()},
                "word_frequencies": self.word_frequencies,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.vocab_file, 'w', encoding='utf-8') as f:
                json.dump(vocab_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Vocabulary saved to {self.vocab_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save vocabulary: {e}")
            return False
    
    def _save_preferences(self) -> bool:
        """Save user preferences."""
        try:
            preferences = {
                "vocabulary_enabled": True,
                "auto_suggest": True,
                "proper_noun_capitalization": True,
                "domain_detection": True,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save preferences: {e}")
            return False
    
    def _load_vocabulary(self) -> bool:
        """Load vocabulary from saved files."""
        try:
            if self.vocab_file.exists():
                with open(self.vocab_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.custom_words = set(data.get("custom_words", []))
                self.proper_nouns = set(data.get("proper_nouns", []))
                
                # Load domain vocabulary
                domain_data = data.get("domain_vocabulary", {})
                self.domain_vocabulary = {k: set(v) for k, v in domain_data.items()}
                
                self.word_frequencies = data.get("word_frequencies", {})
                
                self.logger.info(f"Loaded vocabulary: {len(self.custom_words)} words, "
                               f"{len(self.proper_nouns)} proper nouns")
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to load vocabulary: {e}")
        
        return False
    
    def get_all_vocabulary(self) -> Dict[str, Any]:
        """
        Get all vocabulary data.
        
        Returns:
            Dict containing all vocabulary information.
        """
        return {
            "custom_words": list(self.custom_words),
            "proper_nouns": list(self.proper_nouns),
            "domain_vocabulary": {k: list(v) for k, v in self.domain_vocabulary.items()},
            "total_words": len(self.custom_words),
            "total_proper_nouns": len(self.proper_nouns),
            "domains": list(self.domain_vocabulary.keys())
        }
    
    def clear_vocabulary(self) -> bool:
        """
        Clear all vocabulary data.
        
        Returns:
            bool: True if cleared successfully.
        """
        try:
            self.custom_words.clear()
            self.proper_nouns.clear()
            self.domain_vocabulary.clear()
            self.word_frequencies.clear()
            
            # Remove saved files
            if self.vocab_file.exists():
                self.vocab_file.unlink()
            
            self.logger.info("Vocabulary cleared")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear vocabulary: {e}")
            return False
    
    def export_vocabulary(self, file_path: str, format_type: str = "json") -> bool:
        """
        Export vocabulary to a file.
        
        Args:
            file_path: Output file path.
            format_type: Export format ("json", "csv", "text").
            
        Returns:
            bool: True if exported successfully.
        """
        try:
            export_path = Path(file_path)
            
            if format_type.lower() == "json":
                return self._export_json(export_path)
            elif format_type.lower() == "csv":
                return self._export_csv(export_path)
            elif format_type.lower() == "text":
                return self._export_text(export_path)
            else:
                self.logger.error(f"Unsupported export format: {format_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to export vocabulary: {e}")
            return False
    
    def _export_json(self, file_path: Path) -> bool:
        """Export to JSON format."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.get_all_vocabulary(), f, indent=2, ensure_ascii=False)
        return True
    
    def _export_csv(self, file_path: Path) -> bool:
        """Export to CSV format."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("word,type,frequency\n")
            
            for word in sorted(self.custom_words):
                freq = self.word_frequencies.get(word, 0)
                f.write(f"{word},word,{freq}\n")
            
            for noun in sorted(self.proper_nouns):
                f.write(f"{noun},proper_noun,0\n")
        
        return True
    
    def _export_text(self, file_path: Path) -> bool:
        """Export to plain text format."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# Custom Words\n")
            for word in sorted(self.custom_words):
                f.write(f"{word}\n")
            
            f.write("\n# Proper Nouns\n")
            for noun in sorted(self.proper_nouns):
                f.write(f"{noun}\n")
        
        return True 