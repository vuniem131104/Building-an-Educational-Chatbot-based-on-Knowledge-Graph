"""
Test file for LLM as Judge Quiz Evaluation Domain

This file tests the quiz evaluation functionality using sample quiz data
from the existing quiz generation output files.
"""

import asyncio
import json
from pathlib import Path
from typing import List

from generation.domain.llm_as_judge import (
    QuizEvaluatorService,
    QuizEvaluationInput,
    QuizEvaluationOutput,
    ComprehensiveQuizEvaluationOutput,
    EvaluationCriteria
)
from generation.shared.models import QuizQuestion, Topic
from generation.shared.settings import QuizEvaluatorSetting
from lite_llm import LiteLLMService, LiteLLMSetting


# Sample quiz data based on the quiz generation output
SAMPLE_QUIZ_QUESTIONS = [
    {
        "question": "Mô hình Perceptron được sử dụng chủ yếu để giải quyết loại bài toán nào?",
        "answer": "Phân loại nhị phân cho dữ liệu tách tuyến tính",
        "distractors": [
            "Tất cả các loại dữ liệu",
            "Chỉ các bài toán hồi quy tuyến tính",
            "Phân loại đa lớp cho dữ liệu phi tuyến"
        ],
        "difficulty": "Easy",
        "bloom_taxonomy_level": "Remember",
        "estimated_right_answer_rate": 0.85,
        "explanation": "Perceptron là một mô hình phân loại tuyến tính chỉ có thể giải quyết các bài toán phân loại nhị phân với dữ liệu tách tuyến tính.",
        "topic": {
            "name": "Perceptron Model Fundamentals",
            "description": "This topic covers the basic definition of the Perceptron model, its use in linear classification, and the concept of defining a separating hyperplane."
        }
    },
    {
        "question": "Mục tiêu chính của Hard Margin SVM là gì?",
        "answer": "Tìm hyperplane tách với margin tối đa cho dữ liệu tách tuyến tính hoàn hảo",
        "distractors": [
            "Giảm thiểu số lượng support vectors",
            "Tối ưu hóa tham số regularization C",
            "Xử lý dữ liệu nhiễu và overlap"
        ],
        "difficulty": "Easy", 
        "bloom_taxonomy_level": "Understand",
        "estimated_right_answer_rate": 0.80,
        "explanation": "Hard Margin SVM tìm hyperplane phân tách tối ưu bằng cách tối đa hóa margin giữa các lớp, yêu cầu dữ liệu phải tách tuyến tính hoàn hảo.",
        "topic": {
            "name": "Hard Margin SVM Objective",
            "description": "This topic focuses on the core objective of Hard Margin SVM and its strict requirement for linearly separable datasets."
        }
    },
    {
        "question": "Slack variables (ξᵢ) trong Soft Margin SVM có mục đích chính là gì?",
        "answer": "Cho phép một số điểm bị phân loại sai trong tập huấn luyện",
        "distractors": [
            "Tăng tốc độ tính toán của thuật toán",
            "Giảm số chiều của không gian đặc trưng",
            "Cải thiện độ chính xác trên tập kiểm tra"
        ],
        "difficulty": "Easy",
        "bloom_taxonomy_level": "Remember", 
        "estimated_right_answer_rate": 0.75,
        "explanation": "Slack variables cho phép SVM dung thứ với các điểm nằm trong margin hoặc bị phân loại sai, làm cho mô hình có thể xử lý dữ liệu không tách tuyến tính hoàn hảo.",
        "topic": {
            "name": "Soft Margin SVM Slack Variables",
            "description": "This topic assesses understanding of slack variables in Soft Margin SVM and their role in allowing misclassifications."
        }
    }
]

SAMPLE_LECTURE_CONTENT = """
# Lecture 6: Support Vector Machines and Perceptron

## 1. Perceptron Model
- Perceptron là một mô hình phân loại tuyến tính đơn giản
- Sử dụng để phân loại nhị phân với dữ liệu tách tuyến tính
- Định nghĩa hyperplane phân tách: w^T x + b = 0
- Chỉ có thể xử lý dữ liệu tách tuyến tính hoàn hảo

## 2. Hard Margin SVM
- Mục tiêu: Tìm hyperplane tách với margin tối đa
- Yêu cầu dữ liệu phải tách tuyến tính hoàn hảo
- Không có điểm nào được phép nằm trong margin
- Tối ưu hóa: min ||w||² subject to yᵢ(w^T xᵢ + b) ≥ 1

## 3. Soft Margin SVM  
- Giải quyết vấn đề của Hard Margin khi dữ liệu không tách tuyến tính hoàn hảo
- Sử dụng slack variables ξᵢ để cho phép một số điểm bị phân loại sai
- Cân bằng giữa tối đa hóa margin và giảm thiểu lỗi phân loại
- Tham số C điều khiển mức độ penalty cho việc vi phạm margin

## 4. Kernel Trick
- Ánh xạ dữ liệu vào không gian đặc trưng có chiều cao hơn
- Cho phép SVM xử lý dữ liệu không tách tuyến tính
- Các kernel phổ biến: Linear, Polynomial, RBF (Gaussian)
- Không cần tính toán trực tiếp trong không gian đặc trưng

## 5. Multi-class Classification
- SVM ban đầu chỉ cho phân loại nhị phân
- One-vs-Rest: k classifiers cho k classes  
- One-vs-One: k(k-1)/2 classifiers cho k classes
- Prediction dựa trên voting hoặc decision function values
"""


def create_quiz_questions_from_sample() -> List[QuizQuestion]:
    """Convert sample data to QuizQuestion objects"""
    quiz_questions = []
    
    for idx, sample in enumerate(SAMPLE_QUIZ_QUESTIONS):
        # Create Topic object
        topic = Topic(
            name=sample["topic"]["name"],
            description=sample["topic"]["description"], 
            difficulty=sample["difficulty"],
            bloom_taxonomy_level=sample["bloom_taxonomy_level"],
            estimated_right_answer_rate=sample["estimated_right_answer_rate"]
        )
        
        # Create QuizQuestion object
        quiz_question = QuizQuestion(
            question=sample["question"],
            answer=sample["answer"], 
            distractors=sample["distractors"],
            explanation=sample["explanation"],
            topic=topic,
            week_number=6,
            course_code="int3405"
        )
        
        quiz_questions.append(quiz_question)
    
    return quiz_questions


async def test_basic_quiz_evaluation():
    """Test basic quiz evaluation functionality"""
    print("🧪 Testing Basic Quiz Evaluation...")
    
    # Setup LiteLLM service
    litellm_setting = LiteLLMSetting(
        base_url="https://api.openai.com/v1",
        api_key="your-api-key-here",  # Replace with actual API key
        model="gpt-4o-mini"
    )
    litellm_service = LiteLLMService(litellm_setting)
    
    # Setup evaluator service
    evaluator_setting = QuizEvaluatorSetting()
    evaluator_service = QuizEvaluatorService(litellm_service)
    
    # Create quiz questions
    quiz_questions = create_quiz_questions_from_sample()
    
    # Create evaluation input
    evaluation_input = QuizEvaluationInput(
        quiz_questions=quiz_questions,
        lecture_content=SAMPLE_LECTURE_CONTENT,
        course_code="int3405",
        week_number=6,
        evaluation_criteria=list(EvaluationCriteria)
    )
    
    try:
        # Perform evaluation
        print("📊 Evaluating quiz questions...")
        evaluation_result = await evaluator_service.evaluate_quiz(evaluation_input)
        
        # Display results
        print(f"\n✅ Evaluation Complete!")
        print(f"📈 Total Score: {evaluation_result.total_score}/100")
        print(f"🎯 Grade: {evaluation_result.grade}")
        print(f"💡 Recommendation: {evaluation_result.recommendation}")
        
        print(f"\n📋 Criteria Breakdown:")
        for criteria_score in evaluation_result.criteria_scores:
            print(f"  • {criteria_score.criteria.value}: {criteria_score.score}/{criteria_score.max_score}")
        
        print(f"\n💬 Overall Feedback:")
        print(f"  {evaluation_result.overall_feedback[:200]}...")
        
        if evaluation_result.major_strengths:
            print(f"\n✨ Major Strengths:")
            for strength in evaluation_result.major_strengths[:3]:
                print(f"  • {strength}")
        
        if evaluation_result.major_weaknesses:
            print(f"\n⚠️  Major Weaknesses:")
            for weakness in evaluation_result.major_weaknesses[:3]:
                print(f"  • {weakness}")
        
        return evaluation_result
        
    except Exception as e:
        print(f"❌ Error during evaluation: {str(e)}")
        return None


async def test_comprehensive_quiz_evaluation():
    """Test comprehensive quiz evaluation with detailed analysis"""
    print("\n🔬 Testing Comprehensive Quiz Evaluation...")
    
    # Setup services (reuse from basic test)
    litellm_setting = LiteLLMSetting(
        base_url="https://api.openai.com/v1", 
        api_key="your-api-key-here",  # Replace with actual API key
        model="gpt-4o-mini"
    )
    litellm_service = LiteLLMService(litellm_setting)
    evaluator_service = QuizEvaluatorService(litellm_service)
    
    # Create evaluation input
    quiz_questions = create_quiz_questions_from_sample()
    evaluation_input = QuizEvaluationInput(
        quiz_questions=quiz_questions,
        lecture_content=SAMPLE_LECTURE_CONTENT,
        course_code="int3405", 
        week_number=6
    )
    
    try:
        # Perform comprehensive evaluation
        print("🔍 Running comprehensive analysis...")
        comprehensive_result = await evaluator_service.evaluate_quiz_comprehensive(evaluation_input)
        
        # Display comprehensive results
        print(f"\n✅ Comprehensive Evaluation Complete!")
        print(f"📊 Content Coverage: {comprehensive_result.metrics.content_coverage_percentage:.1f}%")
        print(f"📚 Questions Evaluated: {comprehensive_result.metrics.total_questions_evaluated}")
        print(f"🎯 Avg Estimated Accuracy: {comprehensive_result.metrics.average_estimated_accuracy:.2f}")
        
        print(f"\n📈 Difficulty Distribution:")
        for difficulty, count in comprehensive_result.metrics.question_difficulty_distribution.items():
            print(f"  • {difficulty}: {count} questions")
        
        print(f"\n🧠 Bloom's Taxonomy Distribution:")
        for bloom_level, count in comprehensive_result.metrics.bloom_taxonomy_distribution.items():
            print(f"  • {bloom_level}: {count} questions")
        
        if comprehensive_result.content_gaps:
            print(f"\n🔍 Content Gaps Identified:")
            for gap in comprehensive_result.content_gaps[:3]:
                print(f"  • {gap}")
        
        print(f"\n📝 Individual Question Evaluations:")
        for i, q_eval in enumerate(comprehensive_result.question_evaluations[:2]):
            print(f"  Question {i+1}:")
            print(f"    Content Alignment: {q_eval.content_alignment_score}/10")
            print(f"    Difficulty: {q_eval.difficulty_appropriateness_score}/10")
            print(f"    Clarity: {q_eval.clarity_score}/10")
            print(f"    Pedagogical Value: {q_eval.pedagogical_value_score}/10")
        
        return comprehensive_result
        
    except Exception as e:
        print(f"❌ Error during comprehensive evaluation: {str(e)}")
        return None


async def test_evaluation_with_poor_quiz():
    """Test evaluation with a deliberately poor-quality quiz to test detection"""
    print("\n🚨 Testing Evaluation with Poor Quality Quiz...")
    
    # Create poor quality quiz questions
    poor_quiz_questions = [
        QuizQuestion(
            question="What is AI?",  # Too vague and not from lecture content
            answer="Artificial Intelligence",  # Not from lecture
            distractors=["Machine Learning", "Deep Learning", "Computer Vision"],
            explanation="AI is artificial intelligence.",  # Poor explanation
            topic=Topic(
                name="AI Basics",  # Not from lecture content
                description="Basic AI concepts",
                difficulty="Easy",
                bloom_taxonomy_level="Remember", 
                estimated_right_answer_rate=0.9
            ),
            week_number=6,
            course_code="int3405"
        )
    ]
    
    # Setup services
    litellm_setting = LiteLLMSetting(
        base_url="https://api.openai.com/v1",
        api_key="your-api-key-here",  # Replace with actual API key
        model="gpt-4o-mini"
    )
    litellm_service = LiteLLMService(litellm_setting)
    evaluator_service = QuizEvaluatorService(litellm_service)
    
    # Create evaluation input
    evaluation_input = QuizEvaluationInput(
        quiz_questions=poor_quiz_questions,
        lecture_content=SAMPLE_LECTURE_CONTENT,
        course_code="int3405",
        week_number=6
    )
    
    try:
        # Perform evaluation
        print("🔍 Evaluating poor quality quiz...")
        evaluation_result = await evaluator_service.evaluate_quiz(evaluation_input)
        
        # Display results
        print(f"\n✅ Poor Quiz Evaluation Complete!")
        print(f"📉 Total Score: {evaluation_result.total_score}/100 (Should be low)")
        print(f"❌ Grade: {evaluation_result.grade} (Should be Poor/Needs Improvement)")
        print(f"🚫 Recommendation: {evaluation_result.recommendation} (Should be Reject/Revise)")
        
        print(f"\n⚠️  Expected Issues Detected:")
        for criteria_score in evaluation_result.criteria_scores:
            if criteria_score.score < 60:
                print(f"  • Low {criteria_score.criteria.value}: {criteria_score.score}/{criteria_score.max_score}")
        
        return evaluation_result
        
    except Exception as e:
        print(f"❌ Error during poor quiz evaluation: {str(e)}")
        return None


async def save_evaluation_results(evaluation_result: QuizEvaluationOutput, filename: str):
    """Save evaluation results to JSON file"""
    try:
        output_data = {
            "evaluation_summary": {
                "total_score": evaluation_result.total_score,
                "grade": evaluation_result.grade,
                "recommendation": evaluation_result.recommendation,
                "course_code": evaluation_result.course_code,
                "week_number": evaluation_result.week_number
            },
            "criteria_scores": [
                {
                    "criteria": score.criteria.value,
                    "score": score.score,
                    "max_score": score.max_score,
                    "feedback": score.feedback,
                    "strengths": score.strengths,
                    "weaknesses": score.weaknesses,
                    "suggestions": score.suggestions
                }
                for score in evaluation_result.criteria_scores
            ],
            "overall_feedback": evaluation_result.overall_feedback,
            "major_strengths": evaluation_result.major_strengths,
            "major_weaknesses": evaluation_result.major_weaknesses,
            "priority_improvements": evaluation_result.priority_improvements
        }
        
        # Save to file
        output_path = Path(__file__).parent / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Results saved to: {output_path}")
        
    except Exception as e:
        print(f"❌ Error saving results: {str(e)}")


async def main():
    """Main test function"""
    print("🚀 Starting LLM as Judge Quiz Evaluation Tests")
    print("=" * 60)
    
    # Test 1: Basic evaluation
    basic_result = await test_basic_quiz_evaluation()
    if basic_result:
        await save_evaluation_results(basic_result, "basic_evaluation_result.json")
    
    # Test 2: Comprehensive evaluation  
    comprehensive_result = await test_comprehensive_quiz_evaluation()
    if comprehensive_result:
        await save_evaluation_results(comprehensive_result, "comprehensive_evaluation_result.json")
    
    # Test 3: Poor quiz evaluation
    poor_result = await test_evaluation_with_poor_quiz()
    if poor_result:
        await save_evaluation_results(poor_result, "poor_quiz_evaluation_result.json")
    
    print("\n" + "=" * 60)
    print("🎉 All tests completed! Check the generated JSON files for detailed results.")


if __name__ == "__main__":
    # Note: To run this test, you need to:
    # 1. Install required dependencies (lite_llm, etc.)
    # 2. Set up your OpenAI API key in the LiteLLMSetting
    # 3. Run: python test_llm_as_judge.py
    
    print("⚠️  Before running:")
    print("1. Make sure to set your OpenAI API key in the LiteLLMSetting")
    print("2. Install required dependencies: pip install openai litellm")
    print("3. Run with: python test_llm_as_judge.py")
    print()
    
    # Uncomment the next line to run the tests
    # asyncio.run(main())