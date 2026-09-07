"""
Text Generation Agent Module

The Text Generation Agent (TGA) is responsible for:
1. Converting structured triples into fluent natural language sentences
2. Preserving all information from input triples
3. Generating coherent and grammatically correct text
4. Supporting batch processing for multiple triple sets
"""

from .agent import TextGenerationAgent

__all__ = ['TextGenerationAgent']