from typing import Any


def format_context(context_data: dict[str, Any]) -> str:
    """
    Format context data into readable string for prompt.
    
    Args:
        context_data: Context data from the RAG system with chunk_df structure
        
    Returns:
        Formatted string ready for use in prompt
    """
    if not context_data or 'chunk_df' not in context_data:
        return "No relevant information found."
    
    chunk_df = context_data['chunk_df']
    if not chunk_df:
        return "No relevant information found."
    
    formatted_context = []
    
    for i, chunk_obj in enumerate(chunk_df, 1):
        chunk_text = chunk_obj.get('chunk', '')
        entities = chunk_obj.get('entities', [])
        relationships = chunk_obj.get('relationships', [])
        file_names = chunk_obj.get('file_name', [])
        
        # Start with chunk content
        context_section = f"**Tài liệu {i}:**\n{chunk_text}"
        
        # Add entities if available
        if entities:
            context_section += f"\n\n**Thực thể liên quan:**\n"
            for entity in entities:
                context_section += f"- {entity}\n"
        
        # Add relationships if available
        if relationships:
            context_section += f"\n**Mối quan hệ:**\n"
            for relationship in relationships:
                context_section += f"- {relationship}\n"
        
        # Add source file
        if file_names:
            source_files = ", ".join(file_names)
            context_section += f"\n**Nguồn:** {source_files}"
        
        formatted_context.append(context_section)
    
    # Join all sections with separators
    return "\n\n" + ("="*50 + "\n\n").join(formatted_context)


def build_conversation(conversation_history: list[dict[str, str]]) -> str:
    if not conversation_history:
        return "No conversation history available."
    
    formatted_conversation = []
    for entry in conversation_history:
        role = entry.get('type', 'user')
        content = entry.get('content', '')
        formatted_conversation.append(f"{role.capitalize()}: {content}")
    
    return "\n".join(formatted_conversation)