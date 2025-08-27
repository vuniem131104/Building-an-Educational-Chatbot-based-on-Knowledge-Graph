GRAPH_EXTRACTION_PROMPT = """<role>
Bạn là một chuyên gia phân tích tài liệu hành chính công của Việt Nam, chuyên trích xuất thông tin có cấu trúc để xây dựng knowledge graph phục vụ hỗ trợ công dân trong các thủ tục hành chính.
</role>

<instructions>
Từ đoạn văn bản được cung cấp, hãy trích xuất các thực thể (entities) và mối quan hệ (relationships) để xây dựng knowledge graph phục vụ hệ thống hỗ trợ hành chính công.

1. Xác định các thực thể quan trọng thuộc các loại sau:
   - organization: Cơ quan, tổ chức (Ví dụ: "Ủy ban nhân dân phường", "Công an phường")
   - person: Người, chức vụ (Ví dụ: "Chủ tịch UBND", "Công dân")
   - document: Tài liệu, giấy tờ (Ví dụ: "Căn cước công dân", "Giấy khai sinh")
   - procedure: Thủ tục, quy trình (Ví dụ: "Cấp căn cước công dân", "Đăng ký nhập xã")
   - location: Địa điểm (Ví dụ: "Phường Đống Đa", "Quận Ba Đình")
   - requirement: Điều kiện, yêu cầu (Ví dụ: "Đủ 14 tuổi", "Có hộ khẩu thường trú")
   - fee: Phí, lệ phí (Ví dụ: "20.000 đồng", "Miễn phí")
   - timeline: Thời gian, thời hạn (Ví dụ: "15 ngày làm việc", "Trong vòng 3 ngày")

2. Xác định các mối quan hệ giữa các thực thể:
   - manages: Quản lý (Tổ chức quản lý thủ tục)
   - requires: Yêu cầu (Thủ tục yêu cầu tài liệu)
   - located_in: Nằm tại (Tổ chức nằm tại địa điểm)
   - costs: Có phí (Thủ tục có phí)
   - takes_time: Mất thời gian (Thủ tục mất thời gian)
   - issued_by: Được cấp bởi (Tài liệu được cấp bởi tổ chức)
   - applies_to: Áp dụng cho (Yêu cầu áp dụng cho người/tổ chức)

3. Viết mô tả chi tiết cho mỗi entity và relationship:
   - Entity description: BẮT BUỘC bắt đầu bằng "[Tên entity] là..." sau đó giải thích rõ ràng vai trò, tính chất và tầm quan trọng trong thủ tục hành chính
   - Relationship description: Miêu tả chi tiết mối quan hệ giữa 2 entities, bao gồm bối cảnh và ý nghĩa của mối quan hệ đó
</instructions>

<constraints>
- Chỉ trích xuất thông tin thực sự có trong văn bản
- Tên thực thể phải chính xác và nhất quán
- Mối quan hệ phải logic và có ý nghĩa
- Mô tả phải chi tiết, đầy đủ và có giá trị thông tin cao
- Type phải là lowercase
</constraints>

<output>
Định dạng kết quả như sau:

("entity"|<entity_name>|<entity_type>|<detailed_entity_description>)
("relationship"|<source_entity>|<target_entity>|<relationship_type>|<detailed_relationship_description>)

Ví dụ:
("entity"|Ủy ban nhân dân phường|organization|Ủy ban nhân dân phường là cơ quan hành chính nhà nước cấp phường, có thẩm quyền cấp các loại giấy tờ tùy thân cho công dân, thực hiện các thủ tục hành chính trên địa bàn phường. Đây là cơ quan trực tiếp tiếp xúc và phục vụ người dân trong các vấn đề về hộ tịch, căn cước công dân.)
("entity"|Căn cước công dân|document|Căn cước công dân là giấy tờ tùy thân chính thức của công dân Việt Nam, thay thế cho chứng minh nhân dân, có gắn chip điện tử chứa thông tin sinh trắc học. Được sử dụng để chứng minh danh tính trong các giao dịch, thủ tục hành chính và đời sống xã hội.)
("relationship"|Ủy ban nhân dân phường|Căn cước công dân|issued_by|Ủy ban nhân dân phường là cơ quan có thẩm quyền trực tiếp tiếp nhận hồ sơ, thẩm định và cấp căn cước công dân cho công dân trên địa bàn. Quy trình này được thực hiện theo đúng quy định của pháp luật về căn cước công dân.)
</output>

Văn bản: {input_text}

Kết quả:"""
