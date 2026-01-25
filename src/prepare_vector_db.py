import json
import jsonschema
from pathlib import Path
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document



class University_vector_db:
    def __init__(self, vector_db_path: str, data_path: str):
        self.vector_db_path = Path(vector_db_path)
        self.data_path = Path(data_path)
        self.embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n",".", " ", ""]
        )
        self.structured_data = {
        "to_hop": [],
        "hoc_phi": [],
        "admission_methods": []
        }

    def load_schema(self, schema_name: str) -> Dict:
        """Load JSON Schema để validate"""
        schema_path = self.data_path / "schema" / f"{schema_name}.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # """Validate data"""       
    def validate_document(self, data: Dict, schema: Dict) -> bool:
       
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True
        except jsonschema.ValidationError as e:
            print(f"Validation error: {e.message}")
            return False
        
    #"""Load một file JSON"""         
    def load_json_file(self, file_path: Path) -> Dict:
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    #"""Tạo Document từ dữ liệu chuyên ngành"""
    def create_document_from_major(self, major_data: Dict, file_path: Path ) -> Document:
        
        # Validate dữ liệu với schema
        schema = self.load_schema("major.schema")
        if not self.validate_document(major_data, schema):
            raise ValueError(f"Invalid major data in {file_path}")

            
        # Tạo nội dung text để embedding
        content_parts = [
            f"Tên ngành: {major_data.get('major_name', '')}",
            f"Mã ngành: {major_data.get('major_id', '')}",
            f"Mã ngành nội bộ: {major_data.get('major_code_ministry', '')}",
            f"Tên trường đại học: {major_data.get('university', '')}",
            f"Khoa: {major_data.get('school_name', '')}"
        ]
    
        # Mô tả chuyên ngành
        descriptions = major_data['description']
        content_parts.append(f"\nMục tiêu: {descriptions.get('muc_tieu', '')}")
        content_parts.append(f"Vấn đề thực tế: {descriptions.get('van_de_thuc_te', '')}")
        content_parts.append(f"Học gì: {descriptions.get('hoc_gi', '')}")      

        
        # Cơ hội việc làm
        if 'curriculum' in major_data:
            curriculum = major_data['curriculum']
            if "mon_dai_cuong" in curriculum:
                mon_list = ", ".join(curriculum['mon_dai_cuong'])
                content_parts.append(f"\nMôn đại cương: {mon_list}")
                
            if "mon_chuyen_nganh" in curriculum:
                mon_list = ", ".join(curriculum['mon_chuyen_nganh'])
                content_parts.append(f"Môn chuyên ngành: {mon_list}")
            
            if "mon_co_so_nganh" in curriculum:
                mon_list = ", ".join(curriculum['mon_co_so_nganh'])
                content_parts.append(f"Môn cơ sở ngành: {mon_list}")
            
            if "mon_tieu_bieu" in curriculum:
                content_parts.append("\nCác môn học tiêu biểu:")
                for mon in curriculum['mon_tieu_bieu']:
                    content_parts.append(
                        f"  - {mon['ten_mon']}: {mon.get('mo_ta', '')}"
                    )
       
        # học phí
        tuition = major_data['tuition']
        content_parts.append(f"\nNhóm học phí: {tuition.get('group_id', '')}")
        content_parts.append(f"Học phí dự kiến: {tuition.get('per_year_estimate', '')}")
        
        # xét tuyển
        if 'admission' in major_data:
            admission = major_data['admission']
            
            if "methods" in admission and admission['methods']: 
                method_list = ", ".join(admission['methods'])
                content_parts.append(f"\nPhương thức xét tuyển: {method_list}")
            
            if "to_hop" in admission and admission['to_hop']:
                to_hop_list = ", ".join(admission['to_hop'])
                content_parts.append(f"Tổ hợp môn: {to_hop_list}")
            
            # if 'diem_chuan' in admission:
            #     content_parts.append(f"Điểm chuẩn tham khảo: {admission.get('diem_chuan', '')}")
            
            if "dieu_kien_dac_biet" in admission and admission['dieu_kien_dac_biet']:
                dieu_kien_dac_biet_list = ", ".join(admission['dieu_kien_dac_biet'])
                content_parts.append(f"Điều kiện đặc biệt: {dieu_kien_dac_biet_list}")
        
        # công việc sau khi tốt nghiệp
        if 'career' in major_data:
            career = major_data['career']
            
            if "positions" in career and career['positions']:
                positions_list = ", ".join(career['positions'])
                content_parts.append(f"\nVị trí công việc: {positions_list}")
                
            if "workplace" in career and career['workplace']:
                workplace_list = ", ".join(career['workplace'])
                content_parts.append(f"Nơi làm việc: {workplace_list}")
                
            if 'salary' in career:
                salary_list = career['salary']
                content_parts.append("\nMức lương:")
                if 'junior' in salary_list:
                    content_parts.append(f"  • Junior: {salary_list['junior']}")
                    
                if 'mid' in salary_list:
                    content_parts.append(f"  • Mid-level: {salary_list['mid']}")
                    
                if 'senior' in salary_list:
                    content_parts.append(f"  • Senior: {salary_list['senior']}")
        
        content = "\n".join(content_parts)
        
        # Metadata để filter và retrieve hiệu quả
        metadata = {
        'source': str(file_path),
        'type': 'major',
        'major_id': major_data.get('major_id', ''),
        'major_code_ministry': major_data.get('major_code_ministry', ''),
        'major_name': major_data.get('major_name', ''),
        'school_id': major_data.get('school_id', ''),
        'school_name': major_data.get('school_name', ''),
        'university': major_data.get('university', ''),
        'language': major_data.get('metadata', {}).get('language', 'vi'),
        'version': major_data.get('metadata', {}).get('version', '2025'),
        }
        
        return Document(page_content=content, metadata=metadata)

    # Tạo document cho admissions/phuong thuc xet tuyen
    def create_document_from_Method(self, method_data: Dict, file_path: Path) -> Document:
         # Validate dữ liệu với schema
        schema = self.load_schema("admission.schema")
        if not self.validate_document(method_data, schema):
            raise ValueError(f"Invalid major data in {file_path}")
        methods = method_data['methods']
        doc_list = []
        for method in methods:
            content_parts = []
            content_parts.append(f"Mã phương thức: {method.get('code', '')}")
            content_parts.append(f"Tên phương thức xét tuyển: {method.get('name', '')}")
            content_parts.append(f"Mô tả phương thức xét tuyển: {method.get('description', '')}")
            content_parts.append(f"Lưu ý: {method.get('note', '')}")
            metadata = {
                'source': str(file_path),
                'type': 'admission_method',
                'Mã phương thức': method.get('code', '')
            }
            content = "\n".join(content_parts)
            doc_list.append(Document(page_content=content, metadata=metadata))
        return doc_list
    
    # Tạo document cho xu hướng điểm
    def create_cutoff_analysis_docs(self, cutoff_data: Dict, path: Path) -> Document:
        """
        CHỈ embed phần ngữ nghĩa:
        - analysis
        - trend
        - note (nếu có)

        TUYỆT ĐỐI KHÔNG embed số điểm
        """
        docs = []

        for item in cutoff_data.get("data", []):
            analysis = item.get("analysis")
            trend = item.get("trend")

            if not analysis and not trend:
                continue

            content = [
                        f"Ngành: {item['major_name']}",
                        f"Nhận định tuyển sinh: {analysis or ''}",
                        f"Xu hướng điểm chuẩn: {trend or ''}"
                    ]

            docs.append(Document(
                page_content="\n".join(content),
                metadata={
                    "type": "cutoff_analysis",
                    "major_id": item["major_id"],
                    "source": str(path)
                }
            ))

        return docs
    
    # Tạo document cho faq
    def create_document_from_faq(self, faq_data: Dict, file_path: Path) -> List[Document]:
        docs = []
        school_id = faq_data.get("school_id")
        school_name = faq_data.get("school_name")
        university = faq_data.get("university")
        for faq_item in faq_data.get("data", []):
            content = []
            question = faq_item.get("question")
            answer = faq_item.get("answer")
            tags = faq_item.get("tags")
            
            content.append(f"Câu hỏi: {question}" )
            content.append(f"Câu trả lời: {answer}" )
            content.append(f"Trường: {school_name}" )
            if tags:
                tags_text = ", ".join(tags)
                content.append(f"Tags: {tags_text}" )
            
            metadata = {
            'source': str(file_path),
            'type': 'faq',
            'faq_id': faq_item.get('faq_id', ''),
            'scope': faq_item.get('scope', ''),  # 'major', 'school', 'general'
            'school_id': school_id,
            'school_name': school_name,
            'university': university,
            'question': question,  # Lưu để hiển thị
            'tags': ', '.join(tags) if tags else '',
            }
            major_id = faq_item.get("major_id")
            if 'major_id' in faq_item:
                metadata['major_id'] = faq_item['major_id']
                
            docs.append(Document(
                page_content="\n".join(content),
                metadata = metadata
            ))

        return docs
    
    # Tạo structure cho tổ hợp, điểm chuẩn, học phí
    def load_structure_data(self):
        adm = self.data_path / "admissions"
        self.structured_data["to_hop"] = self.load_json_file(adm / "to_hop_mon.json")
        self.structured_data["admission_methods"] = self.load_json_file(adm / "phuong_thuc_xet_tuyen.json")
        self.structured_data["hoc_phi"] = self.load_json_file(adm / "hoc_phi.json")
        score_major = adm / "diem_chuan_theo_nam"
        for major in score_major.glob("*.json"):   
            self.structured_data[major.name] = self.load_json_file(major)
    
    # lưu structured data       
    def save_structured_data(self):
        output = self.vector_db_path / "structured_data.json"
        with open(output, "w", encoding="utf-8") as f:
            json.dump(self.structured_data, f, ensure_ascii=False, indent=2)
    
    # Load all data vào 1 document
    def load_all_data(self) -> list[Document]:
        all_document = []
        
        # Load majors
        majors_path = self.data_path / "majors"
        if majors_path.exists():
            for major_category in majors_path.iterdir():
                if major_category.is_dir():
                    for major_file in major_category.glob("*.json"):
                        try: 
                            major_data = self.load_json_file(major_file)
                            doc = self.create_document_from_major(major_data, major_file)
                            all_document.append(doc)
                            print(f"✓ Loaded major: {major_category.name}/{major_file.name}")
                        except Exception as e:
                            print(f"Error processing {major_file}: {e}")
        else:
            print(f"Majors path {majors_path} is not a directory.")    
        
        # Load admission methods
        admission_method_path = self.data_path / "admissions" / "phuong_thuc_xet_tuyen.json"
        if admission_method_path.exists():
            method_data = self.load_json_file(admission_method_path)
            doc = self.create_document_from_Method(method_data, admission_method_path)
            all_document.extend(doc)
            print(f"✓ Loaded method: {admission_method_path.name}")
        
        #load analysis diem 
        analysis_path = self.data_path / "admissions" / "diem_chuan_theo_nam"
        if analysis_path.exists():
            for analysis_major_path in analysis_path.glob("*.json"):
                all_document.extend(self.create_cutoff_analysis_docs(self.load_json_file(analysis_major_path), analysis_major_path))
                print(f"✓ Loaded analysis: {analysis_major_path.name}")
        # load faq
        faq_path = self.data_path / "faq" 
        if faq_path.exists():
            for faq_major_path in faq_path.glob("*.json"):
                all_document.extend(self.create_document_from_faq(self.load_json_file(faq_major_path), faq_major_path))
                print(f"✓ Loaded faq: {faq_major_path.name}")
        # load structure data
        self.load_structure_data()
        return all_document
   
    # Tạo vector db
    def create_vector_db(self):
        print("Loading data and creating vector database...")
        documents = self.load_all_data()
        print(f"Total documents loaded: {len(documents)}")
        
        # ✅ Phân loại documents để chunking khác nhau
        major_docs = [d for d in documents if d.metadata.get('type') == 'major']
        other_docs = [d for d in documents if d.metadata.get('type') != 'major']
        
        # Major documents: KHÔNG chunk
        # Other documents: Chunk bình thường
        chunked_others = self.text_splitter.split_documents(other_docs)
        
        # Kết hợp
        all_docs_for_embedding = major_docs + chunked_others
        
        print(f"- Major docs (no chunking): {len(major_docs)}")
        print(f"- Other docs (chunked): {len(chunked_others)}")
        print(f"- Total for embedding: {len(all_docs_for_embedding)}")
        
        vector_db = FAISS.from_documents(
            documents=all_docs_for_embedding, 
            embedding=self.embeddings_model
        )
        
        vector_db.save_local(self.vector_db_path)
        print(f"Vector database saved at {self.vector_db_path}")
        
        self.save_structured_data()
        print(f"Structured data saved at {self.vector_db_path / 'structured_data.json'}")
        return vector_db
    
if __name__ == "__main__":
    vector_db_path = "D:/Chatbox_tuyensinh/university_vector_db"
    data_path = "D:/Chatbox_tuyensinh/data"

    university_vector_db = University_vector_db(vector_db_path, data_path)                       
    university_vector_db.create_vector_db()
    # doc = university_vector_db.load_all_data()
    # # university_vector_db.load_structure_data()
    # for i in range(len(doc)):
    #     print(doc[i])
    #     print("--------------------------------------------------------------------------------")
    
    # faq_path = Path(data_path)/ "faq" / "faq_tuyen_sinh.json"
    # data = university_vector_db.load_json_file(faq_path)
    # docs = university_vector_db.create_document_from_faq(data,faq_path)
    # for i in range(len(docs)):
    #     print("📄 SAMPLE DOCUMENT:")
    #     print("-"*70)
    #     print(docs[i].page_content)
    #     print("-"*70)
    #     print("\n🏷️  METADATA:")
    #     for key, value in docs[i].metadata.items():
    #         print(f"  {key}: {value}")
    #     print("="*70)
    

