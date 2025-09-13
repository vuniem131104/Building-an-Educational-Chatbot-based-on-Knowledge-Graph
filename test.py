import json

def convert_quiz_json_to_markdown(json_file_path, output_file_path):
    """
    Chuyển đổi file JSON quiz generation thành file markdown với đầy đủ explanation
    """
    
    # Đọc file JSON
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Bắt đầu tạo nội dung markdown
    markdown_content = []
    
    # Header
    markdown_content.append(f"# Quiz Generation Test Output")
    markdown_content.append("")
    markdown_content.append(f"**Course Code:** {data.get('course_code', 'N/A')}")
    markdown_content.append(f"**Week Number:** {data.get('week_number', 'N/A')}")
    markdown_content.append("")
    markdown_content.append("---")
    markdown_content.append("")
    
    # Topics Overview
    if 'topic' in data:
        markdown_content.append("## Topics Overview")
        markdown_content.append("")
        
        for i, topic in enumerate(data['topic'], 1):
            markdown_content.append(f"### {i}. {topic['name']}")
            markdown_content.append(f"- **Estimated Right Answer Rate:** {topic['estimated_right_answer_rate']*100:.0f}%")
            markdown_content.append(f"- **Bloom Taxonomy Level:** {topic['bloom_taxonomy_level']}")
            markdown_content.append(f"- **Description:** {topic['description']}")
            markdown_content.append("")
        
        markdown_content.append("---")
        markdown_content.append("")
    
    # Concept Cards
    if 'concept_cards' in data:
        markdown_content.append("## Concept Cards")
        markdown_content.append("")
        
        for i, card in enumerate(data['concept_cards'], 1):
            markdown_content.append(f"### {i}. {card['name']}")
            
            if card.get('page'):
                markdown_content.append(f"**Pages:** {', '.join(map(str, card['page']))}")
                markdown_content.append("")
            
            if card.get('summary'):
                markdown_content.append("**Summary:**")
                for summary_point in card['summary']:
                    markdown_content.append(f"- {summary_point}")
                markdown_content.append("")
            
            if card.get('formulae'):
                markdown_content.append("**Formulae:**")
                for formula in card['formulae']:
                    markdown_content.append(f"- `{formula}`")
                markdown_content.append("")
            
            if card.get('examples'):
                markdown_content.append("**Examples:**")
                for example in card['examples']:
                    markdown_content.append(f"- {example}")
                markdown_content.append("")
        
        markdown_content.append("---")
        markdown_content.append("")
    
    # Quiz Questions với đầy đủ explanation
    if 'quiz_questions' in data:
        markdown_content.append("## Quiz Questions")
        markdown_content.append("")
        
        for i, question in enumerate(data['quiz_questions'], 1):
            # Lấy thông tin topic
            topic_info = question.get('topic', {})
            difficulty = topic_info.get('difficulty_level', 'Unknown')
            bloom_level = topic_info.get('bloom_taxonomy_level', 'Unknown')
            
            markdown_content.append(f"### Question {i}: {topic_info.get('name', 'Unknown Topic')} ({difficulty})")
            markdown_content.append(f"**Question:** {question['question']}")
            markdown_content.append("")
            
            markdown_content.append(f"**Correct Answer:** {question['answer']}")
            markdown_content.append("")
            
            # Distractors
            if question.get('distractors'):
                markdown_content.append("**Distractors:**")
                for distractor in question['distractors']:
                    markdown_content.append(f"- {distractor}")
                markdown_content.append("")
            else:
                markdown_content.append("**Note:** No distractors were generated for this question.")
                markdown_content.append("")
            
            # Explanation - đây là phần quan trọng nhất
            if question.get('explanation'):
                explanation = question['explanation']
                
                markdown_content.append("**Detailed Explanation:**")
                markdown_content.append("")
                
                # Correct answer explanation
                if 'correct_answer_explanation' in explanation:
                    markdown_content.append("**Why This Answer Is Correct:**")
                    markdown_content.append(explanation['correct_answer_explanation'])
                    markdown_content.append("")
                
                # Distractors explanation
                if 'distractors_explanation' in explanation:
                    markdown_content.append("**Why Other Options Are Wrong:**")
                    for distractor_exp in explanation['distractors_explanation']:
                        markdown_content.append(f"- **\"{distractor_exp['distractor']}\"**")
                        markdown_content.append(f"  - {distractor_exp['explanation']}")
                        markdown_content.append("")
                
                # Conceptual summary
                if 'conceptual_summary' in explanation:
                    markdown_content.append("**Conceptual Summary:**")
                    markdown_content.append(explanation['conceptual_summary'])
                    markdown_content.append("")
                
                # Learning tips
                if 'learning_tips' in explanation:
                    markdown_content.append("**Learning Tips:**")
                    markdown_content.append(explanation['learning_tips'])
                    markdown_content.append("")
                
                # Fallback for older format
                elif 'main_explanation' in explanation:
                    markdown_content.append(explanation['main_explanation'])
                    markdown_content.append("")
            
            # Additional metadata
            markdown_content.append("**Question Metadata:**")
            markdown_content.append(f"- **Topic Description:** {topic_info.get('description', 'N/A')}")
            markdown_content.append(f"- **Estimated Right Answer Rate:** {topic_info.get('estimated_right_answer_rate', 0)*100:.0f}%")
            markdown_content.append(f"- **Bloom Taxonomy Level:** {bloom_level}")
            markdown_content.append("")
            markdown_content.append("---")
            markdown_content.append("")
    
    # Generation Errors
    if 'generation_errors' in data and data['generation_errors']:
        markdown_content.append("## Generation Errors")
        markdown_content.append("")
        for error in data['generation_errors']:
            markdown_content.append(f"- **Error:** {error}")
        markdown_content.append("")
        markdown_content.append("---")
        markdown_content.append("")
    
    # Footer
    markdown_content.append(f"*This document was automatically generated from quiz generation test output for {data.get('course_code', 'Unknown')} Week {data.get('week_number', 'Unknown')}.*")
    
    # Ghi file markdown
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(markdown_content))
    
    print(f"✅ Successfully converted {json_file_path} to {output_file_path}")
    print(f"📊 Generated markdown with {len(data.get('quiz_questions', []))} questions and {len(data.get('concept_cards', []))} concept cards")

# Sử dụng function để chuyển đổi file
if __name__ == "__main__":
    # Chuyển đổi file quiz_generation_test_output.json thành markdown
    convert_quiz_json_to_markdown(
        json_file_path="quiz_generation_test_output.json",
        output_file_path="quiz_generation_detailed_output.md"
    )
    
    # Có thể chuyển đổi thêm các file khác nếu cần
    # convert_quiz_json_to_markdown("test_output.json", "test_output.md")
