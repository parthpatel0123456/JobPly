"""
Local skill matcher for the JobPly system.

Uses sentence-transformers to compute semantic similarity between
resumes and job descriptions.
"""

import logging
from typing import Optional, List, Union
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    # Create a mock for type hints when not available
    class SentenceTransformer:
        pass

logger = logging.getLogger(__name__)

class SkillMatcher:
    """
    A matcher that computes semantic similarity between resumes and job descriptions
    using sentence-transformers models.
    """
    
    # Class variable to hold the model instance (shared across instances)
    _model: Optional[SentenceTransformer] = None
    _model_name: str = 'all-MiniLM-L6-v2'
    
    def __init__(self, model_name: str = None):
        """
        Initialize the SkillMatcher.
        
        Args:
            model_name: Name of the sentence-transformers model to use.
                       If None, uses the class default ('all-MiniLM-L6-v2')
        """
        if model_name is not None:
            self._model_name = model_name
            
        # Initialize model if not already done
        if SkillMatcher._model is None:
            self._load_model()
    
    @classmethod
    def _load_model(cls):
        """Load the sentence-transformers model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Please install it with: pip install sentence-transformers"
            )
        
        try:
            logger.info(f"Loading sentence-transformers model: {cls._model_name}")
            cls._model = SentenceTransformer(cls._model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model {cls._model_name}: {str(e)}")
            raise
    
    def match(self, resume_text: str, job_description_text: str) -> float:
        """
        Compute the semantic similarity between a resume and a job description.
        
        Args:
            resume_text: The resume text
            job_description_text: The job description text
            
        Returns:
            A similarity score between 0.0 and 1.0 (cosine similarity)
            
        Raises:
            ValueError: If either input is empty or None
            RuntimeError: If model is not available
        """
        # Validate inputs
        if not resume_text or not isinstance(resume_text, str):
            raise ValueError("Resume text must be a non-empty string")
        if not job_description_text or not isinstance(job_description_text, str):
            raise ValueError("Job description text must be a non-empty string")
            
        # Check if model is available
        if not SENTENCE_TRANSFORMERS_AVAILABLE or SkillMatcher._model is None:
            raise RuntimeError("Sentence transformer model is not available")
        
        try:
            # Encode both texts
            embeddings = self._model.encode([resume_text, job_description_text])
            
            # Compute cosine similarity
            # Normalize the vectors
            norm1 = np.linalg.norm(embeddings[0])
            norm2 = np.linalg.norm(embeddings[1])
            
            # Avoid division by zero
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            # Compute dot product and normalize
            similarity = np.dot(embeddings[0], embeddings[1]) / (norm1 * norm2)
            
            # Ensure the result is in [0, 1] range (cosine similarity is in [-1, 1])
            # For text embeddings from similar domains, we expect positive values
            similarity = max(0.0, min(1.0, float(similarity)))
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            raise RuntimeError(f"Failed to compute similarity: {str(e)}")
    
    def match_batch(self, resume_text: str, job_descriptions: List[str]) -> List[float]:
        """
        Compute similarities between a resume and multiple job descriptions.
        
        Args:
            resume_text: The resume text
            job_descriptions: List of job description texts
            
        Returns:
            List of similarity scores between 0.0 and 1.0
        """
        if not job_descriptions:
            return []
            
        # Validate resume
        if not resume_text or not isinstance(resume_text, str):
            raise ValueError("Resume text must be a non-empty string")
            
        # Validate all job descriptions
        for i, jd in enumerate(job_descriptions):
            if not jd or not isinstance(jd, str):
                raise ValueError(f"Job description at index {i} must be a non-empty string")
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE or SkillMatcher._model is None:
            raise RuntimeError("Sentence transformer model is not available")
        
        try:
            # Encode resume once
            resume_embedding = self._model.encode([resume_text])
            
            # Encode all job descriptions
            jd_embeddings = self._model.encode(job_descriptions)
            
            # Compute cosine similarities
            similarities = []
            for jd_emb in jd_embeddings:
                # Normalize vectors
                norm_res = np.linalg.norm(resume_embedding[0])
                norm_jd = np.linalg.norm(jd_emb)
                
                if norm_res == 0 or norm_jd == 0:
                    similarities.append(0.0)
                    continue
                    
                # Compute cosine similarity
                similarity = np.dot(resume_embedding[0], jd_emb) / (norm_res * norm_jd)
                # Clamp to [0, 1] range
                similarity = max(0.0, min(1.0, float(similarity)))
                similarities.append(similarity)
                
            return similarities
            
        except Exception as e:
            logger.error(f"Error computing batch similarity: {str(e)}")
            raise RuntimeError(f"Failed to compute batch similarity: {str(e)}")
    
    @classmethod
    def is_available(cls) -> bool:
        """
        Check if the sentence-transformers dependency is available.
        
        Returns:
            True if sentence-transformers is installed and model can be loaded, False otherwise
        """
        return SENTENCE_TRANSFORMERS_AVAILABLE
    
    @classmethod
    def get_model_name(cls) -> str:
        """
        Get the name of the model being used.
        
        Returns:
            The model name string
        """
        return cls._model_name