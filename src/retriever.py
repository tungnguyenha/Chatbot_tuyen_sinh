import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.utils import parse_score_query,extract_major_from_query, MAJOR_MAPPING
from config import (VECTOR_DB_DIR, EMBEDDING_MODEL, EMBEDDING_DEVICE, RETRIEVAL_K, SIMILARITY_THRESHOLD,
                    RERANKER_MODEL,RERANKER_MAX_LENGTH,RERANKER_BATCH_SIZE,RERANKER_DEVICE,RERANKER_ENABLE, RERANKER_TOP_K)
from sentence_transformers import CrossEncoder

class University_Retrieve:
    def __init__(self, vector_db_path: str = None):
        self.vector_db_path = Path(vector_db_path or VECTOR_DB_DIR)
        # load embedding model
        print("Loading embedding model...")
        self.embedding_model = HuggingFaceEmbeddings(
            model_name = EMBEDDING_MODEL,
            model_kwargs = {"device": EMBEDDING_DEVICE},
            encode_kwargs = {"normalize_embeddings": True}
        )
        # load vector database
        print("Loading vector database...")
        if self.vector_db_path:
            self.vector_db = FAISS.load_local(
                self.vector_db_path,
                self.embedding_model,
                allow_dangerous_deserialization=True)
        else:
            self.vector_db = None
        print("Vector database loaded.")
        # Load structured data
        structure_path = self.vector_db_path/"structured_data.json"
        if structure_path.exists():
            with open(structure_path, "r", encoding="utf-8") as f:
                self.structured_data = json.load(f)
            print("✅ Structured data loaded!")
        else:
            self.structured_data = {}
            print("⚠️  No structured data found")
        # load reranker model
        if RERANKER_ENABLE:
            try:
                print("Loading reranker model...")
                self.reranker = CrossEncoder(
                    model_name= RERANKER_MODEL,
                    max_length= RERANKER_MAX_LENGTH,
                    device= RERANKER_DEVICE,
                )
                print("✅ Reranker model loaded!")
            except Exception as e:
                print(f"⚠️ Failed to load reranker: {e}")
                print("   Continuing without reranking...")
                self.reranker = None
        else:
            print("⚠️ Reranking disabled in config")
            self.reranker = None

    # ============================================
    # BASIC RETRIEVAL
    # ============================================
    def search(self, query: str, k: int = RETRIEVAL_K, filter_dict: Optional[Dict] = None) -> List[Document]:
        # Tìm kiếm cơ bản
        if self.vector_db is None:
                return []
        try:
            if filter_dict:
                raw_data = self.vector_db.similarity_search(query=query, k=k*4)
                filter_results = []
                for doc in raw_data:
                    match = all(
                        doc.metadata.get(key) == value
                        for key,value in filter_dict.items()
                    )
                    if match:
                        filter_results.append(doc)
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
            """Tìm kiếm kèm điểm số"""
            if self.vector_db is None:
                return []
            try:
                if filter_dict:
                    raw_data = self.vector_db.similarity_search_with_score(query=query, k=k*4)
                    filter_results = []
                    for doc, score in raw_data:
                        if score >= score_threshold:
                            match = all(
                                doc.metadata.get(key) == value
                                for key,value in filter_dict.items()
                            )
                            if match:
                                filter_results.append(doc)
                    return filter_results[:k]
                else:
                    results = self.vector_db.similarity_search_with_score(query=query, k=k)
                    return [(doc, score) for doc, score in results if score >= score_threshold]
                
            except Exception as e:
                print(f"⚠️ Search with score error: {e}")
                return []
    
    # ============================================
    # QUERY ROUTING
    # ============================================
    def detect_query_type(self, query: str) -> str:
        # Phát hiện loại truy vấn
        query_lower = query.lower()
        if any(kw in query_lower for kw in ['điểm','diem','điểm chuẩn', 'diem chuan', 'điểm đầu vào']):
            return "cutoff_scores" 
        if any(kw in query_lower for kw in ['tổ hợp', 'to hop', 'môn thi', 'a00', 'a01']):
            return "subject_combinations"
        if any(kw in query_lower for kw in ['tiền','phí','học phí', 'hoc phi', 'mức phí', 'chi phí']):
            return "tuition"
        if any(kw in query_lower for kw in ['làm gì', 'lam gi', 'ra trường', 'nghề nghiệp', 'việc làm', 'cơ hội việc làm', 'vị trí công việc']):
            return "career"
        if any(kw in query_lower for kw in ['học gì', 'hoc gi', 'học những gì','học những môn', 'môn gì', 'mon gi', 'môn học', 'chương trình', 'curriculum']):
            return "curriculum_major"
        if any(kw in query_lower for kw in ['phương thức', 'xét tuyển', 'xet tuyen', 'tuyển sinh', 'đăng ký']):
            return "admission_methods"
        if any(kw in query_lower for kw in ['ngành', 'nganh', 'chuyên ngành', 'major']):
            return "major_infor"
        return 'faq'

    # ============================================
    # STRUCTURED DATA RETRIEVAL
    # ============================================
    def _get_structured_scores(self, query: str) -> List[Document]:
        # Tìm kiếm diem số từ dữ liệu có cấu trúc
        parsed = parse_score_query(query=query)
        all_scores = []
        for key,value in self.structured_data.items():
            if "diem_" in key and isinstance(value,dict) and "data" in value:
                score_data = value['data']
                if parsed.get('year'):
                    score_data= [s for s in score_data if s.get('year') == parsed['year']]
                
                if parsed.get('major_id'):
                    score_data= [s for s in score_data if s.get('major_id') == parsed['major_id']]
                elif parsed.get('major_name'):
                    major_name_lower = parsed['major_name'].lower()
                    score_data = [
                        s for s in score_data
                        if major_name_lower in s.get('major_name', '').lower()
                    ]
                
                if parsed.get('to_hop'):
                    score_data= [s for s in score_data if s.get('to_hop') == parsed['to_hop']]
                
                all_scores.extend(score_data)
        if all_scores:
            all_scores.sort(key=lambda x: x.get('year', 0), reverse=True)
            return {
                'scores': all_scores[:10],  # Lấy top 10
                'total': len(all_scores),
                'query_info': parsed
            } 
        return None
    
    def _get_structured_combinations(self, query:str) -> List[Document]:
        # Tìm kiếm tổ hợp từ dữ liệu có cấu trúc
        query_upper = query.upper()
        combo_codes =  ['A00', 'A01', 'A02', 'B00', 'B01', 'B02', 'C00', 'C01', 
                       'D01', 'D02', 'D03', 'D04', 'D05', 'D06', 'D07', 'D14',
                       'V00', 'V01', 'H00', 'H01', 'DD2']
        to_hop_data = self.structured_data.get("to_hop")
        if not to_hop_data:
            return None
        combinations = to_hop_data.get('combinations', [])
        found_code = None
        for code in combo_codes:
            if code in query_upper:
                found_code = code
                break
        if found_code:
            combinations = [c for c in combinations if c.get("code") == found_code]
        return {
            'description': to_hop_data.get('description', ''),
            'combinations': combinations,
            'total': len(to_hop_data.get('combinations', []))
        }
    
    def _get_structured_tuitions(self, query:str) -> List[Document]:
        # Tìm kiếm học phí từ dữ liệu có cấu trúc
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
        
        major_infor = extract_major_from_query(query)
        if major_infor:
            major_id = major_infor['major_id']
            result['tuition_groups'] = [
                g for g in result['tuition_groups']
                if major_id in g.get('major_id',[]) or self._match_group_by_major(g.get('group_id', ''), major_infor['school_id'])
            ]
        return result
    
    def _match_group_by_major(self, group_id: str, school_id:str) -> bool:
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
    # HYBRID SEARCH
    # ============================================
    def hybrid_search(self, query: str, k: int = RETRIEVAL_K, score_threshold: float = SIMILARITY_THRESHOLD, filter_dict: Optional[Dict] = None) -> List[Tuple[Document, float]]:
        # Tìm kiếm kết hợp semantic + structured
        query_type = self.detect_query_type(query)
        major_info = extract_major_from_query(query)
        major_id = major_info['major_id'] if major_info else None
        results = {
            'query_type': query_type,
            'semantic_results': [],
            'structured_results': None,
            'context': '',
            'major_info': extract_major_from_query(query)
        }

        if query_type == "cutoff_scores":
            results['structured_results'] = self._get_structured_scores(query)
            docs = self.search(query,k = k,filter_dict= {'type': "cutoff_analysis"})
            docs = self._enhance_with_major_context(query, docs)
            results['semantic_results'] = docs[:k]
        
        elif query_type == "tuition":
            results['structured_results'] = self._get_structured_tuitions(query)
      
        elif query_type == "subject_combinations":
            if major_id:
                docs = self._search_major_content(query, major_id,k, content_type='admission')
                results['semantic_results'] = docs
            else:
                results['structured_results'] = self._get_structured_combinations(query)
        
        elif query_type == "career":
            docs = self._search_major_content(query, major_id,k, content_type='career')
            results['semantic_results'] = docs

        elif query_type == "curriculum_major":
            docs = self._search_major_content(query, major_id,k, content_type='curriculum')
            results['semantic_results'] = docs

        elif query_type == "admission_methods":
            results['semantic_results'] = self.search(query, k=k, filter_dict={'type': "admission_methods"})
            if major_id:
                docs = self._search_major_content(query, major_id,k, content_type='admission')
                results['semantic_results'] = docs
        
        elif query_type == "major_info":
            docs = self._search_major_docs(query, major_id, k)
            results['semantic_results'] = docs

        elif query_type == "faq":
            docs = self.search(query,k = k,filter_dict={'type' : 'faq'})
            if not docs and major_id:
                docs = self.search(query= major_id, k= k*5, filter_dict={'type':'major','major_id': major_id})
            docs = self._enhance_with_major_context(query,docs)
            results['semantic_results'] = docs[:k]
        
        else:
            results['semantic_results'] = self.search(query, k=k)
        
        if results['semantic_results'] and RERANKER_ENABLE and self.reranker:
            results['semantic_results'] = self.reranker_documents(query, results['semantic_results'], top_k= RERANKER_TOP_K)
        
        results['context'] = self.build_context(results)
        return results
    
    # ============================================
    # Context building
    # ============================================
    def build_context(self, result: dict) -> str:
        """
        Tạo bối cảnh cho LLM
        """
        context_parts = []
        
        # Thêm major info nếu có
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
                
                # Thêm metadata quan trọng
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
   
    # ============================================
    # UTILITY METHODS
    # ============================================
    def _filter_docs_by_metadata(self, docs: List[Document], filter_dict: Dict, target_count: int =None):
        # lọc các doc theo bộ 
        filtered = []
        for doc in docs:
            match = all(
                doc.metadata.get(key) == value
                for key,value in filter_dict.items()
            )
            if match:
                filtered.append(doc)
         # Debug logging
        if len(filtered) < len(docs):
            print(f"🔍 Filtered: {len(docs)} → {len(filtered)} docs (filter: {filter_dict})")
        
        return filtered[:target_count] if target_count else filtered
    
    def _enhance_with_major_context(self, query: str, docs: List[Document]) -> List[Document]:  
        """Ưu tiên docs liên quan đến ngành trong query"""
        major_info = extract_major_from_query(query)
        
        if not major_info or not docs:
            return docs
        
        major_id = major_info['major_id']
        variants = major_info['variants']
        
        # Phân loại docs
        relevant_docs = []
        other_docs = []
        
        for doc in docs:
            content_lower = doc.page_content.lower()
            metadata_str = json.dumps(doc.metadata, ensure_ascii=False).lower()
            
            # Check nếu doc liên quan đến major
            is_relevant = (
                major_id.lower() in metadata_str or
                any(variant in content_lower for variant in variants)
            )
            
            if is_relevant:
                relevant_docs.append(doc)
            else:
                other_docs.append(doc)
        
        return relevant_docs + other_docs

    def _search_major_docs(self, query:str, major_id: Optional[str], k:int) ->  List[Document]:
        # search major doc lien quan den cau hoi
        docs = self.search(query,k = k,filter_dict={'type' : 'major'})
        if not docs:
            docs = self.search(query= major_id, k= k*5, filter_dict={'type':'major','major_id': major_id})
        docs = self._enhance_with_major_context(query,docs)
        if major_id :
            major_filtered = [
                d for d in docs
                if d.metadata.get("major_id") == major_id
            ]
            docs = major_filtered if major_filtered else docs
        return docs[:k]
    
    def _search_major_content(self, query: str, major_id: Optional[str], k:int, content_type:str) ->List[Document]:
        # extract thông tin liên quan đến câu hỏi trong doc
        docs = self._search_major_docs(query, major_id, k*3)
        content_keywords = {
            'career': ['vị trí', 'công việc', 'nơi làm việc', 'mức lương', 
                      'nghề nghiệp', 'career', 'positions', 'workplace', 'salary'],
            'curriculum': ['học gì:', 'môn đại cương:', 'môn chuyên ngành:', 
                          'môn cơ sở ngành:', 'các môn học tiêu biểu:'],
            'admission' : ['phương thức xét tuyển']             
        }
        extract_keywords = {
            'career': ['Vị trí công việc', 'Nơi làm việc', 'Mức lương', 
                      '• Junior', '• Mid-level', '• Senior'],
            'curriculum': ['Học gì:', 'Môn đại cương:', 'Môn chuyên ngành:', 
                          'Môn cơ sở ngành:', 'Các môn học tiêu biểu:'],
            'admission' : ['Phương thức xét tuyển:','Tổ hợp môn:','Điều kiện đặc biệt:']                
        }

        keywords = content_keywords.get(content_type, [])
        extract_kw = extract_keywords.get(content_type, [])

        extracted_docs = []
        for doc in docs:
            if any(kw in doc.page_content.lower() for kw in keywords):
                try:
                    extracted_content = self._extract_section(doc.page_content,extract_kw,content_type)
                    
                    new_doc = Document(
                        page_content=extracted_content,
                        metadata={
                            **doc.metadata,
                            'content_type': f'{content_type}_only'
                        }
                    )
                    extracted_docs.append(new_doc)
                except Exception as e:
                    print(f"Error extracting: {e}")
                    extracted_docs.append(doc)
            else:
                extracted_docs.append(doc)

        return extracted_docs[:k]

    def _extract_section(self, content:str, keyword:list, section_type:str) -> str:
        
        lines = content.split('\n')
        result = []
        
        # Extract header
        header_kw = ['Tên ngành:', 'Khoa:', 'Tên trường']
        for line in lines[:5]:  
            if any(kw in line for kw in header_kw):    
                result.append(line)
        
        if result:
            result.append('')
        
        include_line = False
        stop_keywords = {
            'curriculum': ['Nhóm học phí:', 'Học phí dự kiến:', 'Phương thức xét tuyển:', 'Vị trí công việc:'],
            'career': [],  # Career extracts till end
            'admission':['Vị trí công việc']
        }
        for line in lines:
            # Check curriculum keywords
            if any(kw in line for kw in keyword):
                include_line = True
                result.append(line)
                continue
            
            # stop when reach other sections
            if include_line and (section_type == 'curriculum' or section_type == 'admission') :
                if any(kw in line for kw in stop_keywords.get(section_type,[])):
                    break
            # if include_line and section_type == 'admission' :
            #     if any(kw in line for kw in stop_keywords.get(section_type,[])):
            #         break
                
            
            # Include lines in curriculum section
            if include_line and line.strip():
                result.append(line)
        
        extracted = '\n'.join(result)
        return extracted
    
    def reranker_documents(self,
                           query:str,
                           documents: List[Document],
                           top_k:Optional[int] = None,
                           debug: bool = False) -> List[Document]:
    # Rerank documents dựa trên độ liên quan với query sử dụng CrossEncoder
        if not self.reranker:
            if debug:
                print("⚠️ Reranker not available, returning original docs")
            return documents
        
        if not documents:
            return []
        
        if len(documents)<= 1:
            return documents
        
        top_k = top_k or RERANKER_TOP_K

        try :
            pairs = [[query,doc.page_content] for doc in documents]
            reranker_score = self.reranker.predict(pairs)
            doc_score_pairs = list(zip(documents, reranker_score))
            doc_score_pairs.sort(key= lambda x:x[1], reverse= True)

            if debug: 
                print(f"\n{'='*70}")
                print(f"🔍 RERANKING DETAILS")
                print(f"{'='*70}")
                print(f"Query: {query}")
                print(f"Original docs: {len(documents)}")
                print(f"Keeping top: {top_k}")
                print(f"\nTop 5 scores after reranking:")
                for i, (doc, score) in enumerate(doc_score_pairs[:5], 1):
                    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                    major = metadata.get('major_name', 'N/A')
                    doc_type = metadata.get('type', 'N/A')
                    preview = doc.page_content[:80].replace('\n', ' ')
                    print(f"  [{i}] Score: {score:.4f} | Type: {doc_type} | Major: {major}")
                    print(f"      Preview: {preview}...")
                print(f"{'='*70}\n")

            reranked_docs = [doc for doc, score in doc_score_pairs[:top_k]]
            if not debug:
                print(f"🔄 Reranked: {len(documents)} → {len(reranked_docs)} docs")
    
            return reranked_docs
    
        except Exception as e:
            print(f"⚠️ Reranking error: {str(e)}")
            print(f"   Falling back to original top {top_k} docs")
            return documents[:top_k]

if __name__ == "__main__":
    print("\n🧪 Testing Retriever (Semantic + Structured)...\n")

    try:
        retriever = University_Retrieve()

        test_queries = [
            # "ngành Trí tuệ nhân tạo học gì",
            # "điểm chuẩn ngành Trí tuệ nhân tạo năm 2024",
            # "Học phí Trí tuệ nhân tạo",
            # "Tổ hợp A00 gồm những môn nào?",
            # "Ra trường ngành marketing làm gì?",
            # "ngành Artificial Intelligence ra trường làm công việc gì ?",
            # "ngành AI học gì",
            "Tổ hợp môn của ngành du lịch là gì"
        ]

        for query in test_queries:
            print(f"\n{'='*80}")
            print(f"🔎 Query: {query}")

            query_type = retriever.detect_query_type(query)
            print(f"📌 Detected type: {query_type}")

            result = retriever.hybrid_search(query, k=2)

            semantic_results = result.get("semantic_results", [])
            structured_results = result.get("structured_results")

            # ===== Summary =====
            print("\n📊 RESULT SUMMARY")
            print(f"- Semantic results: {len(semantic_results)} document(s)")
            print(f"- Structured results: {'YES' if structured_results else 'NO'}")

            # ===== Semantic preview =====
            if semantic_results:
                print("\n🧠 SEMANTIC RESULTS PREVIEW")
                for i, doc in enumerate(semantic_results, 1):
                    preview = doc.page_content.replace("\n", " ")
                    print(f"\n  [{i}] {preview}...")
                    if doc.metadata:
                        meta = {
                            k: v for k, v in doc.metadata.items()
                            if k in ["type", "major_id", "major_name", "school_id"]
                        }
                        if meta:
                            print(f"      Metadata: {meta}")

            # ===== Structured preview =====
            if structured_results:
                print("\n📐 STRUCTURED RESULTS PREVIEW")
                if isinstance(structured_results, dict):
                    # in gọn, không spam
                    print(json.dumps(structured_results, ensure_ascii=False, indent=2)[:800])
                else:
                    print(structured_results)

            if not semantic_results and not structured_results:
                print("\n⚠️  NO DATA FOUND FOR THIS QUERY")

        print(f"\n{'='*80}")
        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()