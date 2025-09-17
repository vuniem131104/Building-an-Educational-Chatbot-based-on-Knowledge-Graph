# LLM as Judge Quiz Evaluation Domain

Domain này cung cấp chức năng đánh giá chất lượng quiz được sinh tự động bằng cách sử dụng LLM (Large Language Model) như một "thẩm phán" chuyên nghiệp.

## Tổng quan

### Mục đích
- Đánh giá chất lượng các câu hỏi quiz được tạo tự động
- So sánh quiz với nội dung bài giảng gốc
- Cung cấp feedback chi tiết và điểm số
- Đề xuất cải thiện cho các câu hỏi

### Kiến trúc
```
llm_as_judge/
├── __init__.py           # Module exports
├── models.py             # Data models và schemas
├── prompts.py            # System và user prompts cho LLM
├── service.py            # Core evaluation service
└── README.md             # Tài liệu này
```

## Các tính năng chính

### 1. Tiêu chí đánh giá (Evaluation Criteria)

Domain sử dụng 6 tiêu chí đánh giá chính:

1. **Content Alignment (25%)** - Mức độ phù hợp với nội dung bài giảng
2. **Learning Objectives Coverage (20%)** - Độ bao phủ mục tiêu học tập
3. **Question Quality (20%)** - Chất lượng cấu trúc câu hỏi
4. **Difficulty Appropriateness (15%)** - Mức độ khó phù hợp
5. **Pedagogical Soundness (10%)** - Tính hợp lý về mặt giáo dục
6. **Language Clarity (10%)** - Độ rõ ràng ngôn ngữ

### 2. Các loại đánh giá

#### Basic Evaluation
- Đánh giá tổng quan quiz
- Điểm số tổng thể (0-100)
- Phân loại (Excellent/Good/Satisfactory/Needs Improvement/Poor)
- Khuyến nghị (Accept/Revise/Reject)

#### Comprehensive Evaluation
- Đánh giá chi tiết từng câu hỏi
- Phân tích độ bao phủ nội dung
- Thống kê phân bố độ khó và Bloom's taxonomy
- Xác định khoảng trống và nội dung dư thừa

## Data Models

### QuizEvaluationInput
```python
class QuizEvaluationInput(BaseModel):
    quiz_questions: List[QuizQuestion]  # Danh sách câu hỏi cần đánh giá
    lecture_content: str                # Nội dung bài giảng gốc
    course_code: str                    # Mã môn học
    week_number: int                    # Tuần học
    evaluation_criteria: List[EvaluationCriteria]  # Tiêu chí đánh giá
```

### QuizEvaluationOutput
```python
class QuizEvaluationOutput(BaseModel):
    total_score: int                    # Điểm tổng (0-100)
    grade: str                          # Phân loại chất lượng
    criteria_scores: List[CriteriaScore] # Điểm từng tiêu chí
    overall_feedback: str               # Feedback tổng quan
    major_strengths: List[str]          # Điểm mạnh chính
    major_weaknesses: List[str]         # Điểm yếu chính
    priority_improvements: List[str]    # Cải thiện ưu tiên
    recommendation: str                 # Khuyến nghị (Accept/Revise/Reject)
```

## Cách sử dụng

### 1. Setup cơ bản

```python
from generation.domain.llm_as_judge import (
    QuizEvaluatorService,
    QuizEvaluationInput,
    QuizEvaluationOutput
)
from lite_llm import LiteLLMService, LiteLLMSetting

# Setup LLM service
litellm_setting = LiteLLMSetting(
    base_url="https://api.openai.com/v1",
    api_key="your-api-key",
    model="gpt-4o-mini"
)
litellm_service = LiteLLMService(litellm_setting)

# Create evaluator service
evaluator_service = QuizEvaluatorService(litellm_service)
```

### 2. Đánh giá cơ bản

```python
async def evaluate_quiz():
    # Prepare input
    evaluation_input = QuizEvaluationInput(
        quiz_questions=your_quiz_questions,
        lecture_content=your_lecture_content,
        course_code="INT3405",
        week_number=6
    )
    
    # Perform evaluation
    result = await evaluator_service.evaluate_quiz(evaluation_input)
    
    print(f"Score: {result.total_score}/100")
    print(f"Grade: {result.grade}")
    print(f"Recommendation: {result.recommendation}")
```

### 3. Đánh giá toàn diện

```python
async def comprehensive_evaluate():
    comprehensive_result = await evaluator_service.evaluate_quiz_comprehensive(evaluation_input)
    
    print(f"Content Coverage: {comprehensive_result.metrics.content_coverage_percentage}%")
    print(f"Difficulty Distribution: {comprehensive_result.metrics.question_difficulty_distribution}")
    
    # Individual question evaluations
    for q_eval in comprehensive_result.question_evaluations:
        print(f"Question: {q_eval.question_text}")
        print(f"Content Alignment: {q_eval.content_alignment_score}/10")
```

## Configuration

### QuizEvaluatorSetting

```python
class QuizEvaluatorSetting(BaseModel):
    model: str = "gpt-4o-mini"              # LLM model
    temperature: float = 0.1                # Creativity level (low for consistency)
    max_completion_tokens: int = 4000       # Response length limit
    
    # Score thresholds
    acceptance_threshold: int = 80          # Accept if score >= 80
    revision_threshold: int = 60            # Revise if 60 <= score < 80
    
    # Evaluation modes
    enable_detailed_analysis: bool = True
    enable_individual_question_evaluation: bool = True
    enable_content_coverage_analysis: bool = True
```

## Testing

Sử dụng file test có sẵn:

```bash
# Chạy test với dữ liệu mẫu
cd /home/vuiem/KLTN
python test_llm_as_judge.py
```

Test file bao gồm:
- Test đánh giá quiz chất lượng tốt
- Test đánh giá toàn diện
- Test phát hiện quiz chất lượng kém
- Lưu kết quả ra file JSON

## Kết quả mẫu

### Điểm số
- 90-100: Excellent (Accept)
- 80-89: Good (Accept)
- 70-79: Satisfactory (Accept/Revise)
- 60-69: Needs Improvement (Revise)
- <60: Poor (Reject)

### Feedback mẫu
```json
{
  "total_score": 85,
  "grade": "Good",
  "recommendation": "Accept",
  "criteria_scores": [
    {
      "criteria": "content_alignment",
      "score": 90,
      "feedback": "Câu hỏi phù hợp tốt với nội dung bài giảng...",
      "strengths": ["Accurate content", "Clear connections"],
      "suggestions": ["Add more advanced questions"]
    }
  ]
}
```

## Best Practices

### 1. Chuẩn bị dữ liệu
- Cung cấp nội dung bài giảng đầy đủ và chính xác
- Đảm bảo câu hỏi có đủ metadata (difficulty, bloom level, etc.)
- Giới hạn độ dài nội dung để tránh vượt quá context limit

### 2. Cấu hình đánh giá
- Sử dụng temperature thấp (0.1) để đảm bảo tính nhất quán
- Điều chỉnh trọng số tiêu chí theo nhu cầu cụ thể
- Enable detailed analysis cho đánh giá sâu

### 3. Xử lý kết quả
- Sử dụng score thresholds để tự động phân loại
- Lưu feedback chi tiết để cải thiện hệ thống
- Tích hợp với feedback loop để tự động cải thiện

## Limitations

1. **API Cost**: Mỗi lần đánh giá consume LLM tokens
2. **Language**: Tối ưu cho tiếng Việt, có thể cần điều chỉnh cho ngôn ngữ khác
3. **Context Length**: Giới hạn bởi context window của LLM
4. **Subjectivity**: Đánh giá có thể có yếu tố chủ quan từ LLM

## Future Enhancements

1. **Fine-tuning**: Train model riêng cho domain giáo dục Việt Nam
2. **Multi-modal**: Hỗ trợ đánh giá câu hỏi có hình ảnh, công thức
3. **Comparative Analysis**: So sánh với quiz từ các tuần khác
4. **Student Performance**: Tích hợp dữ liệu thực tế từ học sinh
5. **Automated Improvement**: Tự động suggest câu hỏi thay thế