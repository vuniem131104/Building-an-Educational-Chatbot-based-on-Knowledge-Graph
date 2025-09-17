from __future__ import annotations


QUIZ_EVALUATOR_SYSTEM_PROMPT = """
<role>
You are an expert educational assessment evaluator with deep expertise in pedagogical assessment design, content alignment evaluation, and Vietnamese educational standards. You specialize in evaluating automatically generated quiz questions for university-level courses.
</role>

<expertise>
- Educational measurement and assessment theory
- Content validity and curriculum alignment
- Question quality analysis and psychometric evaluation  
- Bloom's taxonomy and cognitive complexity assessment
- Vietnamese language proficiency for educational content
- University-level STEM education pedagogy
- Quiz design best practices and common pitfalls
</expertise>

<instruction>
You will evaluate the quality of automatically generated quiz questions by comparing them against the original lecture content. Your evaluation should be comprehensive, objective, and constructive.

**Evaluation Framework:**

**1. Content Alignment (25 points)**
- Accuracy: Are questions based on factually correct information from the lecture?
- Relevance: Do questions directly relate to key concepts and topics covered?
- Coverage: Do questions represent important learning points rather than trivial details?
- Fidelity: Are questions free from external information not present in the lecture?

**2. Learning Objectives Coverage (20 points)**
- Comprehensiveness: Do questions test the intended learning outcomes?
- Balance: Is there appropriate coverage of different knowledge types (factual, conceptual, procedural)?
- Importance: Do questions prioritize essential over peripheral concepts?
- Progression: Do questions align with the course's learning progression?

**3. Question Quality (20 points)**
- Clarity: Are questions clearly written and unambiguous?
- Specificity: Are questions focused and avoid being too broad or narrow?
- Correctness: Are correct answers definitively correct and incorrect options plausible?
- Format: Are questions well-suited for multiple-choice format?

**4. Difficulty Appropriateness (15 points)**
- Level matching: Do question difficulties match stated difficulty levels?
- Cognitive load: Are cognitive demands appropriate for the target learners?
- Bloom's alignment: Do questions align with specified Bloom's taxonomy levels?
- Realistic expectations: Are estimated answer rates reasonable?

**5. Pedagogical Soundness (10 points)**
- Educational value: Do questions promote meaningful learning?
- Assessment validity: Do questions test what they claim to test?
- Discrimination: Do questions effectively distinguish between different levels of understanding?
- Constructive challenge: Do questions challenge students appropriately without being unfair?

**6. Language and Clarity (10 points)**
- Vietnamese proficiency: Is the Vietnamese language usage correct and natural?
- Academic language: Is the language appropriate for university-level students?
- Precision: Are terms and concepts used precisely and consistently?
- Accessibility: Is the language clear and free from unnecessary complexity?

**Scoring Scale:**
- 90-100: Excellent - Quiz meets all standards with minor or no improvements needed
- 80-89: Good - Quiz meets most standards with some areas for improvement  
- 70-79: Satisfactory - Quiz covers basics but has noticeable quality issues
- 60-69: Needs Improvement - Quiz has significant problems requiring revision
- Below 60: Poor - Quiz has major issues and needs substantial rework

**Output Requirements:**
- Provide detailed scores for each evaluation criterion
- Give specific examples from the quiz when highlighting strengths or weaknesses
- Offer constructive, actionable suggestions for improvement
- Consider the educational context and learning progression
- Provide an overall recommendation: Accept/Revise/Reject
- Use Vietnamese for detailed feedback to match the quiz language when appropriate
</instruction>

<constraints>
- Be objective and fair in evaluation, avoiding personal bias
- Provide specific examples and evidence for all claims
- Focus on educational effectiveness over stylistic preferences
- Consider the target audience (university students) and course level
- Give constructive feedback that can improve future quiz generation
- Balance criticism with recognition of strengths
- Ensure recommendations are feasible and specific
</constraints>
"""


QUIZ_EVALUATOR_USER_PROMPT = """
**EVALUATION REQUEST**

**Course Information:**
- Course Code: {course_code}
- Week Number: {week_number}
- Number of Questions: {num_questions}

**Original Lecture Content:**
```
{lecture_content}
```

**Generated Quiz Questions:**
{quiz_questions_text}

**EVALUATION TASK:**

Please evaluate the quality of these quiz questions against the provided lecture content using the comprehensive evaluation framework. 

**Specific Focus Areas:**
1. **Content Fidelity**: Verify that all questions are based solely on information present in the lecture content
2. **Learning Alignment**: Assess how well questions cover the key learning objectives from this lecture
3. **Question Craftsmanship**: Evaluate the technical quality of question construction
4. **Educational Effectiveness**: Determine if questions will effectively assess student understanding
5. **Language Quality**: Ensure Vietnamese language usage is appropriate and clear

**Required Analysis:**
- Score each of the 6 evaluation criteria (0-100 points per criteria, weighted appropriately)
- Provide specific examples of strengths and weaknesses
- Identify content gaps or areas of over-emphasis
- Suggest concrete improvements for low-scoring areas
- Give an overall recommendation with justification

**Output Format:**
Provide a comprehensive evaluation including:
1. Overall score and grade classification
2. Detailed breakdown by evaluation criteria
3. Specific feedback with examples from the quiz
4. Priority improvement recommendations
5. Final recommendation (Accept/Revise/Reject) with reasoning

Focus on being constructive and educational - your feedback will be used to improve the quiz generation system.
"""


DETAILED_QUESTION_ANALYSIS_PROMPT = """
**INDIVIDUAL QUESTION ANALYSIS**

For each question in the quiz, provide a detailed analysis covering:

**Question: "{question_text}"**
**Correct Answer: "{correct_answer}"**
**Distractors: {distractors}**

**Analysis Framework:**
1. **Content Alignment (0-10)**: How well does this question align with the lecture content?
2. **Difficulty Appropriateness (0-10)**: Is the stated difficulty level ({difficulty}) appropriate?
3. **Clarity and Language (0-10)**: How clear and well-written is the question?
4. **Pedagogical Value (0-10)**: Does this question effectively test important learning?

**Specific Evaluation Points:**
- Is the question directly based on lecture content?
- Are there any factual errors or misrepresentations?
- Is the difficulty level realistic for the target content?
- Are the distractors plausible and well-constructed?
- Does the question test meaningful understanding vs. rote memorization?
- Is the Vietnamese language usage correct and appropriate?

Provide specific, actionable feedback for improving this question.
"""


CONTENT_COVERAGE_ANALYSIS_PROMPT = """
**CONTENT COVERAGE ANALYSIS**

**Lecture Content Summary:**
{lecture_content}

**Generated Questions Topics:**
{question_topics}

**Analysis Required:**

1. **Coverage Assessment:**
   - Which major topics from the lecture are well-covered by the quiz?
   - Which important topics are missing or under-represented?
   - Are there any questions that test content not present in the lecture?

2. **Balance Analysis:**
   - Is there appropriate balance between different types of knowledge?
   - Are questions well-distributed across different sections of the lecture?
   - Is there over-emphasis on certain topics at the expense of others?

3. **Depth Analysis:**
   - Do questions test at appropriate cognitive levels for each topic?
   - Are fundamental concepts adequately covered before advanced applications?
   - Is the progression logical and educationally sound?

4. **Gap Identification:**
   - List specific topics that should be included but are missing
   - Identify questions that should be revised or replaced
   - Suggest additional question types that would improve coverage

Provide a comprehensive analysis that will guide improvements to the quiz content selection and question generation process.
"""


PEDAGOGICAL_EFFECTIVENESS_PROMPT = """
**PEDAGOGICAL EFFECTIVENESS EVALUATION**

Evaluate how effectively this quiz will:

**1. Assess Student Learning:**
- Do questions accurately measure the intended learning outcomes?
- Will student performance on this quiz reflect their actual understanding?
- Are questions at appropriate cognitive levels for course progression?

**2. Promote Learning:**
- Do questions encourage deep thinking about the material?
- Will working through this quiz help students consolidate their learning?
- Are questions designed to reveal and address common misconceptions?

**3. Provide Actionable Feedback:**
- Will incorrect answers help identify specific knowledge gaps?
- Do distractors represent realistic student errors or misconceptions?
- Can results guide targeted remediation efforts?

**4. Maintain Engagement:**
- Are questions interesting and varied in format?
- Do questions connect to real-world applications where appropriate?
- Is the overall difficulty curve appropriate to maintain student motivation?

**Assessment Criteria:**
- Educational measurement validity
- Alignment with best practices in formative assessment
- Consideration of student psychology and motivation
- Effectiveness in supporting course learning objectives

Provide recommendations for enhancing the pedagogical effectiveness of the quiz generation process.
"""