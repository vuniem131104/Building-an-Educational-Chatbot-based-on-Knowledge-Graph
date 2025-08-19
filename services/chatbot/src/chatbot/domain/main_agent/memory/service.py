from asyncio.log import logger
from datetime import datetime
import uuid
import psycopg2
import json
from chatbot.shared.state.chatbot_state import ChatbotState
from functools import cached_property
from dotenv import load_dotenv
from base import BaseService
import os 
from typing import Any, Dict, List
from pg import SQLDatabase
from pg.database.schemas import Message
from base import BaseModel
from sqlalchemy import desc
from chatbot.shared.state.chatbot_state import ChatbotState
load_dotenv()

class MemoryInput(BaseModel):
    pass

class MemoryOutput(BaseModel):
    conversation_history: List[Dict[str, str]]

class MemoryService(BaseService):

    database: SQLDatabase

    def process(self, state: ChatbotState) -> list[dict[str, Any]]:
        try:
            with self.database.get_session() as session:
                messages = self.database.get_messages(
                    session=session,
                    filter=None,
                    order_by=[desc("created_at")],
                    limit=3
                )

                conversation_history = []

                if messages:
                    # Reverse to get chronological order (oldest first)
                    for message in reversed(messages):
                        if message.query:
                            conversation_history.append({
                                "type": "user",
                                "content": message.query
                            })
                        if message.answer:
                            conversation_history.append({
                                "type": "assistant",
                                "content": message.answer
                            })
                else:
                    logger.info("No conversation history found.")

                return {
                    'conversation_history': conversation_history
                }
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            # Return empty history if error
            return {
                'conversation_history': [{'type': 'error', 'content': 'Error retrieving conversation history'}]
            }
    def save_conversation_history(
        self,
        raw_question: str,
        refirement_query: str,
        sub_questions: List[str],
        answer: str
    ) -> None:
        try:
            with self.database.get_session() as session:
                message = Message(
                    id= uuid.uuid4().hex,  # Generate a unique ID
                    query=raw_question,
                    refirement_query=refirement_query,
                    sub_questions=sub_questions,  # Pass list directly without json.dumps()
                    answer=answer,
                    created_at=datetime.now()
                )
                self.database.insert_message(session, message)
                session.commit()
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}")
