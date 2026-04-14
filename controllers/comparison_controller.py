import os
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from database.db_manager import DatabaseManager
from database.models import ManuscriptComparison, ComparisonDetail, Manuscript, InvestigationFile
import logging
import json

logger = logging.getLogger(__name__)

class ComparisonController:
    def __init__(self):
        self.db = DatabaseManager()

    def create_comparison(self, investigation_id: int, manuscript1_id: int, 
                        manuscript2_id: int, comparison_method: str = 'text_similarity') -> int:
        """Create a new manuscript comparison"""
        def create_comparison_transaction(session):
            # Validate investigation exists
            from database.models import BookInvestigation
            investigation = session.query(BookInvestigation).get(investigation_id)
            if not investigation:
                raise ValueError("Investigation not found")
            
            # Validate manuscripts exist and are different
            manuscript1 = session.query(Manuscript).get(manuscript1_id)
            manuscript2 = session.query(Manuscript).get(manuscript2_id)
            
            if not manuscript1 or not manuscript2:
                raise ValueError("One or both manuscripts not found")
            
            if manuscript1_id == manuscript2_id:
                raise ValueError("Cannot compare manuscript with itself")
            
            # Check if comparison already exists
            existing = session.query(ManuscriptComparison).filter(
                ManuscriptComparison.investigation_id == investigation_id,
                ManuscriptComparison.manuscript1_id == manuscript1_id,
                ManuscriptComparison.manuscript2_id == manuscript2_id
            ).first()
            
            if existing:
                raise ValueError("Comparison already exists between these manuscripts")
            
            # Create comparison
            comparison = ManuscriptComparison(
                investigation_id=investigation_id,
                manuscript1_id=manuscript1_id,
                manuscript2_id=manuscript2_id,
                comparison_method=comparison_method,
                comparison_date=datetime.utcnow()
            )
            
            session.add(comparison)
            session.flush()
            logger.info(f"Created comparison: manuscripts {manuscript1_id} vs {manuscript2_id}")
            return comparison.id
        
        try:
            return self.db.execute_in_transaction(create_comparison_transaction)
        except Exception as e:
            logger.error(f"Failed to create comparison: {e}")
            raise

    def perform_text_comparison(self, comparison_id: int) -> Dict:
        """Perform detailed text comparison between manuscripts"""
        def perform_comparison_transaction(session):
            comparison = session.query(ManuscriptComparison).get(comparison_id)
            if not comparison:
                raise ValueError("Comparison not found")
            
            # Get manuscripts
            manuscript1 = session.query(Manuscript).get(comparison.manuscript1_id)
            manuscript2 = session.query(Manuscript).get(comparison.manuscript2_id)
            
            # For now, simulate text comparison (in real implementation, would extract text from files)
            # This is a placeholder for actual text extraction and comparison
            
            # Simulate text analysis
            text1 = self._extract_manuscript_text(session, comparison.manuscript1_id)
            text2 = self._extract_manuscript_text(session, comparison.manuscript2_id)
            
            # Perform comparison analysis
            similarity_result = self._calculate_text_similarity(text1, text2)
            differences = self._find_differences(text1, text2)
            similarities = self._find_similarities(text1, text2)
            
            # Update comparison with results
            comparison.similarity_score = similarity_result['score']
            comparison.differences_count = len(differences)
            comparison.similarities_count = len(similarities)
            comparison.total_words = similarity_result['total_words']
            comparison.key_differences = self._summarize_differences(differences)
            comparison.key_similarities = self._summarize_similarities(similarities)
            comparison.detailed_analysis = json.dumps({
                'differences': differences[:10],  # Store first 10 differences
                'similarities': similarities[:10],  # Store first 10 similarities
                'analysis': similarity_result
            })
            
            # Create detailed comparison records
            for i, diff in enumerate(differences[:20]):  # Store top 20 differences
                detail = ComparisonDetail(
                    comparison_id=comparison_id,
                    detail_type=diff['type'],
                    manuscript1_text=diff.get('text1'),
                    manuscript2_text=diff.get('text2'),
                    position_chapter=diff.get('chapter'),
                    confidence_score=diff.get('confidence', 0.8),
                    notes=diff.get('notes')
                )
                session.add(detail)
            
            session.commit()
            logger.info(f"Completed comparison {comparison_id} with similarity score: {similarity_result['score']}")
            
            return {
                'similarity_score': similarity_result['score'],
                'differences_count': len(differences),
                'similarities_count': len(similarities),
                'total_words': similarity_result['total_words'],
                'key_differences': comparison.key_differences,
                'key_similarities': comparison.key_similarities
            }
        
        try:
            return self.db.execute_in_transaction(perform_comparison_transaction)
        except Exception as e:
            logger.error(f"Failed to perform text comparison: {e}")
            raise

    def _extract_manuscript_text(self, session, manuscript_id: str) -> str:
        """Extract text from manuscript files (placeholder implementation)"""
        # In real implementation, this would:
        # 1. Find uploaded files for this manuscript
        # 2. Extract text from PDF/Word files
        # 3. Return the extracted text
        
        # For now, return placeholder text
        manuscript = session.query(Manuscript).get(manuscript_id)
        if not manuscript:
            return ""
        
        # Simulate text extraction based on manuscript info
        placeholder_text = f"Sample text from manuscript {manuscript.library_name}. "
        placeholder_text += "This is placeholder text for demonstration purposes. "
        placeholder_text += "In a real implementation, this would be the actual extracted text from the manuscript file. "
        placeholder_text += "The text would include the actual content of the manuscript for comparison analysis."
        
        return placeholder_text

    def _calculate_text_similarity(self, text1: str, text2: str) -> Dict:
        """Calculate text similarity metrics"""
        # Simple similarity calculation (placeholder)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return {'score': 1.0, 'total_words': 0}
        
        if not words1 or not words2:
            return {'score': 0.0, 'total_words': len(words1) + len(words2)}
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity_score = len(intersection) / len(union) if union else 0
        total_words = len(union)
        
        return {
            'score': similarity_score,
            'total_words': total_words,
            'common_words': len(intersection),
            'unique_words_1': len(words1 - words2),
            'unique_words_2': len(words2 - words1)
        }

    def _find_differences(self, text1: str, text2: str) -> List[Dict]:
        """Find differences between texts"""
        differences = []
        
        # Simple difference detection (placeholder)
        words1 = text1.split()
        words2 = text2.split()
        
        # Find unique words in text1
        for word in set(words1):
            if word not in words2:
                differences.append({
                    'type': 'deletion',
                    'text1': word,
                    'text2': '',
                    'chapter': 'Unknown',
                    'confidence': 0.9,
                    'notes': f'Word found only in first manuscript: {word}'
                })
        
        # Find unique words in text2
        for word in set(words2):
            if word not in words1:
                differences.append({
                    'type': 'addition',
                    'text1': '',
                    'text2': word,
                    'chapter': 'Unknown',
                    'confidence': 0.9,
                    'notes': f'Word found only in second manuscript: {word}'
                })
        
        return differences[:50]  # Limit to 50 differences

    def _find_similarities(self, text1: str, text2: str) -> List[Dict]:
        """Find similarities between texts"""
        similarities = []
        
        # Find common words (placeholder)
        words1 = text1.split()
        words2 = text2.split()
        common_words = set(words1).intersection(set(words2))
        
        for word in common_words:
            similarities.append({
                'type': 'common',
                'text': word,
                'chapter': 'Unknown',
                'confidence': 1.0,
                'notes': f'Common word: {word}'
            })
        
        return similarities[:50]  # Limit to 50 similarities

    def _summarize_differences(self, differences: List[Dict]) -> str:
        """Create summary of key differences"""
        if not differences:
            return "No significant differences found."
        
        # Count different types of differences
        additions = len([d for d in differences if d['type'] == 'addition'])
        deletions = len([d for d in differences if d['type'] == 'deletion'])
        modifications = len([d for d in differences if d['type'] == 'modification'])
        
        summary = f"Found {len(differences)} differences: "
        summary += f"{additions} additions, {deletions} deletions"
        if modifications > 0:
            summary += f", {modifications} modifications"
        
        return summary

    def _summarize_similarities(self, similarities: List[Dict]) -> str:
        """Create summary of key similarities"""
        if not similarities:
            return "No significant similarities found."
        
        summary = f"Found {len(similarities)} similarities between the manuscripts. "
        summary += "The manuscripts share significant common content and structure."
        
        return summary

    def get_comparison_details(self, comparison_id: int) -> Dict:
        """Get detailed comparison results"""
        session = self.db.get_session()
        try:
            comparison = session.query(ManuscriptComparison).get(comparison_id)
            if not comparison:
                raise ValueError("Comparison not found")
            
            # Get detailed differences
            details = session.query(ComparisonDetail).filter(
                ComparisonDetail.comparison_id == comparison_id
            ).order_by(ComparisonDetail.confidence_score.desc()).all()
            
            detail_list = []
            for detail in details:
                detail_list.append({
                    'type': detail.detail_type,
                    'manuscript1_text': detail.manuscript1_text,
                    'manuscript2_text': detail.manuscript2_text,
                    'position_chapter': detail.position_chapter,
                    'position_page': detail.position_page,
                    'position_line': detail.position_line,
                    'confidence_score': detail.confidence_score,
                    'notes': detail.notes
                })
            
            # Parse detailed analysis if available
            detailed_analysis = {}
            if comparison.detailed_analysis:
                try:
                    detailed_analysis = json.loads(comparison.detailed_analysis)
                except json.JSONDecodeError:
                    detailed_analysis = {}
            
            return {
                'id': comparison.id,
                'manuscript1_id': comparison.manuscript1_id,
                'manuscript2_id': comparison.manuscript2_id,
                'manuscript1_name': comparison.manuscript1.library_name if comparison.manuscript1 else 'Unknown',
                'manuscript2_name': comparison.manuscript2.library_name if comparison.manuscript2 else 'Unknown',
                'similarity_score': comparison.similarity_score,
                'differences_count': comparison.differences_count,
                'similarities_count': comparison.similarities_count,
                'total_words': comparison.total_words,
                'comparison_date': comparison.comparison_date.isoformat(),
                'comparison_method': comparison.comparison_method,
                'key_differences': comparison.key_differences,
                'key_similarities': comparison.key_similarities,
                'detailed_analysis': detailed_analysis,
                'details': detail_list
            }
        except Exception as e:
            logger.error(f"Failed to get comparison details: {e}")
            raise
        finally:
            self.db.close_session(session)

    def get_investigation_comparisons(self, investigation_id: int) -> List[Dict]:
        """Get all comparisons for an investigation"""
        session = self.db.get_session()
        try:
            comparisons = session.query(ManuscriptComparison).filter(
                ManuscriptComparison.investigation_id == investigation_id
            ).order_by(ManuscriptComparison.comparison_date.desc()).all()
            
            result = []
            for comp in comparisons:
                result.append({
                    'id': comp.id,
                    'manuscript1_id': comp.manuscript1_id,
                    'manuscript2_id': comp.manuscript2_id,
                    'manuscript1_name': comp.manuscript1.library_name if comp.manuscript1 else 'Unknown',
                    'manuscript2_name': comp.manuscript2.library_name if comp.manuscript2 else 'Unknown',
                    'similarity_score': comp.similarity_score,
                    'differences_count': comp.differences_count,
                    'similarities_count': comp.similarities_count,
                    'total_words': comp.total_words,
                    'comparison_date': comp.comparison_date.isoformat(),
                    'comparison_method': comp.comparison_method,
                    'key_differences': comp.key_differences,
                    'key_similarities': comp.key_similarities,
                    'status': 'completed' if comp.similarity_score is not None else 'pending'
                })
            
            return result
        except Exception as e:
            logger.error(f"Failed to get investigation comparisons: {e}")
            raise
        finally:
            self.db.close_session(session)

    def delete_comparison(self, comparison_id: int) -> bool:
        """Delete a comparison"""
        def delete_comparison_transaction(session):
            comparison = session.query(ManuscriptComparison).get(comparison_id)
            if not comparison:
                raise ValueError("Comparison not found")
            
            # Delete related details first (cascade should handle this)
            session.query(ComparisonDetail).filter(
                ComparisonDetail.comparison_id == comparison_id
            ).delete()
            
            # Delete comparison
            session.delete(comparison)
            logger.info(f"Deleted comparison: {comparison_id}")
            return True
        
        try:
            return self.db.execute_in_transaction(delete_comparison_transaction)
        except Exception as e:
            logger.error(f"Failed to delete comparison: {e}")
            raise
