from lite_llm import LiteLLMSetting
from pydantic import HttpUrl
from lite_llm import LiteLLMService, LiteLLMInput, CompletionMessage, Role
import asyncio 
from base import BaseModel


litellm_service = LiteLLMService(
    litellm_setting=LiteLLMSetting(
        url=HttpUrl("http://localhost:9510"),
        token="abc123",
        model="gemini-2.5-flash",
        frequency_penalty=0.0,
        n=1,
        temperature=0.0,
        top_p=1.0,
        max_completion_tokens=10000,
        dimension=1536,
        embedding_model="gemini-embedding",
    )
)

system_prompt = """
You are an expert educational assessment designer. Your task is to create optimal question slots for an exam based on the blueprint requirements and lecture content.

Given:
1. An exam blueprint specifying the number and types of questions needed
2. Lecture topics organized by weeks

Create question slots that:
- Meet the exact blueprint requirements (number of each question type)
- Cover the most important topics from the lectures
- Distribute questions appropriately across different weeks/lectures
- Ensure balanced difficulty and comprehensive coverage

## Blueprint Analysis:
The blueprint specifies:
- Number of Multiple Choice Questions (mcq)
- Number of Short Answer questions (short_answer) 
- Number of Case Study questions (case_study)
- Exam type (mid_term, final, etc.)

## Slot Creation Rules:

1. **Question Type Distribution**: Create exactly the number of slots specified in blueprint
2. **Topic Coverage**: Prioritize fundamental concepts and important topics from lectures
3. **Week Distribution**: Spread questions across different weeks, focusing more on recent content for mid-term
4. **Difficulty Balance**: Mix easy, medium, and hard questions appropriately
5. **Topic Description**: Be specific about what the question should test

## For each slot, specify:
- **type**: Question format (mcq, short_answer, case_study)
- **target_weeks**: List of lecture weeks this slot should draw from (e.g., [1, 2])
- **difficulty**: Level (easy, medium, hard)
- **topic_description**: Specific topic/concept to be tested with enough detail for question generation

## Important Guidelines:
- For mid_term: Focus more on weeks 1-4, but include some from later weeks
- For final: Include all weeks with emphasis on integration across topics
- MCQ slots should test factual knowledge, definitions, and quick applications
- Short answer slots should test deeper understanding and explanations
- Case study slots should test analysis, application, and integration of multiple concepts
- Ensure no duplicate or overly similar slots

Create slots that would result in a comprehensive and fair assessment of student learning.
"""

class Slot(BaseModel):
    type: str 
    target_weeks: list[int] 
    difficulty: str 
    topic_description: str
    
class Slots(BaseModel):
    topics: list[Slot]
    

if __name__ == "__main__":
    lecture_1 = [
        "Các ví dụ tạo động lực",
        "Giới thiệu về Học máy",
        "Thống kê so với Học máy",
        "Học máy so với Học sâu",
        "Các ứng dụng của Học máy",
        "Các loại Học máy",
        "Học có giám sát",
        "Học không giám sát",
        "Học tăng cường"
    ]

    lecture_2 = [
        "Thống kê - Xác suất",
        "Phân phối dữ liệu điển hình",
        "Các phép đo điển hình",
        "Entropy, Cross Entropy",
        "Thông tin tương hỗ",
        "Độ phân kỳ Kullback-Leibler",
        "Lý thuyết học máy"
    ]

    lecture_3 = [
        "Học có giám sát",
        "Hồi quy tuyến tính với một biến",
        "Biểu diễn mô hình",
        "Hàm chi phí",
        "Giảm độ dốc",
        "Hồi quy tuyến tính với nhiều biến",
        "Tốc độ học",
        "Phương trình chuẩn"
    ]
    
    lecture_4 = [
        "Học máy Bayes",
        "Định lý Bayes",
        "Học MAP so với học MLE",
        "Mô hình sinh xác suất",
        "Bộ phân loại Bayes ngây thơ",
        "Mô hình phân biệt",
        "Hồi quy Logistic",
        "Cây quyết định",
        "K-Hàng xóm gần nhất"
    ]

    lecture_5 = [
        "Ví dụ về Cây Quyết định",
        "Thuật toán Cây Quyết định",
        "Các phương pháp biểu diễn điều kiện kiểm tra",
        "Các thước đo độ không thuần khiết của nút",
        "Chỉ số Gini",
        "Entropy",
        "Tỷ lệ tăng trưởng",
        "Lỗi phân loại"
    ]

    lecture_6 = [
        "Vấn đề và Trực giác: Perceptron",
        "Công thức của SVM tuyến tính",
        "SVM biên cứng",
        "SVM biên mềm",
        "Các vấn đề đối ngẫu/nguyên thủy",
        "SVM phi tuyến tính với Kernel",
        "Các thủ thuật Kernel",
        "Phân loại đa lớp"
    ]

    lecture_7 = [
        "Lỗi thực so với Lỗi thực nghiệm",
        "Quá khớp, Dưới khớp",
        "Đánh đổi Thiên vị-Phương sai",
        "Tối ưu hóa Mô hình",
        "Lựa chọn Đặc trưng",
        "Chuẩn hóa (Regularization)",
        "Tập hợp Mô hình"
    ]

    lecture_8 = [
        "Phân cụm - Các khái niệm chung",
        "Các ứng dụng trong đời sống thực",
        "Các loại phân cụm",
        "Các thuật toán phân cụm điển hình",
        "K-Means và các biến thể",
        "Phân cụm phân cấp (HAC)",
        "Phân cụm dựa trên mật độ (DBSCAN)"
    ]
    
    blueprint = {
        "mcq": 10,
        "short_answer": 5, 
        "case_study": 1,
        "type": "mid_term"
    }


    # Tạo input cho LLM dựa trên blueprint và lecture content
    lecture_content = f"""
LECTURE CONTENT BY WEEKS:

Week 1 - Introduction to Machine Learning:
{', '.join(lecture_1)}

Week 2 - General Concepts:
{', '.join(lecture_2)}

Week 3 - Linear Regression:
{', '.join(lecture_3)}

Week 4 - Classification Part 1:
{', '.join(lecture_4)}

Week 5 - Decision Trees:
{', '.join(lecture_5)}

Week 6 - Support Vector Machines:
{', '.join(lecture_6)}

Week 7 - Model Optimization:
{', '.join(lecture_7)}

Week 8 - Unsupervised Learning:
{', '.join(lecture_8)}
"""

    blueprint_text = f"""
EXAM BLUEPRINT:
- Type: {blueprint['type']}
- Multiple Choice Questions: {blueprint['mcq']}
- Short Answer Questions: {blueprint['short_answer']}
- Case Study Questions: {blueprint['case_study']}
Total Questions: {blueprint['mcq'] + blueprint['short_answer'] + blueprint['case_study']}
"""

    user_prompt = f"""
{blueprint_text}

{lecture_content}

Please create question slots that meet the blueprint requirements exactly. Generate {blueprint['mcq'] + blueprint['short_answer'] + blueprint['case_study']} slots total:
- {blueprint['mcq']} slots with type "mcq"
- {blueprint['short_answer']} slots with type "short_answer"  
- {blueprint['case_study']} slots with type "case_study"

Focus on the most important and testable concepts from the lectures.
"""

    output = asyncio.run(
        litellm_service.process_async(
            inputs=LiteLLMInput(
                model="gemini-2.5-flash",
                messages=[
                    CompletionMessage(
                        role=Role.SYSTEM,
                        content=system_prompt
                    ),
                    CompletionMessage(
                        role=Role.USER,
                        content=user_prompt
                    )
                ],
                response_format=Slots
            )
        )
    )

    print("Generated Slots:")
    print("=" * 50)
    for i, slot in enumerate(output.response.topics, 1):
        print(f"Slot {i}:")
        print(f"  Type: {slot.type}")
        print(f"  Target Weeks: {slot.target_weeks}")
        print(f"  Difficulty: {slot.difficulty}")
        print(f"  Topic: {slot.topic_description}")
        print("-" * 30)
    
    # Save to JSON file
    import json
    with open('generated_slots.json', 'w', encoding='utf-8') as f:
        json.dump(output.response.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"\nSummary:")
    print(f"Total slots generated: {len(output.response.topics)}")
    mcq_count = len([s for s in output.response.topics if s.type == 'mcq'])
    sa_count = len([s for s in output.response.topics if s.type == 'short_answer'])
    cs_count = len([s for s in output.response.topics if s.type == 'case_study'])
    print(f"MCQ: {mcq_count}, Short Answer: {sa_count}, Case Study: {cs_count}")
    print("Slots saved to 'generated_slots.json'")
