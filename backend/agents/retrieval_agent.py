import json
import logging
import os
from typing import Dict, List, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime

from ..config import KNOWLEDGE_BASE_PATH, CHROMA_DB_PATH, COLLECTION_NAME, BASE_DIR

class RetrievalAgent:
    """Knowledge Base Retrieval Agent using ChromaDB and Sentence Transformers"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        
        # Initialize components
        self.load_embedding_model()
        self.initialize_chroma()
        self.initialize_knowledge_base()
    
    def load_embedding_model(self):
        """Load sentence transformer model for embeddings"""
        try:
            model_name = 'all-MiniLM-L6-v2'  # Lightweight and fast
            self.logger.info(f"Loading embedding model: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
            self.logger.info("Embedding model loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading embedding model: {e}")
            raise
    
    def initialize_chroma(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Create ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=str(CHROMA_DB_PATH),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create or get collection
            try:
                self.collection = self.chroma_client.get_collection(COLLECTION_NAME)
                self.logger.info(f"Retrieved existing collection: {COLLECTION_NAME}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=COLLECTION_NAME,
                    metadata={"description": "Admission inquiry knowledge base"}
                )
                self.logger.info(f"Created new collection: {COLLECTION_NAME}")
                
        except Exception as e:
            self.logger.error(f"Error initializing ChromaDB: {e}")
            raise
    
    def initialize_knowledge_base(self):
        """Load and index knowledge base"""
        try:
            # Load knowledge base
            if not os.path.exists(KNOWLEDGE_BASE_PATH):
                self.create_default_knowledge_base()
            
            with open(KNOWLEDGE_BASE_PATH, 'r') as f:
                knowledge_data = json.load(f)
            
            # Check if collection is empty or needs updating
            collection_count = self.collection.count()
            
            if collection_count == 0:
                self.logger.info("Populating empty knowledge base...")
                self.populate_knowledge_base(knowledge_data)
            else:
                self.logger.info(f"Knowledge base already contains {collection_count} items")
                
        except Exception as e:
            self.logger.error(f"Error initializing knowledge base: {e}")
            raise
    
    def create_default_knowledge_base(self):
        """Create default knowledge base"""
        default_kb = {
            "university_info": {
                "name": "University Name",
                "established": "1950",
                "location": "City, State",
                "type": "Public Research University"
            },
            "faqs": [
                {
                    "id": "req_001",
                    "question": "What are the admission requirements?",
                    "answer": "To apply for admission, you need: 1) High school diploma or equivalent, 2) Minimum GPA of 3.0, 3) SAT score of 1200+ or ACT score of 26+, 4) Two letters of recommendation, 5) Personal statement, 6) Official transcripts.",
                    "category": "admission_requirements",
                    "keywords": ["requirements", "admission", "GPA", "SAT", "ACT", "transcripts"]
                },
                {
                    "id": "deadline_001",
                    "question": "When is the application deadline?",
                    "answer": "Application deadlines are: Fall semester - March 1st (Regular Decision), November 15th (Early Decision); Spring semester - October 1st; Summer semester - March 1st. Late applications may be considered on a space-available basis.",
                    "category": "application_deadline",
                    "keywords": ["deadline", "application", "fall", "spring", "summer", "early decision"]
                },
                {
                    "id": "fees_001",
                    "question": "What are the tuition and fees?",
                    "answer": "For the 2024-2025 academic year: In-state tuition: $12,000/year, Out-of-state tuition: $28,000/year, Room and board: $14,000/year, Books and supplies: $1,500/year, Personal expenses: $2,000/year. Total estimated cost varies by residency status.",
                    "category": "tuition_fees",
                    "keywords": ["tuition", "fees", "cost", "in-state", "out-of-state", "room", "board"]
                },
                {
                    "id": "programs_001",
                    "question": "What programs do you offer?",
                    "answer": "We offer over 100 undergraduate programs including: Business Administration, Computer Science, Engineering, Pre-Med, Psychology, Education, Arts & Sciences, and more. Graduate programs include MBA, MS in Computer Science, Engineering, and various PhD programs.",
                    "category": "programs_offered",
                    "keywords": ["programs", "majors", "degrees", "undergraduate", "graduate", "MBA", "PhD"]
                },
                {
                    "id": "aid_001",
                    "question": "What financial aid is available?",
                    "answer": "Financial aid options include: Federal grants and loans, State grants, University scholarships (merit and need-based), Work-study programs, Graduate assistantships. Complete FAFSA by March 1st for priority consideration. Over 80% of students receive some form of financial aid.",
                    "category": "financial_aid",
                    "keywords": ["financial aid", "scholarships", "grants", "loans", "FAFSA", "work-study"]
                },
                {
                    "id": "contact_001",
                    "question": "How can I contact the admissions office?",
                    "answer": "Admissions Office Contact: Phone: (555) 123-4567, Email: admissions@university.edu, Address: 123 University Ave, City, State 12345. Office hours: Monday-Friday 8:00 AM - 5:00 PM. Virtual appointments available.",
                    "category": "contact_info",
                    "keywords": ["contact", "phone", "email", "address", "office hours", "appointments"]
                },
                {
                    "id": "visit_001",
                    "question": "Can I visit the campus?",
                    "answer": "Yes! Campus visits are encouraged. We offer: Daily campus tours at 10 AM and 2 PM, Information sessions, Overnight stays for prospective students, Virtual tours available online. Schedule visits at least 48 hours in advance through our website or by calling the admissions office.",
                    "category": "campus_visit",
                    "keywords": ["campus visit", "tour", "information session", "overnight", "virtual tour"]
                },
                {
                    "id": "housing_001",
                    "question": "What housing options are available?",
                    "answer": "On-campus housing includes: Traditional residence halls, Suite-style dormitories, Apartment-style housing for upperclassmen, Special interest housing (honors, international). All freshmen are required to live on campus. Housing applications open in February for fall semester.",
                    "category": "housing",
                    "keywords": ["housing", "dormitory", "residence hall", "apartment", "on-campus", "freshman"]
                }
            ]
        }
        
        with open(KNOWLEDGE_BASE_PATH, 'w') as f:
            json.dump(default_kb, f, indent=2)
        
        self.logger.info("Default knowledge base created")
    
    def populate_knowledge_base(self, knowledge_data):
        """Populate ChromaDB with knowledge base data"""
        try:
            documents = []
            metadatas = []
            ids = []
            
            # Process FAQs
            for faq in knowledge_data.get('faqs', []):
                # Combine question and answer for better retrieval
                doc_text = f"Q: {faq['question']} A: {faq['answer']}"
                documents.append(doc_text)
                
                metadata = {
                    'id': faq['id'],
                    'question': faq['question'],
                    'answer': faq['answer'],
                    'category': faq.get('category', 'general'),
                    'type': 'faq',
                    'keywords': ','.join(faq.get('keywords', []))
                }
                metadatas.append(metadata)
                ids.append(faq['id'])
            
            # Process university info
            if 'university_info' in knowledge_data:
                uni_info = knowledge_data['university_info']
                doc_text = f"University Information: {json.dumps(uni_info)}"
                documents.append(doc_text)
                
                metadata = {
                    'id': 'uni_info_001',
                    'type': 'university_info',
                    'category': 'general_info'
                }
                metadatas.append(metadata)
                ids.append('uni_info_001')
            
            if documents:
                # Generate embeddings
                embeddings = self.embedding_model.encode(documents).tolist()
                
                # Add to collection
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
                
                self.logger.info(f"Added {len(documents)} documents to knowledge base")
            
        except Exception as e:
            self.logger.error(f"Error populating knowledge base: {e}")
            raise
    
    def retrieve(self, query: str, intent_result: Dict = None, top_k: int = 3) -> Dict[str, Any]:
        """Retrieve relevant information from knowledge base"""
        try:
            if not query.strip():
                return {'documents': [], 'metadata': [], 'distances': []}
            
            # Build search filters based on intent
            where_filter = None
            if intent_result and intent_result.get('intent') != 'unknown':
                intent = intent_result['intent']
                # Map intent to category
                category_mapping = {
                    'admission_requirements': 'admission_requirements',
                    'application_deadline': 'application_deadline',
                    'tuition_fees': 'tuition_fees',
                    'programs_offered': 'programs_offered',
                    'financial_aid': 'financial_aid',
                    'contact_info': 'contact_info',
                    'campus_visit': 'campus_visit',
                    'housing': 'housing'
                }
                
                if intent in category_mapping:
                    where_filter = {"category": category_mapping[intent]}
            
            # Perform similarity search
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter
            )
            
            # Process results
            processed_results = {
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'query': query,
                'intent': intent_result.get('intent') if intent_result else None
            }
            
            # Add relevance scores (convert distances to similarity scores)
            if processed_results['distances']:
                max_distance = max(processed_results['distances'])
                relevance_scores = []
                for distance in processed_results['distances']:
                    # Convert distance to similarity (0-1, higher is better)
                    similarity = 1 - (distance / (max_distance + 1e-6))
                    relevance_scores.append(max(0, min(1, similarity)))
                
                processed_results['relevance_scores'] = relevance_scores
            
            # Filter results by relevance threshold
            filtered_results = self._filter_by_relevance(processed_results, threshold=0.3)
            
            self.logger.info(f"Retrieved {len(filtered_results['documents'])} relevant documents for query: '{query}'")
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Error retrieving information: {e}")
            return {
                'documents': [],
                'metadatas': [],
                'distances': [],
                'query': query,
                'error': str(e)
            }
    
    def _filter_by_relevance(self, results: Dict, threshold: float = 0.3) -> Dict:
        """Filter results by relevance threshold"""
        if not results.get('relevance_scores'):
            return results
        
        filtered_indices = [
            i for i, score in enumerate(results['relevance_scores']) 
            if score >= threshold
        ]
        
        if not filtered_indices:
            # If no results meet threshold, return the top result
            filtered_indices = [0] if results['documents'] else []
        
        filtered_results = {}
        for key in results:
            if key in ['documents', 'metadatas', 'distances', 'relevance_scores']:
                filtered_results[key] = [results[key][i] for i in filtered_indices]
            else:
                filtered_results[key] = results[key]
        
        return filtered_results
    
    def add_document(self, document: str, metadata: Dict, doc_id: str = None):
        """Add a new document to the knowledge base"""
        try:
            if not doc_id:
                doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Generate embedding
            embedding = self.embedding_model.encode([document]).tolist()[0]
            
            # Add to collection
            self.collection.add(
                documents=[document],
                metadatas=[metadata],
                ids=[doc_id],
                embeddings=[embedding]
            )
            
            self.logger.info(f"Added document with ID: {doc_id}")
            
        except Exception as e:
            self.logger.error(f"Error adding document: {e}")
    
    def update_document(self, doc_id: str, document: str, metadata: Dict):
        """Update an existing document"""
        try:
            # Generate new embedding
            embedding = self.embedding_model.encode([document]).tolist()[0]
            
            # Update in collection
            self.collection.update(
                ids=[doc_id],
                documents=[document],
                metadatas=[metadata],
                embeddings=[embedding]
            )
            
            self.logger.info(f"Updated document with ID: {doc_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating document: {e}")
    
    def delete_document(self, doc_id: str):
        """Delete a document from the knowledge base"""
        try:
            self.collection.delete(ids=[doc_id])
            self.logger.info(f"Deleted document with ID: {doc_id}")
            
        except Exception as e:
            self.logger.error(f"Error deleting document: {e}")
    
    def get_collection_stats(self):
        """Get statistics about the knowledge base"""
        try:
            count = self.collection.count()
            
            # Get sample documents for analysis
            sample_results = self.collection.get(limit=min(10, count))
            
            categories = {}
            types = {}
            
            for metadata in sample_results.get('metadatas', []):
                category = metadata.get('category', 'unknown')
                doc_type = metadata.get('type', 'unknown')
                
                categories[category] = categories.get(category, 0) + 1
                types[doc_type] = types.get(doc_type, 0) + 1
            
            return {
                'total_documents': count,
                'categories': categories,
                'types': types,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def search_by_keywords(self, keywords: List[str], top_k: int = 5) -> Dict:
        """Search documents by keywords"""
        try:
            # Combine keywords into query
            query = ' '.join(keywords)
            
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            return {
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'keywords': keywords
            }
            
        except Exception as e:
            self.logger.error(f"Error searching by keywords: {e}")
            return {'documents': [], 'metadatas': [], 'distances': [], 'keywords': keywords}
    
    def cleanup(self):
        """Cleanup resources"""
        if self.chroma_client:
            # ChromaDB handles cleanup automatically
            pass
        self.logger.info("Retrieval Agent cleaned up")