"""
University Retrieval System - Final Optimized Version
All critical bugs fixed + performance optimizations
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.utils import parse_score_query, extract_major_from_query, MAJOR_MAPPING
from config import (VECTOR_DB_DIR, EMBEDDING_MODEL, EMBEDDING_DEVICE, RETRIEVAL_K, SIMILARITY_THRESHOLD)


class University_Retrieve:
    def __init__(self, vector_db_path: str = None):
        self.vector_db_path = Path(vector_db_path or VECTOR_DB_DIR)
        
        # Load embedding model
        print("Loading embedding model...")
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": EMBEDDING_DEVICE},
            encode_kwargs={"normalize_embeddings": True}
        )
        
        # Load vector database
        print("Loading vector database...")
        self.vector_db = None
        if self.vector_db_path.exists():
            try:
                self.vector_db = FAISS.load_local(
                    self.vector_db_path,
                    self.embedding_model,
                    allow_dangerous_deserialization=True
                )
                print("✓ Vector database loaded")
            except Exception as e:
                print(f"⚠️ Error loading vector DB: {e}")
        else:
            print(f"⚠️ Vector DB not found at {self.vector_db_path}")
        
        # Load structured data
        structure_path = self.vector_db_path / "structured_data.json"
        if structure_path.exists():
            with open(structure_path, "r", encoding="utf-8") as f:
                self.structured_data = json.load(f)
            print("✓ Structured data loaded")
        else:
            self.structured_data = {}
            print("⚠️ No structured data found")

    # ============================================
    # BASIC RETRIEVAL - OPTIMIZED
    # ============================================
    def search(self, query: str, k: int = RETRIEVAL_K, filter_dict: Optional[Dict] = None) -> List[Document]:
        """Tìm kiếm semantic với post-filtering"""
        if self.vector_db is None:
            return []
        
        try:
            if filter_dict:
                multiplier = 4
                raw_data = self.vector_db.similarity_search(query=query, k=k*multiplier)
                
                # Post-filter
                filter_results = [
                    doc for doc in raw_data
                    if all(doc.metadata.get(key) == value for key, value in filter_dict.items())
                ]
                
                return filter_results[:k]
            else:
                return self.vector_db.similarity_search(query=query, k=k)
                
        except Exception as e:
            print(f"⚠️ Search error: {e}")
            return []
    
    def search_with_score(
        self,
        query: str,
        k: int = RETRIEVAL_K,
        score_threshold: float = SIMILARITY_THRESHOLD,
        filter_dict: Optional[Dict] = None
    ) -> List[Tuple[Document, float]]:
        """Tìm kiếm kèm điểm số - FIXED"""
        if self.vector_db is None:
            return []
        
        try:
            if filter_dict:
                multiplier = 4
                raw_data = self.vector_db.similarity_search_with_score(query=query, k=k*multiplier)
                
                # FIX: Filter đúng cách
                filter_results = [
                    (doc, score) for doc, score in raw_data
                    if score >= score_threshold and
                       all(doc.metadata.get(key) == value for key, value in filter_dict.items())
                ]
                
                return filter_results[:k]
            else:
                results = self.vector_db.similarity_search_with_score(query=query, k=k)
                return [(doc, score) for doc, score in results if score >= score_threshold]
                
        except Exception as e:
            print(f"⚠️ Search with score error: {e}")
            return []
    
    # ============================================
    # QUERY ROUTING - IMPROVED
    # ============================================
    def detect_query_type(self, query: str) -> str:
        """Phát hiện loại truy vấn - ưu tiên rõ ràng"""
        query_lower = query.lower()
        
        # Ưu tiên 1: Điểm chuẩn (cụ thể)
        if 'điểm chuẩn' in query_lower or 'diem chuan' in query_lower:
            return "cutoff_scores"
        
        # Ưu tiên 2: Tổ hợp môn
        if any(kw in query_lower for kw in ['tổ hợp', 'to hop']) or \
           any(code in query_lower.upper() for code in ['A00', 'A01', 'B00', 'C00', 'D01']):
            return "subject_combinations"
        
        # Ưu tiên 3: Học phí
        if 'học phí' in query_lower or 'hoc phi' in query_lower:
            return "tuition"
        
        # Ưu tiên 4: Nghề nghiệp (phải check trước "học gì")
        if any(kw in query_lower for kw in ['làm gì', 'lam gi', 'ra trường', 'nghề nghiệp', 'việc làm', 'công việc']):
            return "career"
        
        # Ưu tiên 5: Chương trình học
        if any(kw in query_lower for kw in ['học gì', 'hoc gi', 'học những', 'môn gì', 'môn học', 'chương trình']):
            return "curriculum_major"
        
        # Ưu tiên 6: Phương thức xét tuyển
        if any(kw in query_lower for kw in ['phương thức', 'xét tuyển', 'xet tuyen', 'tuyển sinh']):
            return "admission_methods"
        
        # Ưu tiên 7: Thông tin ngành
        if any(kw in query_lower for kw in ['ngành', 'nganh', 'chuyên ngành']) or extract_major_from_query(query):
            return "major_info"
        
        return 'faq'

    # ============================================
    # STRUCTURED DATA RETRIEVAL - FIXED
    # ============================================
    def _get_structured_scores(self, query: str) -> Optional[Dict]:
        """
        FIX: Bug ở dòng 147 - filtered chưa được định nghĩa
        """
        parsed = parse_score_query(query=query)
        all_scores = []
        
        for key, value in self.structured_data.items():
            # Accept both "diem_xxx" and "diem_xxx.json"
            if "diem_" not in key or not isinstance(value, dict):
                continue
            
            score_data = value.get('data', [])
            if not score_data:
                continue
            
            # Filter theo year
            if parsed.get('year'):
                score_data = [s for s in score_data if s.get('year') == parsed['year']]
            
            # Filter theo major_id
            if parsed.get('major_id'):
                score_data = [s for s in score_data if s.get('major_id') == parsed['major_id']]
            # FIX: Fallback to major_name
            elif parsed.get('major_name'):
                major_name_lower = parsed['major_name'].lower()
                score_data = [  # FIX: Dùng score_data không phải filtered
                    s for s in score_data
                    if major_name_lower in s.get('major_name', '').lower()
                ]
            
            # Filter theo tổ hợp
            if parsed.get('to_hop'):
                score_data = [s for s in score_data if s.get('to_hop') == parsed['to_hop']]
            
            all_scores.extend(score_data)
        
        if all_scores:
            all_scores.sort(key=lambda x: x.get('year', 0), reverse=True)
            return {
                'scores': all_scores[:10],
                'total': len(all_scores),
                'query_info': parsed
            }
        
        return None
    
    def _get_structured_combinations(self, query: str) -> Optional[Dict]:
        """Tìm tổ hợp môn - OPTIMIZED"""
        query_upper = query.upper()
        combo_codes = ['A00', 'A01', 'A02', 'B00', 'B01', 'B02', 'C00', 'C01', 
                       'D01', 'D02', 'D03', 'D04', 'D05', 'D06', 'D07', 'D14',
                       'V00', 'V01', 'H00', 'H01', 'DD2']
        
        to_hop_data = self.structured_data.get("to_hop")
        if not to_hop_data:
            return None
        
        all_combinations = to_hop_data.get('combinations', [])
        
        # Tìm mã cụ thể
        found_code = next((code for code in combo_codes if code in query_upper), None)
        
        # Filter nếu có mã
        filtered_combinations = (
            [c for c in all_combinations if c.get("code") == found_code]
            if found_code else all_combinations
        )
        
        return {
            'description': to_hop_data.get('description', ''),
            'combinations': filtered_combinations,
            'total': len(all_combinations),
            'found_code': found_code
        }
    
    def _get_structured_tuitions(self, query: str) -> Optional[Dict]:
        """Tìm học phí - FIXED"""
        tuition_data = self.structured_data.get('hoc_phi', {})
        
        if not tuition_data:
            return None
        
        result = {
            'university': tuition_data.get('university', ''),
            'currency': tuition_data.get('currency', 'VND'),
            'calculation_method': tuition_data.get('calculation_method', ''),
            'tuition_groups': tuition_data.get('tuition_groups', []),
            'notes': tuition_data.get('notes', [])
        }
        
        # FIX: Dùng extract_major_from_query
        major_info = extract_major_from_query(query)
        
        if major_info:
            major_id = major_info['major_id']
            school_id = major_info['school_id']
            
            result['tuition_groups'] = [
                g for g in result['tuition_groups']
                if major_id in g.get('major_ids', []) or 
                   self._match_group_by_major(g.get('group_id', ''), school_id)
            ]
        
        return result
    
    def _match_group_by_major(self, group_id: str, school_id: str) -> bool:
        """Map group_id với school_id"""
        mapping = {
            'CNTT': 'CS',
            'ECON': 'ECON',
            'MED': 'MED',
            'TOUR': 'TOUR',
            'LANG': 'LANG',
            'ENG': 'ENG'
        }
        return mapping.get(group_id) == school_id

    # ============================================
    # HYBRID SEARCH - OPTIMIZED
    # ============================================
    def hybrid_search(self, query: str, k: int = RETRIEVAL_K) -> Dict:
        """
        Tìm kiếm kết hợp - MAJOR REFACTOR
        """
        query_type = self.detect_query_type(query)
        major_info = extract_major_from_query(query)

        results = {
            'query_type': query_type,
            'semantic_results': [],
            'structured_results': None,
            'context': '',
            'major_info': major_info
        }
        
        # FIX: Lấy major_id an toàn
        major_id = major_info['major_id'] if major_info else None

        # Route theo query type
        if query_type == "cutoff_scores":
            results['structured_results'] = self._get_structured_scores(query)
            docs = self.search(query, k=k, filter_dict={'type': 'cutoff_analysis'})
            results['semantic_results'] = self._enhance_with_major_context(query, docs)
        
        elif query_type == "tuition":
            results['structured_results'] = self._get_structured_tuitions(query)
            # Thêm semantic context
            if major_info:
                docs = self.search(query, k=k, filter_dict={'type': 'major'})
                results['semantic_results'] = self._enhance_with_major_context(query, docs)
        
        elif query_type == "subject_combinations":
            results['structured_results'] = self._get_structured_combinations(query)
            docs = self.search(query, k=k, filter_dict={'type': 'admission_method'})
            results['semantic_results'] = docs
        
        elif query_type == "career":
            docs = self._search_major_content(query, major_id, k, content_type='career')
            results['semantic_results'] = docs
        
        elif query_type == "curriculum_major":
            docs = self._search_major_content(query, major_id, k, content_type='curriculum')
            results['semantic_results'] = docs
        
        elif query_type == "admission_methods":
            results['semantic_results'] = self.search(query, k=k, filter_dict={'type': 'admission_method'})
        
        elif query_type == "major_info":
            docs = self._search_major_docs(query, major_id, k)
            results['semantic_results'] = docs
        
        elif query_type == "faq":
            # FIX: Typo 'doc' → 'docs'
            docs = self.search(query, k=k, filter_dict={'type': 'faq'})
            if not docs and major_id:
                docs = self.search(major_id, k=k*2, filter_dict={'type': 'major', 'major_id': major_id})
            results['semantic_results'] = docs[:k]
        
        else:
            results['semantic_results'] = self.search(query, k=k)
        
        results['context'] = self.build_context(results)
        return results
    
    # ============================================
    # HELPER METHODS - NEW
    # ============================================
    def _search_major_docs(self, query: str, major_id: Optional[str], k: int) -> List[Document]:
        """
        Helper: Search major documents với fallback
        """
        # Try search with query
        docs = self.search(query, k=k*2, filter_dict={'type': 'major'})
        
        # Fallback: search by major_id
        if not docs and major_id:
            docs = self.search(major_id, k=k*3, filter_dict={'type': 'major', 'major_id': major_id})
        
        # Enhance với major context
        docs = self._enhance_with_major_context(query, docs)
        
        # Filter by major_id if available
        if major_id:
            major_filtered = [d for d in docs if d.metadata.get("major_id") == major_id]
            docs = major_filtered if major_filtered else docs
        
        return docs[:k]
    
    def _search_major_content(
        self, 
        query: str, 
        major_id: Optional[str], 
        k: int, 
        content_type: str = 'career'
    ) -> List[Document]:
        """
        Helper: Search and extract specific content (career/curriculum)
        OPTIMIZED: Tách logic chung ra
        """
        # Get base documents
        docs = self._search_major_docs(query, major_id, k*3)
        
        # Define keywords for content types
        content_keywords = {
            'career': ['vị trí', 'công việc', 'nơi làm việc', 'mức lương', 
                      'nghề nghiệp', 'career', 'positions', 'workplace', 'salary'],
            'curriculum': ['học gì:', 'môn đại cương:', 'môn chuyên ngành:', 
                          'môn cơ sở ngành:', 'các môn học tiêu biểu:']
        }
        
        extract_keywords = {
            'career': ['Vị trí công việc', 'Nơi làm việc', 'Mức lương', 
                      '• Junior', '• Mid-level', '• Senior'],
            'curriculum': ['Học gì:', 'Môn đại cương:', 'Môn chuyên ngành:', 
                          'Môn cơ sở ngành:', 'Các môn học tiêu biểu:']
        }
        
        keywords = content_keywords.get(content_type, [])
        extract_kw = extract_keywords.get(content_type, [])
        
        # Extract relevant content
        extracted_docs = []
        for doc in docs:
            if any(kw in doc.page_content.lower() for kw in keywords):
                try:
                    extracted_content = self._extract_section(
                        doc.page_content, 
                        extract_kw,
                        content_type
                    )
                    
                    new_doc = Document(
                        page_content=extracted_content,
                        metadata={
                            **doc.metadata,
                            'content_type': f'{content_type}_only'
                        }
                    )
                    extracted_docs.append(new_doc)
                except Exception as e:
                    print(f"⚠️ Extraction error: {e}")
                    extracted_docs.append(doc)
            else:
                extracted_docs.append(doc)
        
        return extracted_docs[:k]
    
    def _extract_section(self, content: str, keywords: List[str], section_type: str) -> str:
        """
        OPTIMIZED: Unified extraction logic
        """
        lines = content.split('\n')
        result = []
        
        # Extract header (first 5 lines)
        header_keywords = ['Tên ngành:', 'Mã ngành', 'Khoa:', 'Tên trường']
        for line in lines[:5]:
            if any(kw in line for kw in header_keywords):
                result.append(line)
        
        if result:
            result.append('')
        
        # Extract content
        include_line = False
        stop_keywords = {
            'curriculum': ['Nhóm học phí:', 'Học phí dự kiến:', 'Phương thức xét tuyển:', 'Vị trí công việc:'],
            'career': []  # Career extracts till end
        }
        
        for line in lines:
            # Start including
            if any(kw in line for kw in keywords):
                include_line = True
                result.append(line)
                continue
            
            # Stop including (curriculum only)
            if section_type == 'curriculum' and include_line:
                if any(kw in line for kw in stop_keywords.get(section_type, [])):
                    break
            
            # Include lines
            if include_line and line.strip():
                result.append(line)
        
        return '\n'.join(result)
    
    # ============================================
    # LEGACY METHODS - DEPRECATED
    # ============================================
    def extract_curriculum_section(self, content: str, keyword: list) -> str:
        """DEPRECATED: Use _extract_section instead"""
        return self._extract_section(content, keyword, 'curriculum')
    
    def extract_career_section(self, content: str, keyword: list) -> str:
        """DEPRECATED: Use _extract_section instead"""
        return self._extract_section(content, keyword, 'career')
    
    # ============================================
    # CONTEXT & UTILITIES
    # ============================================
    def build_context(self, result: dict) -> str:
        """Tạo bối cảnh cho LLM"""
        context_parts = []
        
        # Major info
        if result.get('major_info'):
            major = result['major_info']
            context_parts.append("=== THÔNG TIN NGÀNH ===")
            context_parts.append(f"Ngành: {major['major_name']} ({major['major_id']})")
            context_parts.append(f"Trường: {major['school_id']}\n")
        
        # Semantic results
        if result['semantic_results']:
            context_parts.append("=== THÔNG TIN TỪ CƠ SỞ DỮ LIỆU ===")
            for i, doc in enumerate(result['semantic_results'], 1):
                context_parts.append(f"\n[Nguồn {i}]")
                context_parts.append(doc.page_content)
                
                # Metadata
                if doc.metadata:
                    meta_str = ", ".join(
                        f"{k}: {v}" for k, v in doc.metadata.items()
                        if k in ['type', 'major_id', 'major_name', 'school_id']
                    )
                    if meta_str:
                        context_parts.append(f"[Metadata: {meta_str}]")
        
        # Structured results
        if result['structured_results']:
            context_parts.append("\n=== DỮ LIỆU CHÍNH XÁC ===")
            context_parts.append(
                json.dumps(result['structured_results'], ensure_ascii=False, indent=2)
            )
        
        return "\n".join(context_parts)
    
    def _enhance_with_major_context(self, query: str, docs: List[Document]) -> List[Document]:
        """Ưu tiên docs liên quan đến ngành"""
        major_info = extract_major_from_query(query)
        
        if not major_info or not docs:
            return docs
        
        major_id = major_info['major_id']
        variants = major_info['variants']
        
        # Partition docs
        relevant_docs = []
        other_docs = []
        
        for doc in docs:
            content_lower = doc.page_content.lower()
            metadata_str = json.dumps(doc.metadata, ensure_ascii=False).lower()
            
            is_relevant = (
                major_id.lower() in metadata_str or
                any(variant in content_lower for variant in variants)
            )
            
            if is_relevant:
                relevant_docs.append(doc)
            else:
                other_docs.append(doc)
        
        return relevant_docs + other_docs


# ============================================
# TESTING
# ============================================
if __name__ == "__main__":
    print("\n🧪 Testing Retriever (Optimized Version)...\n")

    try:
        retriever = University_Retrieve()

        test_queries = [
            "ngành marketing học gì",
            "điểm chuẩn ngành Trí tuệ nhân tạo năm 2024",
            "Học phí Trí tuệ nhân tạo",
            "Tổ hợp A00 gồm những môn nào?",
            "Ra trường ngành marketing làm gì?",
            "ngành y khoa ra trường làm công việc gì?",
            "ngành du lịch học gì",
        ]

        for query in test_queries:
            print(f"\n{'='*80}")
            print(f"🔎 Query: {query}")

            result = retriever.hybrid_search(query, k=2)

            print(f"📌 Type: {result['query_type']}")
            if result['major_info']:
                print(f"🎓 Major: {result['major_info']['major_name']} ({result['major_info']['major_id']})")
            
            print(f"\n📊 Results:")
            print(f"  - Semantic: {len(result['semantic_results'])} docs")
            print(f"  - Structured: {'Yes' if result['structured_results'] else 'No'}")
            
            # Show first semantic result
            if result['semantic_results']:
                doc = result['semantic_results'][0]
                preview = doc.page_content.replace("\n", " ")[:200]
                print(f"\n📄 Preview: {preview}...")
                if doc.metadata:
                    print(f"   Metadata: {doc.metadata.get('type')}, {doc.metadata.get('major_id')}")
            
            # Show structured summary
            if result['structured_results']:
                if isinstance(result['structured_results'], dict):
                    keys = list(result['structured_results'].keys())
                    print(f"📊 Structured keys: {keys}")

        print(f"\n{'='*80}")
        print("✅ All tests completed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()