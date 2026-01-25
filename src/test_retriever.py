from retriever import University_Retrieve

# Khởi tạo
retriever = University_Retrieve()

print("="*70)
print("🧪 TESTING STRUCTURED DATA FUNCTIONS")
print("="*70)

# Test 1: Điểm chuẩn
print("\n 1 TEST: Điểm chuẩn Trí Tuệ Nhân tạo năm 2024")
print("-"*70)
result = retriever._get_structured_scores("điểm chuẩn Trí Tuệ Nhân tạo năm 2024")
if result:
    print(f"✅ Found {result['total']} scores")
    print(f"Query info: {result['query_info']}")
    if result['scores']:
        first = result['scores'][0]
        print(f"First result: {first['major_name']} - {first['year']} - {first['cutoff_score']}")
else:
    print("❌ No scores found")

# Test 2: Học phí
print("\n 2  TEST: Học phí CNTT")
print("-"*70)
result = retriever._get_structured_tuitions("học phí ngành luật")
if result:
    print(f"✅ University: {result['university']}")
    print(f"✅ Groups found: {len(result['tuition_groups'])}")
    if result['tuition_groups']:
        first = result['tuition_groups'][0]
        print(f"First group: {first['group_name']} - {first['estimated_per_year']}")
else:
    print("❌ No tuition found")

# Test 3: Tổ hợp môn
print("\n3️⃣  TEST: Tổ hợp A00")
print("-"*70)
result = retriever._get_structured_combinations("tổ hợp A00")
if result:
    print(f"✅ Total combinations: {result['total']}")
    print(f"✅ Filtered: {len(result['combinations'])}")
    if result['combinations']:
        first = result['combinations'][0]
        print(f"A00: {', '.join(first['subjects'])}")
else:
    print("❌ No combinations found")

print("\n" + "="*70)
print("✅ Test completed!")

