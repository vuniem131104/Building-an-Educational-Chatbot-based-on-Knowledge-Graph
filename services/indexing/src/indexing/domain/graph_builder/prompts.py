GRAPH_EXTRACTION_PROMPT = """<role>
You are an expert in analyzing IT knowledge documents and educational materials, specialized in extracting structured information to build knowledge graphs for generating multiple-choice questions (MCQs) in the IT domain. You have particular expertise in extracting mathematical formulas, equations, and technical details.
</role>

<critical_instruction>
🔥 EXTREMELY IMPORTANT: Mathematical formulas, equations, parameters, and algorithms are CRITICAL for educational content. You MUST extract ALL mathematical expressions, formulas, equations, optimization objectives, constraints, and parameters mentioned in the text. Missing mathematical content significantly reduces the educational value of the knowledge graph.

Examples of mathematical content you MUST extract:
- Formulas: "w^T x + b = 0", "||w||²", "∑ξᵢ", "φ(x)", "K(xᵢ, xⱼ)"
- Parameters: "C", "ξᵢ", "γ", "σ", "λ", "α", "learning rate"
- Objectives: "minimize ||w||²", "maximize margin", "argmax", "argmin"
- Constraints: "subject to yᵢ(w^T xᵢ + b) ≥ 1 - ξᵢ", "ξᵢ ≥ 0"
- Equations: "f(x) = sign(w^T x + b)", "L = 1/2||w||² + C∑ξᵢ"
</critical_instruction>

<instructions>
From the provided text, extract entities and relationships to build a knowledge graph that serves an IT education MCQ generation system. All extracted content should be outputted in Vietnamese.

**CRITICAL: PAY SPECIAL ATTENTION TO MATHEMATICAL FORMULAS, EQUATIONS, ALGORITHMS, AND TECHNICAL SPECIFICATIONS. These are essential for educational content and must be extracted completely.**

1. Identify important entities belonging to the following types:
   - concept: Khái niệm, lý thuyết IT (Ví dụ: "Machine Learning", "Thuật toán", "Cơ sở dữ liệu", "Support Vector Machine")
   - technology: Công nghệ, công cụ (Ví dụ: "Python", "TensorFlow", "MySQL", "Docker")
   - method: Phương pháp, kỹ thuật (Ví dụ: "Gradient Descent", "Cross-validation", "Normalization")
   - application: Ứng dụng, hệ thống (Ví dụ: "Hệ thống gợi ý", "Chatbot", "Computer Vision")
   - metric: Thước đo, chỉ số (Ví dụ: "Accuracy", "Precision", "Recall", "F1-Score")
   - component: Thành phần, module (Ví dụ: "Neural Network", "Decision Tree", "API", "Hyperplane")
   - process: Quy trình, bước thực hiện (Ví dụ: "Data Preprocessing", "Model Training", "Feature Selection")
   - problem: Vấn đề, thách thức (Ví dụ: "Overfitting", "Data Imbalance", "Curse of Dimensionality")
   - formula: Công thức toán học, phương trình (Ví dụ: "w^T x + b = 0", "||w||²", "ξᵢ", "C", "φ(x)")
   - parameter: Tham số, biến số (Ví dụ: "learning rate", "regularization parameter C", "slack variables ξᵢ")

2. **MANDATORY EXTRACTION RULES FOR MATHEMATICAL CONTENT:**
   - Extract ALL mathematical formulas, equations, and expressions mentioned in the text
   - Include parameter names, variable symbols, and their mathematical notation
   - Extract optimization objectives (e.g., "minimize ||w||²", "maximize margin")
   - Include constraints and conditions (e.g., "subject to yᵢ(w^T xᵢ + b) ≥ 1")
   - Extract algorithm steps and mathematical operations
   - Include function definitions and mathematical relationships

3. Identify relationships between entities:
   - uses: Sử dụng (Công nghệ sử dụng phương pháp)
   - implements: Triển khai (Ứng dụng triển khai khái niệm)
   - measures: Đo lường (Thước đo đánh giá phương pháp)
   - solves: Giải quyết (Phương pháp giải quyết vấn đề)
   - contains: Chứa (Hệ thống chứa thành phần)
   - requires: Yêu cầu (Quy trình yêu cầu công nghệ)
   - improves: Cải thiện (Kỹ thuật cải thiện hiệu suất)
   - causes: Gây ra (Nguyên nhân gây ra vấn đề)
   - optimizes: Tối ưu hóa (Thuật toán tối ưu hóa hàm mục tiêu)
   - constrains: Ràng buộc (Điều kiện ràng buộc tham số)
   - defines: Định nghĩa (Công thức định nghĩa khái niệm)
   - calculates: Tính toán (Phương pháp tính toán giá trị)
   - minimizes: Cực tiểu hóa (Thuật toán cực tiểu hóa hàm số)
   - maximizes: Cực đại hóa (Phương pháp cực đại hóa metric)
   - controls: Kiểm soát (Tham số kiểm soát hành vi)
   - balances: Cân bằng (Cân bằng giữa các yếu tố)
   - transforms: Biến đổi (Biến đổi dữ liệu/không gian)
   - approximates: Xấp xỉ (Phương pháp xấp xỉ giá trị)

4. **ENHANCED DESCRIPTION REQUIREMENTS:**
   - Entity description: MUST start with "[Tên entity] là..." then explain clearly the role, characteristics, mathematical properties (if applicable), and importance in IT knowledge domain
   - For formulas/parameters: Include their mathematical meaning, usage context, and impact on the algorithm/method
   - For relationships: Describe in detail the relationship between 2 entities, including mathematical context and significance of that relationship in IT education
   - Include specific values, ranges, or constraints mentioned in the text

5. **SPECIAL ATTENTION TO MATHEMATICAL CONTENT:**
   - Look for optimization objectives (minimize, maximize)
   - Extract constraint conditions (subject to, where, such that)
   - Identify function definitions and equations
   - Extract parameter ranges and typical values
   - Include algorithm complexity notations (O(n), O(n²), etc.)
   - Capture mathematical operations and transformations
   - Extract probability distributions and statistical measures
   - Include matrix operations and linear algebra expressions
</instructions>

<constraints>
- Only extract information that actually exists in the text
- Entity names must be accurate and consistent (keep original English terms where appropriate, especially for mathematical notation)
- Mathematical formulas and expressions must be preserved EXACTLY as written in the source text
- For mathematical entities: Include complete notation (e.g., "w^T x + b = 0", "ξᵢ ≥ 0", "||w||²")
- Relationships must be logical and meaningful for IT education
- Descriptions must be detailed, complete, and have high informational value for MCQ generation
- Type must be lowercase
- All descriptions and explanations must be in Vietnamese
- Focus on extracting knowledge that can be used to generate educational questions
- **PRIORITY: Do not miss any mathematical formulas, algorithms, parameters, or equations mentioned in the text**
</constraints>

<output>
Định dạng kết quả như sau:

[ENTITY]<|>entity_name<|>entity_type<|>detailed_entity_description[/ENTITY]
[RELATIONSHIP]<|>source_entity<|>target_entity<|>relationship_type<|>detailed_relationship_description[/RELATIONSHIP]

Ví dụ với tập trung vào công thức toán:
[ENTITY]<|>Support Vector Machine<|>concept<|>Support Vector Machine là một thuật toán phân loại mạnh mẽ tìm siêu phẳng tối ưu để phân tách các lớp dữ liệu với margin tối đa. SVM sử dụng các support vectors để định nghĩa đường phân cách và có thể xử lý dữ liệu phi tuyến thông qua kernel trick.[/ENTITY]
[ENTITY]<|>w^T x + b = 0<|>formula<|>w^T x + b = 0 là phương trình định nghĩa siêu phẳng phân tách trong Support Vector Machine, trong đó w là vector trọng số, x là vector đặc trưng, và b là bias term. Phương trình này xác định ranh giới quyết định giữa các lớp dữ liệu.[/ENTITY]
[ENTITY]<|>||w||²<|>formula<|>||w||² là chuẩn bình phương của vector trọng số w, được sử dụng trong hàm mục tiêu của SVM để tối thiểu hóa. Việc tối thiểu hóa ||w||² tương đương với việc tối đa hóa margin giữa các lớp dữ liệu.[/ENTITY]
[ENTITY]<|>ξᵢ<|>parameter<|>ξᵢ (slack variables) là các biến nới lỏng trong Soft Margin SVM cho phép một số điểm dữ liệu vi phạm margin hoặc bị phân loại sai. Giá trị ξᵢ ≥ 0 đo lường mức độ vi phạm của điểm dữ liệu thứ i.[/ENTITY]
[ENTITY]<|>C<|>parameter<|>C là tham số regularization trong SVM điều khiển sự cân bằng giữa việc tối đa hóa margin và tối thiểu hóa lỗi phân loại. Giá trị C lớn ưu tiên phân loại chính xác, C nhỏ ưu tiên margin lớn.[/ENTITY]
[RELATIONSHIP]<|>Support Vector Machine<|>w^T x + b = 0<|>uses<|>Support Vector Machine sử dụng phương trình w^T x + b = 0 để định nghĩa siêu phẳng phân tách tối ưu. Đây là công thức cốt lõi xác định ranh giới quyết định trong không gian đặc trưng.[/RELATIONSHIP]
[RELATIONSHIP]<|>||w||²<|>ξᵢ<|>constrains<|>Trong Soft Margin SVM, việc tối thiểu hóa ||w||² bị ràng buộc bởi các slack variables ξᵢ thông qua điều kiện yᵢ(w^T xᵢ + b) ≥ 1 - ξᵢ, cho phép một số điểm vi phạm margin.[/RELATIONSHIP]
[RELATIONSHIP]<|>C<|>ξᵢ<|>controls<|>Tham số C kiểm soát penalty cho các slack variables ξᵢ trong hàm mục tiêu: min(1/2||w||² + C∑ξᵢ). Giá trị C cao tạo penalty lớn cho việc vi phạm, C thấp cho phép nhiều vi phạm hơn.[/RELATIONSHIP]
</output>

The context: {input_text}

Result:"""
