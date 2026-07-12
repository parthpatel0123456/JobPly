"""
Tests for the SkillMatcher class.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

# Try to import the matcher
try:
    from embedding_matcher.matcher import SkillMatcher
    MATCHER_AVAILABLE = True
except ImportError:
    MATCHER_AVAILABLE = False

class TestSkillMatcher(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.sample_resume = """
        EXPERIENCED SOFTWARE ENGINEER
        Skilled in Python, JavaScript, and web development
        Experience with RESTful APIs, databases, and agile methodologies
        Strong problem-solving and communication skills
        """
        
        self.sample_job_description = """
        We are looking for a Software Engineer with experience in Python and JavaScript.
        The ideal candidate will have:
        - 2+ years of experience in web development
        - Proficiency in Python and JavaScript
        - Experience with RESTful APIs
        - Strong problem-solving skills
        """
        
        self.unrelated_text = """
        CHEF SPECIALIZING IN FRENCH CUISINE
        10 years experience in Michelin-starred restaurants
        Expert in sauce preparation and pastry making
        """

    @unittest.skipIf(not MATCHER_AVAILABLE, "Matcher module not available")
    def test_init_default_model(self):
        """Test that the matcher initializes with the default model."""
        matcher = SkillMatcher()
        self.assertEqual(matcher.get_model_name(), 'all-MiniLM-L6-v2')
    
    @unittest.skipIf(not MATCHER_AVAILABLE, "Matcher module not available")
    def test_init_custom_model(self):
        """Test that the matcher can initialize with a custom model."""
        matcher = SkillMatcher(model_name='test-model')
        self.assertEqual(matcher.get_model_name(), 'test-model')
    
    @unittest.skipIf(not MATCHER_AVAILABLE, "Matcher module not available")
    def test_match_identical_texts(self):
        """Test matching identical texts returns high similarity."""
        matcher = SkillMatcher()
        text = "This is a test sentence."
        similarity = matcher.match(text, text)
        # Identical texts should have similarity close to 1.0
        self.assertGreaterEqual(similarity, 0.9)
        self.assertLessEqual(similarity, 1.0)
    
    @unittest.skipIf(not MATCHER_AVAILABLE, "Matcher module not available")
    def test_match_related_texts(self):
        """Test matching related texts returns reasonable similarity."""
        matcher = SkillMatcher()
        similarity = matcher.match(self.sample_resume, self.sample_job_description)
        # Related texts should have moderate to high similarity
        self.assertGreaterEqual(similarity, 0.5)
        self.assertLessEqual(similarity, 1.0)
    
    @unittest.skipIf(not MATCHER_AVAILABLE, "Matcher module not available")
    def test_match_unrelated_texts(self):
        """Test matching unrelated texts returns low similarity."""
        matcher = SkillMatcher()
        similarity = matcher.match(self.sample_resume, self.unrelated_text)
        # Unrelated texts should have low similarity
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 0.5)
    
    @unittest.skipIf(not MATCHER_AVAILABLE, "Matcher module not available")
    def test_match_batch(self):
        """Test batch matching functionality."""
        matcher = SkillMatcher()
        job_descriptions = [
            self.sample_job_description,
            self.unrelated_text,
            "Another software engineering position requiring Python and web development"
        ]
        
        similarities = matcher.match_batch(self.sample_resume, job_descriptions)
        
        # Should return same number of scores as job descriptions
        self.assertEqual(len(similarities), len(job_descriptions))
        
        # All scores should be between 0 and 1
        for score in similarities:
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
        
        # First and third should be higher than second (unrelated)
        self.assertGreater(similarities[0], similarities[1])
        self.assertGreater(similarities[2], similarities[1])
    
    @unittest.skipIf(not MATCHER_AVAILABLE, "Matcher module not available")
    def test_match_empty_input(self):
        """Test that empty inputs raise ValueError."""
        matcher = SkillMatcher()
        
        with self.assertRaises(ValueError):
            matcher.match("", "Some job description")
        
        with self.assertRaises(ValueError):
            matcher.match("Some resume", "")
        
        with self.assertRaises(ValueError):
            matcher.match(None, "Some job description")
        
        with self.assertRaises(ValueError):
            matcher.match("Some resume", None)
    
    @unittest.skipIf(not MATCHER_AVAILABLE, "Matcher module not available")
    def test_match_batch_empty_list(self):
        """Test that batch matching with empty list returns empty list."""
        matcher = SkillMatcher()
        result = matcher.match_batch("Some resume", [])
        self.assertEqual(result, [])
    
    @unittest.skipIf(not MATCHER_AVAILABLE, "Matcher module not available")
    @patch('embedding_matcher.matcher.SENTENCE_TRANSFORMERS_AVAILABLE', False)
    def test_model_not_available(self):
        """Test that appropriate error is raised when model is not available."""
        matcher = SkillMatcher()
        
        with self.assertRaises(RuntimeError):
            matcher.match("resume", "job description")
    
    @unittest.skipIf(not MATCHER_AVAILABLE, "Matcher module not available")
    def test_is_available(self):
        """Test the is_available method."""
        self.assertTrue(SkillMatcher.is_available())

if __name__ == '__main__':
    unittest.main()