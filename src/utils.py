import re 
from typing import List, Dict, Optional
from langchain_core.documents import Document

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n+','\n', text)              
    return text.strip()


def format_source(source:  List[Document]) -> str:
    formatted_sources = []
    if not source:
        return "Không có nguồn tham khảo."
    for i,doc in enumerate(source,1):
        metadata = doc.metadata
        doc_type = metadata.get('type', 'Unknown Source')
        if doc_type == 'Major':
            header = f"📚 Ngành: {metadata.get('major_name', 'N/A')}"
        elif doc_type == 'University':
            header = f"❓ FAQ: {metadata.get('question', 'N/A')[:50]}..."
        else:
            header = f"📄 {doc_type}"
        content = doc.page_content[:150].replace('\n', ' ')
        formatted_sources.append(f"Nguồn{i}. {header}\n   Nội dung: {content}...")
    return "\n\n".join(formatted_sources)

def truncate_text(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'

def parse_score_query(query: str) -> Dict:
    """Parse câu hỏi về điểm chuẩn"""
    query_lower = query.lower().strip()
    result = {
        'major_id': None,
        'major_name': None,
        'variants': None,
        'year': None,
        'to_hop': None,
        'school_id':None
    }
    
    # Extract year
    year_match = re.search(r'202[0-9]', query)
    if year_match:
        result['year'] = int(year_match.group())
    
    # Extract subject combo
    combo_match = re.search(r'[A-Z]\d{2}', query.upper())
    if combo_match:
        result['to_hop'] = combo_match.group()
    
    for major_id, info in MAJOR_MAPPING.items():
        variants = info['variants']
        if any(variant in query_lower for variant in variants):
                result['major_id'] = major_id
                result['major_name'] = info['name']
                result['school_id'] = info['school_id']
                result['variants'] = info['variants']
                break
    return result
def extract_major_from_query(query: str) -> Optional[Dict]:
    query_lower = query.lower()
    for major_id, info in MAJOR_MAPPING.items():
        if any(v in query_lower for v in info["variants"]):
            return {
                "major_id": major_id,
                "variants": info["variants"],
                "school_id": info["school_id"],
                "major_name": info["name"]
            }
    return None
MAJOR_MAPPING = {
    # ========================================
    # 1️⃣ TRƯỜNG KHOA HỌC MÁY TÍNH (CS)
    # ========================================
    'CS_CS': {
        'name': 'Khoa học máy tính',
        'ministry_code': '7480101',
        'school_id': 'CS',
        'school_name': 'Trường Khoa học Máy tính',
        'domain': 'CNTT',
        'variants': [
            'khoa học máy tính',
            'khoa hoc may tinh',
            'khmt',
            'computer science',
            'cs'
        ]
    },
    'CS_SE': {
        'name': 'Kỹ thuật phần mềm',
        'ministry_code': '7480103',
        'school_id': 'CS',
        'school_name': 'Trường Khoa học Máy tính',
        'domain': 'CNTT',
        'variants': [
            'kỹ thuật phần mềm',
            'ky thuat phan mem',
            'ktpm',
            'software engineering',
            'se'
        ]
    },
    'CS_AI': {
        'name': 'Trí tuệ nhân tạo',
        'ministry_code': '7480107',
        'school_id': 'CS_AI',
        'school_name': 'Trường Khoa học Máy tính',
        'domain': 'CNTT',
        'variants': [
            'trí tuệ nhân tạo',
            'tri tue nhan tao',
            'ai',
            'artificial intelligence',
            'trí tuệ nhân tạo ai'
        ]
    },
    'CS_DS': {
        'name': 'Khoa học dữ liệu',
        'ministry_code': '7480109',  # hoặc 7480201
        'school_id': 'CS',
        'school_name': 'Trường Khoa học Máy tính',
        'domain': 'CNTT',
        'variants': [
            'khoa học dữ liệu',
            'khoa hoc du lieu',
            'khdt',
            'data science',
            'ds'
        ]
    },
    'CS_IS': {
        'name': 'An toàn thông tin',
        'ministry_code': '7480202',
        'school_id': 'CS',
        'school_name': 'Trường Khoa học Máy tính',
        'domain': 'CNTT',
        'variants': [
            'an toàn thông tin',
            'an toan thong tin',
            'attt',
            'information security',
            'security',
            'cyber security'
        ]
    },
    'CS_NET': {
        'name': 'Mạng máy tính và Truyền thông dữ liệu',
        'ministry_code': '7480108',
        'school_id': 'CS',
        'school_name': 'Trường Khoa học Máy tính',
        'domain': 'CNTT',
        'variants': [
            'mạng máy tính',
            'mang may tinh',
            'truyền thông dữ liệu',
            'truyen thong du lieu',
            'network',
            'networking'
        ]
    },
    
    # ========================================
    # 2️⃣ TRƯỜNG CÔNG NGHỆ / KỸ THUẬT (ENG)
    # ========================================
    'ENG_EE': {
        'name': 'Kỹ thuật điện',
        'ministry_code': '7520201',
        'school_id': 'ENG',
        'school_name': 'Trường Công nghệ',
        'domain': 'Engineering',
        'variants': [
            'kỹ thuật điện',
            'ky thuat dien',
            'ktd',
            'electrical engineering',
            'điện'
        ]
    },
    'ENG_EEE': {
        'name': 'Kỹ thuật điện - điện tử',
        'ministry_code': '7520207',
        'school_id': 'ENG',
        'school_name': 'Trường Công nghệ',
        'domain': 'Engineering',
        'variants': [
            'kỹ thuật điện điện tử',
            'ky thuat dien dien tu',
            'điện điện tử',
            'dien dien tu',
            'electrical electronics'
        ]
    },
    'ENG_MECHATRONICS': {
        'name': 'Cơ điện tử',
        'ministry_code': '7520114',
        'school_id': 'ENG',
        'school_name': 'Trường Công nghệ',
        'domain': 'Engineering',
        'variants': [
            'cơ điện tử',
            'co dien tu',
            'mechatronics'
        ]
    },
    'ENG_AUTOMATION': {
        'name': 'Điều khiển và Tự động hóa',
        'ministry_code': '7520216',
        'school_id': 'ENG',
        'school_name': 'Trường Công nghệ',
        'domain': 'Engineering',
        'variants': [
            'điều khiển tự động hóa',
            'dieu khien tu dong hoa',
            'tự động hóa',
            'tu dong hoa',
            'automation',
            'điều khiển và tự động hóa'
        ]
    },
    'ENG_MANUFACTURING': {
        'name': 'Công nghệ chế tạo máy',
        'ministry_code': '7520118',
        'school_id': 'ENG',
        'school_name': 'Trường Công nghệ',
        'domain': 'Engineering',
        'variants': [
            'công nghệ chế tạo máy',
            'cong nghe che tao may',
            'chế tạo máy',
            'che tao may',
            'manufacturing'
        ]
    },
    'ENG_AUTOMOTIVE': {
        'name': 'Công nghệ ô tô',
        'ministry_code': '7510205',
        'school_id': 'ENG',
        'school_name': 'Trường Công nghệ',
        'domain': 'Engineering',
        'variants': [
            'công nghệ ô tô',
            'cong nghe o to',
            'ô tô',
            'o to',
            'automotive'
        ]
    },
    'ENG_CIVIL': {
        'name': 'Kỹ thuật xây dựng',
        'ministry_code': '7580201',
        'school_id': 'ENG',
        'school_name': 'Trường Công nghệ',
        'domain': 'Engineering',
        'variants': [
            'kỹ thuật xây dựng',
            'ky thuat xay dung',
            'xây dựng',
            'xay dung',
            'civil engineering'
        ]
    },
    'ENG_CIVIL_TECH': {
        'name': 'Công nghệ kỹ thuật công trình xây dựng',
        'ministry_code': '7510103',
        'school_id': 'ENG',
        'school_name': 'Trường Công nghệ',
        'domain': 'Engineering',
        'variants': [
            'công nghệ kỹ thuật công trình xây dựng',
            'cong nghe ky thuat cong trinh xay dung',
            'công trình xây dựng',
            'cong trinh xay dung'
        ]
    },
    'ENG_TRANSPORT_CIVIL': {
        'name': 'Xây dựng công trình giao thông',
        'ministry_code': '7580205',
        'school_id': 'ENG',
        'school_name': 'Trường Công nghệ',
        'domain': 'Engineering',
        'variants': [
            'xây dựng công trình giao thông',
            'xay dung cong trinh giao thong',
            'công trình giao thông',
            'cong trinh giao thong',
            'transport civil'
        ]
    },
    'ENG_ARCH': {
        'name': 'Kiến trúc',
        'ministry_code': '7580101',
        'school_id': 'ENG',
        'school_name': 'Trường Công nghệ',
        'domain': 'Engineering',
        'variants': [
            'kiến trúc',
            'kien truc',
            'architecture'
        ]
    },
    'ENG_GRAPHIC': {
        'name': 'Thiết kế đồ họa',
        'ministry_code': '7210403',
        'school_id': 'ENG',
        'school_name': 'Trường Công nghệ',
        'domain': 'Design',
        'variants': [
            'thiết kế đồ họa',
            'thiet ke do hoa',
            'đồ họa',
            'do hoa',
            'graphic design'
        ]
    },
    'ENG_FASHION': {
        'name': 'Thiết kế thời trang',
        'ministry_code': '7210404',
        'school_id': 'ENG',
        'school_name': 'Trường Công nghệ',
        'domain': 'Design',
        'variants': [
            'thiết kế thời trang',
            'thiet ke thoi trang',
            'thời trang',
            'thoi trang',
            'fashion design'
        ]
    },
    
    # ========================================
    # 3️⃣ TRƯỜNG Y - DƯỢC (MED)
    # ========================================
    'MED_MD': {
        'name': 'Y khoa',
        'ministry_code': '7720101',
        'school_id': 'MED',
        'school_name': 'Trường Y - Dược',
        'domain': 'Medical',
        'variants': [
            'y khoa',
            'y',
            'medicine',
            'bác sĩ',
            'bac si'
        ]
    },
    'MED_DENTAL': {
        'name': 'Răng - Hàm - Mặt',
        'ministry_code': '7720501',
        'school_id': 'MED',
        'school_name': 'Trường Y - Dược',
        'domain': 'Medical',
        'variants': [
            'răng hàm mặt',
            'rang ham mat',
            'nha khoa',
            'dental',
            'dentistry'
        ]
    },
    'MED_PHARMACY': {
        'name': 'Dược học',
        'ministry_code': '7720201',
        'school_id': 'MED',
        'school_name': 'Trường Y - Dược',
        'domain': 'Medical',
        'variants': [
            'dược học',
            'duoc hoc',
            'dược',
            'duoc',
            'pharmacy',
            'dược sĩ'
        ]
    },
    'MED_NURSING': {
        'name': 'Điều dưỡng',
        'ministry_code': '7720301',
        'school_id': 'MED',
        'school_name': 'Trường Y - Dược',
        'domain': 'Medical',
        'variants': [
            'điều dưỡng',
            'dieu duong',
            'nursing',
            'y tá',
            'y ta'
        ]
    },
    'MED_BIOTECH': {
        'name': 'Công nghệ sinh học',
        'ministry_code': '7420201',
        'school_id': 'MED',
        'school_name': 'Trường Y - Dược',
        'domain': 'Medical',
        'variants': [
            'công nghệ sinh học',
            'cong nghe sinh hoc',
            'sinh học',
            'sinh hoc',
            'biotechnology',
            'biotech'
        ]
    },
    'MED_BIOMED': {
        'name': 'Kỹ thuật y sinh',
        'ministry_code': '7520212',
        'school_id': 'MED',
        'school_name': 'Trường Y - Dược',
        'domain': 'Medical',
        'variants': [
            'kỹ thuật y sinh',
            'ky thuat y sinh',
            'y sinh',
            'biomedical engineering'
        ]
    },
    
    # ========================================
    # 4️⃣ TRƯỜNG KINH TẾ (ECON)
    # ========================================
    'ECON_BA': {
        'name': 'Quản trị kinh doanh',
        'ministry_code': '7340101',
        'school_id': 'ECON',
        'school_name': 'Trường Kinh tế',
        'domain': 'Business',
        'variants': [
            'quản trị kinh doanh',
            'quan tri kinh doanh',
            'qtkd',
            'business administration',
            'kinh doanh'
        ]
    },
    'ECON_MARKETING': {
        'name': 'Marketing',
        'ministry_code': '7340115',
        'school_id': 'ECON',
        'school_name': 'Trường Kinh tế',
        'domain': 'Business',
        'variants': [
            'marketing',
            'tiếp thị',
            'tiep thi'
        ]
    },
    'ECON_COMMERCE': {
        'name': 'Kinh doanh thương mại',
        'ministry_code': '7340121',
        'school_id': 'ECON',
        'school_name': 'Trường Kinh tế',
        'domain': 'Business',
        'variants': [
            'kinh doanh thương mại',
            'kinh doanh thuong mai',
            'thương mại',
            'thuong mai',
            'commerce'
        ]
    },
    'ECON_ECOMMERCE': {
        'name': 'Thương mại điện tử',
        'ministry_code': '7340122',
        'school_id': 'ECON',
        'school_name': 'Trường Kinh tế',
        'domain': 'Business',
        'variants': [
            'thương mại điện tử',
            'thuong mai dien tu',
            'tmdt',
            'ecommerce',
            'e-commerce'
        ]
    },
    'ECON_FINANCE': {
        'name': 'Tài chính - Ngân hàng',
        'ministry_code': '7340201',
        'school_id': 'ECON',
        'school_name': 'Trường Kinh tế',
        'domain': 'Finance',
        'variants': [
            'tài chính ngân hàng',
            'tai chinh ngan hang',
            'tài chính',
            'tai chinh',
            'ngân hàng',
            'ngan hang',
            'finance',
            'banking'
        ]
    },
    'ECON_ACCOUNTING': {
        'name': 'Kế toán',
        'ministry_code': '7340301',
        'school_id': 'ECON',
        'school_name': 'Trường Kinh tế',
        'domain': 'Finance',
        'variants': [
            'kế toán',
            'ke toan',
            'accounting'
        ]
    },
    'ECON_AUDIT': {
        'name': 'Kiểm toán',
        'ministry_code': '7340302',
        'school_id': 'ECON',
        'school_name': 'Trường Kinh tế',
        'domain': 'Finance',
        'variants': [
            'kiểm toán',
            'kiem toan',
            'audit',
            'auditing'
        ]
    },
    'ECON_HRM': {
        'name': 'Quản trị nhân lực',
        'ministry_code': '7340404',
        'school_id': 'ECON',
        'school_name': 'Trường Kinh tế',
        'domain': 'Business',
        'variants': [
            'quản trị nhân lực',
            'quan tri nhan luc',
            'qtnl',
            'nhân sự',
            'nhan su',
            'hr',
            'human resources'
        ]
    },
    'ECON_INVESTMENT': {
        'name': 'Kinh tế đầu tư',
        'ministry_code': '7310104',
        'school_id': 'ECON',
        'school_name': 'Trường Kinh tế',
        'domain': 'Finance',
        'variants': [
            'kinh tế đầu tư',
            'kinh te dau tu',
            'đầu tư',
            'dau tu',
            'investment'
        ]
    },
    
    # ========================================
    # 5️⃣ TRƯỜNG DU LỊCH (TOUR)
    # ========================================
    'TOUR_TOURISM': {
        'name': 'Du lịch',
        'ministry_code': '7810101',
        'school_id': 'TOUR',
        'school_name': 'Trường Du lịch',
        'domain': 'Tourism',
        'variants': [
            'du lịch',
            'du lich',
            'tourism'
        ]
    },
    'TOUR_TRAVEL': {
        'name': 'Quản lý dịch vụ Du lịch và Lữ hành',
        'ministry_code': '7810103',
        'school_id': 'TOUR',
        'school_name': 'Trường Du lịch',
        'domain': 'Tourism',
        'variants': [
            'quản lý dịch vụ du lịch',
            'quan ly dich vu du lich',
            'lữ hành',
            'lu hanh',
            'travel management'
        ]
    },
    'TOUR_HOTEL': {
        'name': 'Quản trị khách sạn',
        'ministry_code': '7810201',
        'school_id': 'TOUR',
        'school_name': 'Trường Du lịch',
        'domain': 'Hospitality',
        'variants': [
            'quản trị khách sạn',
            'quan tri khach san',
            'khách sạn',
            'khach san',
            'hotel management',
            'hotel'
        ]
    },
    'TOUR_RESTAURANT': {
        'name': 'Quản trị nhà hàng và dịch vụ ăn uống',
        'ministry_code': '7810202',
        'school_id': 'TOUR',
        'school_name': 'Trường Du lịch',
        'domain': 'Hospitality',
        'variants': [
            'quản trị nhà hàng',
            'quan tri nha hang',
            'nhà hàng',
            'nha hang',
            'ăn uống',
            'an uong',
            'restaurant management'
        ]
    },
    'TOUR_EVENT': {
        'name': 'Quản trị sự kiện',
        'ministry_code': '7340403',
        'school_id': 'TOUR',
        'school_name': 'Trường Du lịch',
        'domain': 'Hospitality',
        'variants': [
            'quản trị sự kiện',
            'quan tri su kien',
            'sự kiện',
            'su kien',
            'event management'
        ]
    },
    
    # ========================================
    # 6️⃣ NGOẠI NGỮ - KHXH&NV (LANG)
    # ========================================
    'LANG_EN': {
        'name': 'Ngôn ngữ Anh',
        'ministry_code': '7220201',
        'school_id': 'LANG',
        'school_name': 'Trường Ngoại ngữ và Khoa học Xã hội',
        'domain': 'Language',
        'variants': [
            'ngôn ngữ anh',
            'ngon ngu anh',
            'tiếng anh',
            'tieng anh',
            'ngoại ngữ anh',
            'english',
            'anh văn'
        ]
    },
    'LANG_CN': {
        'name': 'Ngôn ngữ Trung Quốc',
        'ministry_code': '7220204',
        'school_id': 'LANG',
        'school_name': 'Trường Ngoại ngữ và Khoa học Xã hội',
        'domain': 'Language',
        'variants': [
            'ngôn ngữ trung quốc',
            'ngon ngu trung quoc',
            'tiếng trung',
            'tieng trung',
            'trung quốc',
            'chinese',
            'hán ngữ'
        ]
    },
    'LANG_JP': {
        'name': 'Ngôn ngữ Nhật',
        'ministry_code': '7220209',
        'school_id': 'LANG',
        'school_name': 'Trường Ngoại ngữ và Khoa học Xã hội',
        'domain': 'Language',
        'variants': [
            'ngôn ngữ nhật',
            'ngon ngu nhat',
            'tiếng nhật',
            'tieng nhat',
            'nhật bản',
            'japanese',
            'nhật ngữ'
        ]
    },
    'LANG_KR': {
        'name': 'Ngôn ngữ Hàn Quốc',
        'ministry_code': '7220210',
        'school_id': 'LANG',
        'school_name': 'Trường Ngoại ngữ và Khoa học Xã hội',
        'domain': 'Language',
        'variants': [
            'ngôn ngữ hàn quốc',
            'ngon ngu han quoc',
            'tiếng hàn',
            'tieng han',
            'hàn quốc',
            'korean',
            'hàn ngữ'
        ]
    },
    'LANG_LITERATURE': {
        'name': 'Văn học',
        'ministry_code': '7229030',
        'school_id': 'LANG',
        'school_name': 'Trường Ngoại ngữ và Khoa học Xã hội',
        'domain': 'Literature',
        'variants': [
            'văn học',
            'van hoc',
            'literature'
        ]
    },
    'LANG_VN_STUDIES': {
        'name': 'Việt Nam học',
        'ministry_code': '7310630',
        'school_id': 'LANG',
        'school_name': 'Trường Ngoại ngữ và Khoa học Xã hội',
        'domain': 'Social Science',
        'variants': [
            'việt nam học',
            'viet nam hoc',
            'vietnamese studies'
        ]
    },
    'LANG_IR': {
        'name': 'Quan hệ quốc tế',
        'ministry_code': '7310206',
        'school_id': 'LANG',
        'school_name': 'Trường Ngoại ngữ và Khoa học Xã hội',
        'domain': 'Social Science',
        'variants': [
            'quan hệ quốc tế',
            'quan he quoc te',
            'qhqt',
            'international relations',
            'ir'
        ]
    },
    'LANG_PR': {
        'name': 'Quan hệ công chúng',
        'ministry_code': '7320108',
        'school_id': 'LANG',
        'school_name': 'Trường Ngoại ngữ và Khoa học Xã hội',
        'domain': 'Communication',
        'variants': [
            'quan hệ công chúng',
            'quan he cong chung',
            'qhcc',
            'pr',
            'public relations'
        ]
    },
    'LANG_MULTIMEDIA': {
        'name': 'Truyền thông đa phương tiện',
        'ministry_code': '7320104',
        'school_id': 'LANG',
        'school_name': 'Trường Ngoại ngữ và Khoa học Xã hội',
        'domain': 'Communication',
        'variants': [
            'truyền thông đa phương tiện',
            'truyen thong da phuong tien',
            'truyền thông',
            'truyen thong',
            'multimedia',
            'media'
        ]
    },
    'LANG_LAW': {
        'name': 'Luật',
        'ministry_code': '7380101',
        'school_id': 'LANG',
        'school_name': 'Trường Ngoại ngữ và Khoa học Xã hội',
        'domain': 'Law',
        'variants': [
            'luật',
            'luat',
            'law'
        ]
    },
    'LANG_ECON_LAW': {
        'name': 'Luật kinh tế',
        'ministry_code': '7380107',
        'school_id': 'LANG',
        'school_name': 'Trường Ngoại ngữ và Khoa học Xã hội',
        'domain': 'Law',
        'variants': [
            'luật kinh tế',
            'luat kinh te',
            'economic law'
        ]
    },
}
# Test
if __name__ == "__main__":
    print("Testing utils...")
    
    # Test truncate
    long_text = "This is a very long text " * 20
    print(f"Truncated: {truncate_text(long_text, 50)}")
    
    # Test parse
    query = "điểm chuẩn ngành tri tue nhan tao năm 2024 tổ hợp A00"
    result = parse_score_query(query)
    print(f"Parsed: {result}")
    
    print("✅ Utils test completed!")